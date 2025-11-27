"""Multi-Agent Orchestrator - coordinates planner, executor, and evaluator agents.

The orchestrator is the main entry point for task execution. It:
1. Receives a high-level task from the user
2. Coordinates the planner to create multi-step plans
3. Dispatches steps to the executor
4. Uses the evaluator for reflection and re-planning
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from llm.base import BaseLLMProvider, Message
from llm.factory import get_provider_for_role


class TaskStatus(str, Enum):
    """Status of a task execution."""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskResult:
    """Result of a completed task."""
    success: bool
    task: str
    steps_executed: int
    final_result: Any
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class OrchestratorState:
    """Internal state of the orchestrator."""
    task: str
    status: TaskStatus = TaskStatus.PENDING
    current_plan: List[Dict[str, Any]] = field(default_factory=list)
    executed_steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step_index: int = 0
    retry_count: int = 0
    page_context: Optional[str] = None


class Orchestrator:
    """Main orchestrator that coordinates the multi-agent system.
    
    The orchestrator implements a Plan → Execute → Evaluate → (Re-plan) loop:
    
    1. PLAN: Use planner agent to create multi-step plan based on task + DOM
    2. EXECUTE: Execute steps one by one using executor agent
    3. EVALUATE: After each step, evaluate success and decide next action
    4. RE-PLAN: If evaluation detects issues, trigger re-planning
    """
    
    SYSTEM_PROMPT = """You are an orchestrator AI that coordinates a multi-agent browser automation system.

Your role is to:
1. Analyze the user's task and break it down into sub-goals
2. Decide when to invoke the planner for detailed step generation
3. Monitor execution progress and handle failures
4. Determine when a task is complete

You coordinate three agents:
- PLANNER: Creates detailed step-by-step plans with specific selectors
- EXECUTOR: Executes individual browser actions
- EVALUATOR: Checks if actions succeeded and suggests corrections

Always think step by step and explain your reasoning."""

    def __init__(
        self,
        llm: Optional[BaseLLMProvider] = None,
        planner: Optional["PlannerAgent"] = None,
        executor: Optional["ExecutorAgent"] = None,
        evaluator: Optional["EvaluatorAgent"] = None,
        max_retries: int = 3,
        max_steps: int = 20,
    ):
        """Initialize orchestrator.
        
        Args:
            llm: LLM provider for orchestration decisions
            planner: Planner agent instance
            executor: Executor agent instance
            evaluator: Evaluator agent instance
            max_retries: Maximum re-planning attempts
            max_steps: Maximum total steps before giving up
        """
        self.llm = llm or get_provider_for_role("orchestrator")
        self.planner = planner
        self.executor = executor
        self.evaluator = evaluator
        self.max_retries = max_retries
        self.max_steps = max_steps
        self.state: Optional[OrchestratorState] = None
    
    async def execute_task(
        self,
        task: str,
        page: Any = None,
        initial_context: Optional[str] = None,
    ) -> TaskResult:
        """Execute a complete task from start to finish.
        
        Args:
            task: Natural language description of the task
            page: Playwright page object (if browser already open)
            initial_context: Optional DOM/page context
            
        Returns:
            TaskResult with success status and execution details
        """
        # Initialize state
        self.state = OrchestratorState(
            task=task,
            page_context=initial_context,
        )
        
        execution_log = []
        total_steps = 0
        
        try:
            while total_steps < self.max_steps:
                # Phase 1: Planning
                self.state.status = TaskStatus.PLANNING
                
                if not self.state.current_plan or self.state.current_step_index >= len(self.state.current_plan):
                    # Need a new plan
                    plan = await self._create_plan(page)
                    if not plan:
                        return TaskResult(
                            success=False,
                            task=task,
                            steps_executed=total_steps,
                            final_result=None,
                            execution_log=execution_log,
                            error="Failed to create execution plan",
                        )
                    
                    self.state.current_plan = plan
                    self.state.current_step_index = 0
                    execution_log.append({"phase": "planning", "plan": plan})
                
                # Phase 2: Execute next step
                self.state.status = TaskStatus.EXECUTING
                
                step = self.state.current_plan[self.state.current_step_index]
                step_result = await self._execute_step(step, page)
                
                execution_log.append({
                    "phase": "execution",
                    "step": step,
                    "result": step_result,
                })
                
                total_steps += 1
                self.state.executed_steps.append({"step": step, "result": step_result})
                
                # Phase 3: Evaluate
                self.state.status = TaskStatus.EVALUATING
                
                evaluation = await self._evaluate_step(step, step_result, page)
                execution_log.append({"phase": "evaluation", "evaluation": evaluation})
                
                if evaluation.get("task_complete"):
                    # Task is done!
                    self.state.status = TaskStatus.COMPLETED
                    return TaskResult(
                        success=True,
                        task=task,
                        steps_executed=total_steps,
                        final_result=evaluation.get("result"),
                        execution_log=execution_log,
                    )
                
                if evaluation.get("success"):
                    # Step succeeded, move to next
                    self.state.current_step_index += 1
                else:
                    # Step failed, decide whether to re-plan
                    self.state.retry_count += 1
                    
                    if self.state.retry_count > self.max_retries:
                        return TaskResult(
                            success=False,
                            task=task,
                            steps_executed=total_steps,
                            final_result=None,
                            execution_log=execution_log,
                            error=f"Max retries exceeded: {evaluation.get('error')}",
                        )
                    
                    # Trigger re-planning
                    self.state.status = TaskStatus.REPLANNING
                    self.state.current_plan = []  # Force new plan
                    execution_log.append({
                        "phase": "replanning",
                        "reason": evaluation.get("error"),
                    })
            
            # Max steps exceeded
            return TaskResult(
                success=False,
                task=task,
                steps_executed=total_steps,
                final_result=None,
                execution_log=execution_log,
                error="Max steps exceeded",
            )
            
        except Exception as e:
            self.state.status = TaskStatus.FAILED
            return TaskResult(
                success=False,
                task=task,
                steps_executed=total_steps,
                final_result=None,
                execution_log=execution_log,
                error=str(e),
            )
    
    async def _create_plan(self, page: Any) -> List[Dict[str, Any]]:
        """Use planner agent to create execution plan."""
        if self.planner:
            return await self.planner.plan(
                task=self.state.task,
                page=page,
                executed_steps=self.state.executed_steps,
            )
        
        # Fallback: ask orchestrator LLM directly
        prompt = f"""Create a step-by-step plan to accomplish this task:

