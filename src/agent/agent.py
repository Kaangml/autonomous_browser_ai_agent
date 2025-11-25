class Agent:
    """Minimal multi-step agent pipeline used for tests and local workflows.

    This is intentionally small: it demonstrates the Plan → Execute → Reflect
    steps that we'll expand during Faz 2. The agent uses `tools` injected at
    runtime to perform actions (e.g., BrowserActions via controller).
    """

    def __init__(self, name: str = "Agent1", planner=None):
        self.name = name
        self.memory = {}
        self.tools = None
        self.planner = planner

    def receive_task(self, task: str) -> None:
        """Store the incoming task for later planning and execution."""

        self.memory["last_task"] = task

    async def plan_task(self, task: str) -> list[dict]:
        """Produce a simple list of action steps for a task.

        NOTE: This is not an LLM planner — it's a deterministic placeholder for
        early development. Steps are dicts with a `type` and `args` key.
        """

        # if a planner is provided, use it (async planners expected)
        if self.planner:
            # planner.plan may be async — try awaiting if coroutine
            try:
                steps = await self.planner.plan(task)  # type: ignore[misc]
            except TypeError:
                # planner.plan is sync
                steps = self.planner.plan(task)  # type: ignore[misc]
            self.memory["planned_steps"] = steps
            return steps

        # naive decomposition: if the task mentions 'open' or 'goto' look for URL
        steps: list[dict] = []
        lowered = task.lower()
        # If a URL is present in the task, use that URL. Avoid hard-coded domains.
        import re

        url_match = re.search(r"https?://[^\s]+", task)
        if url_match:
            url = url_match.group(0)
            steps.append({"type": "goto", "args": {"url": url}})
            if "read" in lowered or "extract" in lowered:
                steps.append({"type": "extract_text", "args": {"selector": "body"}})
        elif "google" in lowered:
            # generic google if not explicit link
            steps.append({"type": "goto", "args": {"url": "https://www.google.com"}})
        else:
            # fallback single step (no-op)
            steps.append({"type": "noop", "args": {}})

        self.memory["planned_steps"] = steps
        return steps

    async def execute_step(self, step: dict) -> dict:
        """Execute a single planned step using attached tools.

        Returns a result dict; for tests this method will usually be mocked by
        providing `self.tools` or by using a lightweight controller.
        """

        if not self.tools:
            return {"ok": False, "error": "no tools attached"}

        typ = step.get("type")
        args = step.get("args", {})

        # mapping to controller-friendly action types
        if typ in {"goto", "click", "fill", "extract_text", "links", "screenshot"}:
            # proxy to a controller / tool that understands the same format
            return await self.tools.execute_action({"type": typ, "args": args})

        if typ == "noop":
            return {"ok": True, "result": None}

        return {"ok": False, "error": "unknown step type"}

    def evaluate_result(self, step_result: dict) -> bool:
        """Evaluate a single step result and store in memory if needed."""

        ok = bool(step_result.get("ok"))
        self.memory.setdefault("results", []).append(step_result)
        return ok
