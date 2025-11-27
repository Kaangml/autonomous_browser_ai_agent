"""Planner Agent - creates multi-step plans with DOM awareness.

The planner looks ahead 3-4 steps, analyzes the DOM, and produces
structured JSON plans that the executor can follow.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .prompt_templates import PromptTemplates

if TYPE_CHECKING:
    from browser.dom_analyzer import PageStructure
    from llm.base import BaseLLMProvider


# ============================================================================
# Legacy interfaces (kept for backwards compatibility)
# ============================================================================

class LLMClientInterface:
    """Abstract LLM client interface (for injection / testing).

    Concrete LLM clients should implement `complete(prompt: str) -> str`.
    """

    async def complete(self, prompt: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError()


class LLMPlanner:
    """Legacy planner for backwards compatibility.
    
    Use PlannerAgent for new code.
    """

    def __init__(self, llm_client: Optional[LLMClientInterface] = None):
        self.llm = llm_client

    async def plan(self, task: str) -> List[Dict[str, Any]]:
        """Return a list of step dictionaries for a given task."""

        if self.llm:
            prompt = PromptTemplates.task_decomposition_prompt(task)
            raw = await self.llm.complete(prompt)
            steps = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("goto:"):
                    url = line.split("goto:", 1)[1].strip()
                    steps.append({"type": "goto", "args": {"url": url}})
                elif line.startswith("extract_text:"):
                    sel = line.split("extract_text:", 1)[1].strip()
                    steps.append({"type": "extract_text", "args": {"selector": sel}})
                else:
                    steps.append({"type": "noop", "args": {"raw": line}})
            return steps

        # Fallback deterministic planner
        url_match = re.search(r"https?://[^\s]+", task)
        if url_match:
            url = url_match.group(0)
            steps = [{"type": "goto", "args": {"url": url}}]
            if "read" in task.lower() or "extract" in task.lower():
                steps.append({"type": "extract_text", "args": {"selector": "body"}})
            return steps

        if "google" in task.lower():
            return [{"type": "goto", "args": {"url": "https://www.google.com"}}]

        return [{"type": "noop", "args": {}}]


# ============================================================================
# New Multi-Hop Planner Agent
# ============================================================================

# JSON Schema for plan output
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "goal_analysis": {
            "type": "string",
            "description": "Analysis of the main goal and sub-goals",
        },
        "lookahead": {
            "type": "string",
            "description": "What you expect to happen 3-4 steps from now",
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_number": {"type": "integer"},
                    "action": {
                        "type": "string",
                        "enum": ["goto", "click", "fill", "extract_text", "wait", "screenshot", "scroll"],
                    },
                    "selector": {"type": "string"},
                    "value": {"type": "string"},
                    "reason": {"type": "string"},
                    "expected_outcome": {"type": "string"},
                    "fallback": {"type": "string"},
                },
                "required": ["step_number", "action", "reason"],
            },
        },
        "success_criteria": {
            "type": "string",
            "description": "How to know when the task is complete",
        },
    },
    "required": ["steps", "success_criteria"],
}


class PlannerAgent:
    """Advanced planner that creates DOM-aware multi-step plans.
    
    The planner:
    1. Analyzes the current page DOM structure
    2. Identifies interactive elements relevant to the task
    3. Plans 3-4 steps ahead with fallback strategies
    4. Outputs structured JSON that the executor can follow
    """
    
    SYSTEM_PROMPT = """You are an expert browser automation planner. Your job is to create 
precise, executable plans for web automation tasks.

You will receive:
1. A task description from the user
2. Current page DOM analysis with available interactive elements
3. Previously executed steps (if any)

Your responsibilities:
- Analyze the DOM to find the RIGHT selectors for each action
- Think 3-4 steps ahead - what will the page look like after each action?
- Provide fallback strategies for each step
- Be specific with selectors - use IDs when available, then names, then classes
- Consider timing - some actions need waits for elements to appear

Available actions:
- goto: Navigate to a URL
- click: Click an element (requires selector)
- fill: Type into an input (requires selector and value)
- extract_text: Get text from element (requires selector)
- wait: Wait for element to appear (requires selector)
- screenshot: Take a screenshot
- scroll: Scroll page or to element

