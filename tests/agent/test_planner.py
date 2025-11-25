import pytest

from agent.planner import LLMPlanner, LLMClientInterface


class MockLLM(LLMClientInterface):
    async def complete(self, prompt: str) -> str:
        # Return two simple steps
        return "goto:https://example.com\nextract_text: #main"


@pytest.mark.asyncio
async def test_llm_planner_parses_simple_response():
    client = MockLLM()
    planner = LLMPlanner(llm_client=client)

    steps = await planner.plan("Open example and read main")

    assert isinstance(steps, list)
    assert steps[0]["type"] == "goto"
    assert steps[1]["type"] == "extract_text"