"""Executor Agent - executes planned steps using browser actions.

The executor takes individual steps from the planner and executes them
using the browser controller, handling errors and reporting results.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from browser.dom_analyzer import DOMAnalyzer
    from controller.browser_controller import BrowserController
    from llm.base import BaseLLMProvider


class ExecutorAgent:
    """Executes browser actions based on planned steps.
    
    The executor:
    1. Receives a step from the orchestrator
    2. Validates the step can be executed
    3. Executes using the browser controller
    4. Returns detailed result for evaluation
    """
    
    SYSTEM_PROMPT = """You are a browser action executor. Your job is to:
1. Execute browser actions precisely as specified
2. Handle errors gracefully
3. Report detailed results

When an action fails, analyze WHY it failed and suggest corrections."""

    def __init__(
        self,
        controller: Optional["BrowserController"] = None,
        dom_analyzer: Optional["DOMAnalyzer"] = None,
        llm: Optional["BaseLLMProvider"] = None,
    ):
        """Initialize executor.
        
        Args:
            controller: Browser controller for action execution
            dom_analyzer: DOM analyzer for element validation
            llm: LLM for intelligent error handling (optional)
        """
        self.controller = controller
        self.dom_analyzer = dom_analyzer
        self.llm = llm
    
    async def execute(
        self,
        step: Dict[str, Any],
        page: Any = None,
    ) -> Dict[str, Any]:
        """Execute a single step.
        
        Args:
            step: Step dictionary with type and args
            page: Current Playwright page object
            
        Returns:
            Result dictionary with success status and details
        """
        action_type = step.get("type")
        args = step.get("args", {})
        metadata = step.get("metadata", {})
        
        # Validate step
        if not action_type:
            return {
                "ok": False,
                "error": "No action type specified",
                "step": step,
            }
        
        # Pre-execution validation for selector-based actions
        if action_type in ("click", "fill", "extract_text", "wait", "scroll"):
            selector = args.get("selector")
            if not selector:
                return {
                    "ok": False,
                    "error": f"No selector specified for {action_type}",
                    "step": step,
                }
            
            # Validate element exists
            if page and self.dom_analyzer:
                element_info = await self.dom_analyzer.get_element_context(page, selector)
                if not element_info.get("exists"):
                    return {
                        "ok": False,
                        "error": f"Selector not found: {selector}",
                        "step": step,
                        "suggestion": metadata.get("fallback", "Try a different selector"),
                    }
        
        # Execute the action
        if not self.controller:
            return {
                "ok": False,
                "error": "No controller available",
                "step": step,
            }
        
        try:
            # Inject page into args if needed
            if page and action_type != "goto":
                args = {**args, "page": page}
            
            result = await self.controller.execute_action({
                "type": action_type,
                "args": args,
            })
            
            # Enhance result with step metadata
            result["step"] = step
            result["expected_outcome"] = metadata.get("expected_outcome")
            
            return result
            
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "step": step,
                "exception_type": type(e).__name__,
            }
    
    async def execute_with_retry(
        self,
        step: Dict[str, Any],
        page: Any = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Execute a step with automatic retries.
        
        Args:
            step: Step to execute
            page: Current page
            max_retries: Maximum retry attempts
            
        Returns:
            Final result after retries
        """
        last_result = None
        
        for attempt in range(max_retries):
            result = await self.execute(step, page)
            last_result = result
            
            if result.get("ok"):
                return result
            
            # If we have an LLM, ask for suggestions
            if self.llm and attempt < max_retries - 1:
                correction = await self._get_correction(step, result, page)
                if correction:
                    step = correction
        
        return last_result
    
    async def _get_correction(
        self,
        step: Dict[str, Any],
        error_result: Dict[str, Any],
        page: Any,
    ) -> Optional[Dict[str, Any]]:
        """Use LLM to suggest a corrected step."""
        if not self.llm:
            return None
        
        # Get current DOM state
        dom_context = ""
        if page and self.dom_analyzer:
            from browser.dom_analyzer import DOMAnalyzer
            analyzer = DOMAnalyzer()
            structure = await analyzer.analyze(page)
            dom_context = structure.to_prompt_context()
        
        prompt = f"""The following browser action failed:

Step: {step}
Error: {error_result.get('error')}

Current page DOM:
{dom_context}

Suggest a corrected step that might work. Return JSON with the corrected step."""

        try:
            corrected = await self.llm.complete_json(prompt, {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "args": {"type": "object"},
                },
            })
            return corrected
        except Exception:
            return None
