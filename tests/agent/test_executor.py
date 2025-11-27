"""Tests for ExecutorAgent with mock dependencies."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agent.executor import ExecutorAgent


class MockController:
    """Mock browser controller for testing."""
    
    def __init__(self):
        self.executed_actions = []
    
    async def execute_action(self, action):
        self.executed_actions.append(action)
        action_type = action.get("type")
        
        if action_type == "goto":
            return {"ok": True, "result": "navigated", "page": MagicMock()}
        elif action_type == "click":
            return {"ok": True, "result": "clicked"}
        elif action_type == "extract_text":
            return {"ok": True, "result": "Extracted text content"}
        elif action_type == "fail":
            return {"ok": False, "error": "Simulated failure"}
        
        return {"ok": True, "result": "executed"}


@pytest.mark.asyncio
async def test_executor_goto():
    """Test executor handles goto action."""
    controller = MockController()
    executor = ExecutorAgent(controller=controller)
    
    step = {"type": "goto", "args": {"url": "https://example.com"}}
    result = await executor.execute(step)
    
    assert result["ok"] is True
    assert result["result"] == "navigated"
    assert len(controller.executed_actions) == 1


@pytest.mark.asyncio
async def test_executor_click_with_page():
    """Test executor passes page to click action."""
    controller = MockController()
    executor = ExecutorAgent(controller=controller)
    
    page = MagicMock()
    step = {"type": "click", "args": {"selector": "#btn"}}
    result = await executor.execute(step, page=page)
    
    assert result["ok"] is True
    # Verify page was injected into args
    executed = controller.executed_actions[0]
    assert executed["args"]["page"] == page


@pytest.mark.asyncio
async def test_executor_extract_text():
    """Test executor handles extract_text action."""
    controller = MockController()
    executor = ExecutorAgent(controller=controller)
    
    page = MagicMock()
    step = {"type": "extract_text", "args": {"selector": "body"}}
    result = await executor.execute(step, page=page)
    
    assert result["ok"] is True
    assert result["result"] == "Extracted text content"


@pytest.mark.asyncio
async def test_executor_missing_selector():
    """Test executor validates required selector."""
    executor = ExecutorAgent(controller=MockController())
    
    step = {"type": "click", "args": {}}  # Missing selector
    result = await executor.execute(step)
    
    assert result["ok"] is False
    assert "selector" in result["error"].lower()


@pytest.mark.asyncio
async def test_executor_missing_action_type():
    """Test executor handles missing action type."""
    executor = ExecutorAgent(controller=MockController())
    
    step = {"args": {"selector": "#btn"}}  # Missing type
    result = await executor.execute(step)
    
    assert result["ok"] is False
    assert "type" in result["error"].lower()


@pytest.mark.asyncio
async def test_executor_no_controller():
    """Test executor handles missing controller gracefully."""
    executor = ExecutorAgent(controller=None)
    
    step = {"type": "goto", "args": {"url": "https://example.com"}}
    result = await executor.execute(step)
    
    assert result["ok"] is False
    assert "controller" in result["error"].lower()


@pytest.mark.asyncio
async def test_executor_step_metadata_preserved():
    """Test that executor preserves step metadata in results."""
    controller = MockController()
    executor = ExecutorAgent(controller=controller)
    
    step = {
        "type": "click",
        "args": {"selector": "#btn"},
        "metadata": {
            "reason": "Click submit button",
            "expected_outcome": "Form submits",
        },
    }
    
    page = MagicMock()
    result = await executor.execute(step, page=page)
    
    assert result["ok"] is True
    assert result["step"] == step
    assert result["expected_outcome"] == "Form submits"


@pytest.mark.asyncio
async def test_executor_with_retry():
    """Test executor retry mechanism."""
    call_count = 0
    
    class RetryController:
        async def execute_action(self, action):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return {"ok": False, "error": "Temporary failure"}
            return {"ok": True, "result": "Success on retry"}
    
    executor = ExecutorAgent(controller=RetryController())
    
    step = {"type": "goto", "args": {"url": "https://example.com"}}
    result = await executor.execute_with_retry(step, max_retries=3)
    
    assert result["ok"] is True
    assert call_count == 3