IMPORTANT: Only use selectors that exist in the DOM analysis. Don't guess selectors."""

    def __init__(
        self,
        llm: Optional["BaseLLMProvider"] = None,
        lookahead_steps: int = 4,
    ):
        """Initialize planner.
        
        Args:
            llm: LLM provider for plan generation
            lookahead_steps: How many steps to plan ahead
        """
        self.llm = llm
        self.lookahead_steps = lookahead_steps
    
    async def plan(
        self,
        task: str,
        page: Any = None,
        page_structure: Optional["PageStructure"] = None,
        executed_steps: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Create a multi-step plan for the given task.
        
        Args:
            task: Natural language task description
            page: Playwright page object (for DOM analysis)
            page_structure: Pre-analyzed page structure (optional)
            executed_steps: Previously executed steps for context
            
        Returns:
            List of step dictionaries ready for execution
        """
        if self.llm is None:
            # Fallback to simple deterministic planner
            return self._fallback_plan(task)
        
        # Get DOM context
        dom_context = ""
        if page_structure:
            dom_context = page_structure.to_prompt_context()
        elif page:
            from browser.dom_analyzer import DOMAnalyzer
            analyzer = DOMAnalyzer()
            structure = await analyzer.analyze(page)
            dom_context = structure.to_prompt_context()
        
        # Build prompt
        prompt = self._build_prompt(task, dom_context, executed_steps)
        
        try:
            plan_json = await self.llm.complete_json(prompt, PLAN_SCHEMA)
            steps = self._parse_plan(plan_json)
            
            # If no valid steps were parsed, use fallback
            if not steps:
                return self._fallback_plan(task)
            
            return steps
        except Exception as e:
            # Fallback on error
            return self._fallback_plan(task)
    
    def _build_prompt(
        self,
        task: str,
        dom_context: str,
        executed_steps: Optional[List[Dict[str, Any]]],
    ) -> str:
        """Build the planning prompt."""
        
        executed_str = "None"
        if executed_steps:
            executed_str = json.dumps(executed_steps, indent=2)
        
        return f"""{self.SYSTEM_PROMPT}

## TASK
{task}

## CURRENT PAGE STATE
{dom_context if dom_context else "No page loaded yet - start with a 'goto' action"}

## PREVIOUSLY EXECUTED STEPS
{executed_str}

## YOUR TASK
Create a plan with up to {self.lookahead_steps} steps to accomplish the task.
For each step, specify the exact selector from the DOM analysis above.
Think about what will happen after each step and plan accordingly."""

    def _parse_plan(self, plan_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse LLM plan output into executable steps."""
        steps = []
        
        for step in plan_json.get("steps", []):
            parsed = {
                "type": step.get("action", "noop"),
                "args": {},
                "metadata": {
                    "reason": step.get("reason", ""),
                    "expected_outcome": step.get("expected_outcome", ""),
                    "fallback": step.get("fallback", ""),
                },
            }
            
            # Map action to args
            action = step.get("action")
            
            if action == "goto":
                parsed["args"]["url"] = step.get("value", step.get("selector", ""))
            elif action in ("click", "extract_text", "wait", "scroll"):
                parsed["args"]["selector"] = step.get("selector", "")
            elif action == "fill":
                parsed["args"]["selector"] = step.get("selector", "")
                parsed["args"]["text"] = step.get("value", "")
            elif action == "screenshot":
                parsed["args"]["full_page"] = True
            
            steps.append(parsed)
        
        return steps
    
    def _fallback_plan(self, task: str) -> List[Dict[str, Any]]:
        """Simple fallback planner when LLM is unavailable."""
        url_match = re.search(r"https?://[^\s]+", task)
        if url_match:
            url = url_match.group(0)
            steps = [{"type": "goto", "args": {"url": url}}]
            if "extract" in task.lower() or "read" in task.lower() or "get" in task.lower():
                steps.append({"type": "extract_text", "args": {"selector": "body"}})
            return steps
        
        if "google" in task.lower():
            return [{"type": "goto", "args": {"url": "https://www.google.com"}}]
        
        return [{"type": "noop", "args": {}}]
