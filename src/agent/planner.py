from __future__ import annotations

from typing import Any, Dict, List, Optional

from .prompt_templates import PromptTemplates


class LLMClientInterface:
    """Abstract LLM client interface (for injection / testing).

    Concrete LLM clients should implement `complete(prompt: str) -> str`.
    """

    async def complete(self, prompt: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError()


class LLMPlanner:
    """Planner that turns a natural language task into a list of action steps.

    This planner is config-driven and uses a provided LLM client to create
    multi-step plans. For tests we provide a mock client.
    """

    def __init__(self, llm_client: Optional[LLMClientInterface] = None):
        self.llm = llm_client

    async def plan(self, task: str) -> List[Dict[str, Any]]:
        """Return a list of step dictionaries for a given task.

        If an LLM client is available we'll call it (format-based). Otherwise
        fall back to a small deterministic planner used earlier.
        """

        if self.llm:
            prompt = PromptTemplates.task_decomposition_prompt(task)
            raw = await self.llm.complete(prompt)
            # Expect LLM returns steps in a simple newline-separated action:type|arg JSON-lite.
            # This is intentionally permissive for tests — real implementations should use
            # a strict JSON format.
            steps = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                # try to parse 'type:payload' or just a URL
                if line.startswith("goto:"):
                    url = line.split("goto:", 1)[1].strip()
                    steps.append({"type": "goto", "args": {"url": url}})
                elif line.startswith("extract_text:"):
                    sel = line.split("extract_text:", 1)[1].strip()
                    steps.append({"type": "extract_text", "args": {"selector": sel}})
                else:
                    # fallback: add as noop step text
                    steps.append({"type": "noop", "args": {"raw": line}})

            return steps

        # fallback deterministic planner (used before)
        import re

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
