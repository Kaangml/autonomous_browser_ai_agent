"""Tests for EvaluatorAgent with mock LLM."""

import pytest
import json

from agent.evaluator import EvaluatorAgent
from llm.mock_provider import MockLLMProvider


@pytest.mark.asyncio
async def test_evaluator_simple_success():
    """Test evaluator with successful step result (no LLM)."""
    evaluator = EvaluatorAgent(llm=None)
    
    step = {"type": "click", "args": {"selector": "#btn"}}
    result = {"ok": True, "result": "clicked"}
    
    evaluation = await evaluator.evaluate(
        step=step,
        result=result,
        remaining_steps=5,
    )
    
    assert evaluation["success"] is True
    assert evaluation["task_complete"] is False


@pytest.mark.asyncio
async def test_evaluator_simple_failure():
    """Test evaluator with failed step result."""
    evaluator = EvaluatorAgent(llm=None)
    
    step = {"type": "click", "args": {"selector": "#missing"}}
    result = {"ok": False, "error": "Element not found"}
    
    evaluation = await evaluator.evaluate(
        step=step,
        result=result,
        remaining_steps=3,
    )
    
    assert evaluation["success"] is False
    assert evaluation["should_replan"] is True
    assert "not found" in evaluation["error"].lower()


@pytest.mark.asyncio
async def test_evaluator_extract_text_completion():
    """Test evaluator marks task complete on extract_text with no remaining steps."""
    evaluator = EvaluatorAgent(llm=None)
    
    step = {"type": "extract_text", "args": {"selector": "body"}}
    result = {"ok": True, "result": "This is the extracted content from the page."}
    
    evaluation = await evaluator.evaluate(
        step=step,
        result=result,
        remaining_steps=0,  # Last step
    )
    
    assert evaluation["success"] is True
    assert evaluation["task_complete"] is True
    assert evaluation["result"] == "This is the extracted content from the page."


@pytest.mark.asyncio
async def test_evaluator_with_llm():
    """Test evaluator with mock LLM for intelligent evaluation."""
    llm_response = json.dumps({
        "success": True,
        "task_complete": False,
        "confidence": 0.9,
        "should_replan": False,
        "next_action_hint": "Continue with next step",
    })
    
    mock_llm = MockLLMProvider(responses=[llm_response])
    evaluator = EvaluatorAgent(llm=mock_llm)
    
    step = {"type": "click", "args": {"selector": "#btn"}}
    result = {"ok": True, "result": "clicked"}
    
    evaluation = await evaluator.evaluate(
        step=step,
        result=result,
        task="Click the submit button and verify form submission",
    )
    
    assert evaluation["success"] is True
    assert evaluation["confidence"] == 0.9


@pytest.mark.asyncio
async def test_evaluator_llm_suggests_replan():
    """Test evaluator with LLM suggesting re-planning."""
    llm_response = json.dumps({
        "success": True,
        "task_complete": False,
        "should_replan": True,
        "replan_reason": "Page structure changed unexpectedly",
    })
    
    mock_llm = MockLLMProvider(responses=[llm_response])
    evaluator = EvaluatorAgent(llm=mock_llm)
    
    evaluation = await evaluator.evaluate(
        step={"type": "click", "args": {"selector": "#btn"}},
        result={"ok": True, "result": "clicked"},
    )
    
    assert evaluation["should_replan"] is True
    assert "unexpectedly" in evaluation["replan_reason"]


@pytest.mark.asyncio
async def test_evaluator_check_task_completion():
    """Test task completion check based on execution log."""
    evaluator = EvaluatorAgent(llm=None)
    
    execution_log = [
        {"result": {"ok": False, "error": "not found"}},
        {"result": {"ok": True, "result": "The extracted page content here"}},
    ]
    
    completion = await evaluator.check_task_completion(
        task="Extract content from page",
        execution_log=execution_log,
    )
    
    assert completion["complete"] is True
    assert "extracted" in completion["result"].lower()


@pytest.mark.asyncio
async def test_evaluator_handles_invalid_json():
    """Test evaluator handles invalid JSON from LLM."""
    # Invalid JSON will cause empty dict return from mock
    mock_llm = MockLLMProvider(responses=["invalid json response"])
    evaluator = EvaluatorAgent(llm=mock_llm)
    
    step = {"type": "click", "args": {"selector": "#btn"}}
    result = {"ok": True, "result": "clicked"}
    
    evaluation = await evaluator.evaluate(step=step, result=result)
    
    # Should return empty dict from LLM (since mock returns {} on invalid JSON)
    assert evaluation == {}
