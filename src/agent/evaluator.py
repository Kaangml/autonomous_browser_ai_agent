"""Evaluator Agent - evaluates step results and triggers re-planning.

The evaluator analyzes execution results to determine:
1. Did the step succeed?
2. Is the overall task complete?
3. Should we re-plan?
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from browser.dom_analyzer import PageStructure
    from llm.base import BaseLLMProvider


EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {
            "type": "boolean",
            "description": "Whether the step executed successfully",
        },
        "task_complete": {
            "type": "boolean",
            "description": "Whether the overall task is now complete",
        },
        "confidence": {
            "type": "number",
            "description": "Confidence level 0-1 in the evaluation",
        },
        "error": {
            "type": "string",
            "description": "Error description if step failed",
        },
        "result": {
            "type": "string",
            "description": "Extracted result if task is complete",
        },
        "should_replan": {
            "type": "boolean",
            "description": "Whether the planner should create a new plan",
        },
        "replan_reason": {
            "type": "string",
            "description": "Why re-planning is needed",
        },
        "next_action_hint": {
            "type": "string",
            "description": "Suggestion for what to do next",
        },
    },
    "required": ["success", "task_complete"],
}


class EvaluatorAgent:
    """Evaluates execution results and provides feedback for the orchestrator.
    
    The evaluator:
    1. Checks if an individual step succeeded
    2. Determines if the overall task is complete
    3. Decides whether re-planning is needed
    4. Provides hints for the next action
    """
    
    SYSTEM_PROMPT = """You are an evaluation agent for a browser automation system.

After each step is executed, you must evaluate:

1. SUCCESS: Did the action complete without errors? Check:
   - Was the element found?
   - Did the action execute?
   - Did the page respond as expected?

2. TASK COMPLETION: Is the user's original task now complete? Consider:
   - Did we achieve the stated goal?
   - Do we have the information/result requested?
   - Are there remaining sub-goals?

3. RE-PLANNING: Should we create a new plan? Consider:
   - Did the page change unexpectedly?
   - Are there new elements we didn't account for?
   - Is the current plan still valid?

Be precise and conservative - only mark task_complete=true when you're confident
the original goal has been achieved."""

    def __init__(self, llm: Optional["BaseLLMProvider"] = None):
        """Initialize evaluator.
        
        Args:
            llm: LLM provider for intelligent evaluation
        """
        self.llm = llm
    
    async def evaluate(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any],
        page: Any = None,
        task: str = "",
        remaining_steps: int = 0,
        page_structure: Optional["PageStructure"] = None,
    ) -> Dict[str, Any]:
        """Evaluate a step result.
        
        Args:
            step: The step that was executed
            result: Result from the executor
            page: Current page state
            task: Original task description
            remaining_steps: Steps remaining in current plan
            page_structure: Current DOM structure
            
        Returns:
            Evaluation result dictionary
        """
        # Quick check for obvious failures
        if not result.get("ok"):
            return {
                "success": False,
                "task_complete": False,
                "error": result.get("error", "Unknown error"),
                "should_replan": True,
                "replan_reason": f"Step failed: {result.get('error')}",
            }
        
        # If no LLM, use simple heuristics
        if not self.llm:
            return self._simple_evaluation(step, result, remaining_steps)
        
        # Use LLM for intelligent evaluation
        return await self._llm_evaluation(
            step, result, page, task, remaining_steps, page_structure
        )
    
    def _simple_evaluation(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any],
        remaining_steps: int,
    ) -> Dict[str, Any]:
        """Simple rule-based evaluation."""
        step_type = step.get("type")
        
        # Extract text steps might complete the task
        if step_type == "extract_text" and result.get("result"):
            extracted = result.get("result", "")
            if extracted and len(extracted) > 10:
                # We got meaningful content
                if remaining_steps == 0:
                    return {
                        "success": True,
                        "task_complete": True,
                        "result": extracted,
                        "confidence": 0.7,
                    }
        
        # Default: step succeeded, continue with plan
        return {
            "success": True,
            "task_complete": remaining_steps == 0,
            "confidence": 0.5,
        }
    
    async def _llm_evaluation(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any],
        page: Any,
        task: str,
        remaining_steps: int,
        page_structure: Optional["PageStructure"],
    ) -> Dict[str, Any]:
        """Use LLM for intelligent evaluation."""
        
        # Get current DOM context
        dom_context = ""
        if page_structure:
            dom_context = page_structure.to_prompt_context()
        elif page:
            from browser.dom_analyzer import DOMAnalyzer
            analyzer = DOMAnalyzer()
            structure = await analyzer.analyze(page)
            dom_context = structure.to_prompt_context()
        
        prompt = f"""{self.SYSTEM_PROMPT}

## ORIGINAL TASK
{task}

## STEP EXECUTED
{json.dumps(step, indent=2)}

## EXECUTION RESULT
{json.dumps({k: v for k, v in result.items() if k != 'page'}, indent=2)}

## CURRENT PAGE STATE
{dom_context}

## REMAINING PLANNED STEPS
{remaining_steps}

Evaluate this step and provide your assessment."""

        try:
            evaluation = await self.llm.complete_json(prompt, EVALUATION_SCHEMA)
            return evaluation
        except Exception as e:
            # Fallback to simple evaluation on error
            return {
                "success": True,
                "task_complete": False,
                "error": f"Evaluation failed: {e}",
            }
    
    async def check_task_completion(
        self,
        task: str,
        execution_log: list,
        page: Any = None,
    ) -> Dict[str, Any]:
        """Check if the overall task is complete based on execution history.
        
        Called at the end of execution or when steps are exhausted.
        """
        if not self.llm:
            # Simple check: did any step extract meaningful content?
            for entry in execution_log:
                result = entry.get("result", {})
                if result.get("ok") and result.get("result"):
                    return {
                        "complete": True,
                        "result": result.get("result"),
                    }
            return {"complete": False, "reason": "No meaningful result extracted"}
        
        prompt = f"""Review this task execution and determine if the task was completed:

Task: {task}

Execution log:
{json.dumps(execution_log, indent=2, default=str)}

Was the task completed successfully? What was the final result?"""

        try:
            result = await self.llm.complete_json(prompt, {
                "type": "object",
                "properties": {
                    "complete": {"type": "boolean"},
                    "result": {"type": "string"},
                    "reason": {"type": "string"},
                },
            })
            return result
        except Exception:
            return {"complete": False, "reason": "Evaluation failed"}
