"""Controller for mapping agent actions to browser operations.

The controller receives a simple action dict produced by the agent and executes
it using the provided BrowserActions instance. This is intentionally small and
testable — real safety / queueing logic belongs in higher layers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from browser.actions import BrowserActions


class BrowserController:
    """Lightweight controller that executes agent action dictionaries.

    Expected action format (simple):
      {
          "type": "goto" | "click" | "fill" | "extract_text" | "links" | "screenshot",
          "args": { ... }
      }
    """

    def __init__(self, browser_actions: BrowserActions, allowed_schemes: Optional[List[str]] = None):
        self.browser_actions = browser_actions
        self.allowed_schemes = allowed_schemes or ["http", "https"]
        # Execution queue and basic loop tracking
        self._queue: List[Dict[str, Any]] = []
        self._seen_actions: List[str] = []

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action produced by an agent and return a structured result.

        The method validates basic safety rules (e.g., URL scheme) and maps
        action types to methods on BrowserActions.
        """

        typ = action.get("type")
        args = action.get("args", {})

        # safety: if this action contains a URL, ensure allowed scheme
        url = args.get("url")
        if url:
            from urllib.parse import urlparse

            scheme = urlparse(url).scheme
            if scheme and scheme not in self.allowed_schemes:
                return {"ok": False, "error": f"disallowed url scheme: {scheme}"}

        try:
            if typ == "goto":
                page = await self.browser_actions.go_to_url(args["url"])
                return {"ok": True, "result": "navigated", "page": page}

            if typ == "click":
                page = args.get("page")
                selector = args.get("selector")
                await self.browser_actions.click(page, selector)
                return {"ok": True, "result": "clicked"}

            if typ == "fill":
                page = args.get("page")
                selector = args.get("selector")
                text = args.get("text", "")
                await self.browser_actions.fill(page, selector, text)
                return {"ok": True, "result": "filled"}

            if typ == "extract_text":
                page = args.get("page")
                selector = args.get("selector")
                text = await self.browser_actions.extract_text(page, selector)
                return {"ok": True, "result": text}

            if typ == "links":
                page = args.get("page")
                container = args.get("selector")
                links = await self.browser_actions.extract_all_links(page, container)
                return {"ok": True, "result": links}

            if typ == "screenshot":
                page = args.get("page")
                full = bool(args.get("full_page", False))
                img = await self.browser_actions.screenshot(page, full_page=full)
                return {"ok": True, "result": img}

            return {"ok": False, "error": f"unknown action type: {typ}"}

        except Exception as exc:  # pragma: no cover - error path
            return {"ok": False, "error": str(exc)}

    async def execute_sequence(self, steps: List[Dict[str, Any]], max_steps: int = 50) -> Dict[str, Any]:
        """Execute a list of steps in sequence.

        Returns a dict with overall status and the results list. This method enforces
        `max_steps`, basic infinite-loop detection (repeated identical action), and
        URL scheme filtering for any goto actions.
        """

        if not isinstance(steps, list):
            return {"ok": False, "error": "steps must be a list"}

        results = []
        self._queue = list(steps)
        self._seen_actions.clear()

        executed = 0

        while self._queue:
            if executed >= max_steps:
                return {"ok": False, "error": "max_steps exceeded", "results": results}

            action = self._queue.pop(0)
            key = f"{action.get('type')}:{str(action.get('args'))}"

            # loop detection: if we've executed the exact same action 3+ times, bail
            self._seen_actions.append(key)
            if self._seen_actions.count(key) > 3:
                return {"ok": False, "error": "possible infinite loop detected", "results": results}

            # safety: check url scheme for goto
            if action.get("type") == "goto":
                url = action.get("args", {}).get("url")
                if url:
                    from urllib.parse import urlparse

                    scheme = urlparse(url).scheme
                    if scheme and scheme not in self.allowed_schemes:
                        results.append({"ok": False, "error": f"disallowed url scheme: {scheme}", "action": action})
                        executed += 1
                        continue

            res = await self.execute_action(action)
            results.append(res)
            executed += 1

            # if a step returns a followup list of actions (agent restructuring), push them
            if isinstance(res.get("result"), list) and res.get("ok"):
                # assume returned list is actions to run next
                self._queue = res.get("result") + self._queue

        return {"ok": True, "results": results}
