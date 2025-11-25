import pytest

from agent.agent import Agent


class DummyTools:
    def __init__(self):
        self.calls = []

    async def execute_action(self, action):
        self.calls.append(action)
        if action.get("type") == "goto":
            return {"ok": True, "result": "navigated"}
        if action.get("type") == "extract_text":
            return {"ok": True, "result": "extracted"}
        return {"ok": False, "error": "unknown"}


@pytest.mark.asyncio
async def test_plan_task_creates_steps():
    ag = Agent()
    steps = await ag.plan_task("Open https://example.com and read")
    assert isinstance(steps, list)
    assert steps[0]["type"] == "goto"


@pytest.mark.asyncio
async def test_execute_and_evaluate_with_tools():
    ag = Agent()
    dao = DummyTools()
    ag.tools = dao

    steps = await ag.plan_task("Open https://example.com and read")
    first = steps[0]

    res = await ag.execute_step(first)
    assert res["ok"]

    ok = ag.evaluate_result(res)
    assert ok is True
    assert ag.memory["results"][-1]["result"] == "navigated"


@pytest.mark.asyncio
async def test_execute_without_tools_returns_error():
    ag = Agent()
    res = await ag.execute_step({"type": "goto", "args": {"url": "https://ex"}})
    assert res["ok"] is False
    assert "no tools" in res["error"]