Task: {self.state.task}

Page Context:
{self.state.page_context or "No page loaded yet"}

Previously executed steps:
{json.dumps(self.state.executed_steps, indent=2) if self.state.executed_steps else "None"}

Return a JSON array of steps, each with:
- action: "goto" | "click" | "fill" | "extract_text" | "wait"
- selector: CSS selector (if applicable)
- value: value to fill (if applicable)
- reason: why this step is needed
"""
        
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "selector": {"type": "string"},
                    "value": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["action", "reason"],
            },
        }
        
        try:
            return await self.llm.complete_json(prompt, schema)
        except Exception:
            return []
    
    async def _execute_step(self, step: Dict[str, Any], page: Any) -> Dict[str, Any]:
        """Execute a single step using executor agent."""
        if self.executor:
            return await self.executor.execute(step, page)
        
        # Fallback: return mock result
        return {"ok": True, "result": "executed"}
    
    async def _evaluate_step(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any],
        page: Any,
    ) -> Dict[str, Any]:
        """Evaluate step result using evaluator agent."""
        if self.evaluator:
            return await self.evaluator.evaluate(
                step=step,
                result=result,
                page=page,
                task=self.state.task,
                remaining_steps=len(self.state.current_plan) - self.state.current_step_index - 1,
            )
        
        # Fallback: simple success check
        return {
            "success": result.get("ok", False),
            "task_complete": False,
            "error": result.get("error"),
        }
    
    async def analyze_task(self, task: str) -> Dict[str, Any]:
        """Analyze a task and return strategy without executing.
        
        Useful for previewing what the agent would do.
        """
        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=f"""Analyze this task and describe your approach:

Task: {task}

Provide:
1. Main goal
2. Sub-goals to achieve
3. Potential challenges
4. Success criteria"""),
        ]
        
        response = await self.llm.chat(messages)
        
        return {
            "task": task,
            "analysis": response.content,
        }
