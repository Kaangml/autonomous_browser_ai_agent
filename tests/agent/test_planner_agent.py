"""Tests for the PlannerAgent with mock LLM."""

import pytest
import json

from agent.planner import PlannerAgent, LLMPlanner
from llm.mock_provider import MockLLMProvider


@pytest.mark.asyncio
async def test_planner_fallback_with_url():
    """Test planner fallback when no LLM is provided."""
    planner = PlannerAgent(llm=None)
    
    steps = await planner.plan("Open https://example.com and read the content")
    
    assert len(steps) >= 1
    assert steps[0]["type"] == "goto"
    assert steps[0]["args"]["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_planner_fallback_google():
    """Test planner fallback for Google search."""
    planner = PlannerAgent(llm=None)
    
    steps = await planner.plan("Search Google for something")
    
    assert len(steps) >= 1
    assert steps[0]["type"] == "goto"
    assert "google" in steps[0]["args"]["url"].lower()


@pytest.mark.asyncio
async def test_planner_with_mock_llm():
    """Test planner with mock LLM returning structured plan."""
    plan_response = json.dumps({
        "goal_analysis": "Navigate to example.com and extract content",
        "lookahead": "After navigation, we will extract text from body",
        "steps": [
            {
                "step_number": 1,
                "action": "goto",
                "value": "https://example.com",
                "reason": "Navigate to target page",
                "expected_outcome": "Page loads successfully",
            },
            {
                "step_number": 2,
                "action": "extract_text",
                "selector": "body",
                "reason": "Extract main content",
                "expected_outcome": "Text content retrieved",
            },
        ],
        "success_criteria": "Text content from example.com is extracted",
    })
    
    mock_llm = MockLLMProvider(responses=[plan_response])
    planner = PlannerAgent(llm=mock_llm)
    
    steps = await planner.plan("Go to example.com and read content")
    
    assert len(steps) == 2
    assert steps[0]["type"] == "goto"
    assert steps[0]["args"]["url"] == "https://example.com"
    assert steps[1]["type"] == "extract_text"
    assert steps[1]["args"]["selector"] == "body"


@pytest.mark.asyncio
async def test_planner_handles_llm_error():
    """Test planner falls back gracefully on LLM error."""
    # Invalid JSON response will cause parse error
    mock_llm = MockLLMProvider(responses=["not valid json"])
    planner = PlannerAgent(llm=mock_llm)
    
    steps = await planner.plan("Open https://test.com")
    
    # Should fall back to deterministic planner
    assert len(steps) >= 1
    assert steps[0]["type"] == "goto"


@pytest.mark.asyncio
async def test_legacy_llm_planner():
    """Test backwards-compatible LLMPlanner class."""
    planner = LLMPlanner(llm_client=None)
    
    steps = await planner.plan("Open https://example.com")
    
    assert len(steps) >= 1
    assert steps[0]["type"] == "goto"


@pytest.mark.asyncio
async def test_planner_step_metadata():
    """Test that planner includes metadata in steps."""
    plan_response = json.dumps({
        "steps": [
            {
                "step_number": 1,
                "action": "click",
                "selector": "#submit",
                "reason": "Submit the form",
                "expected_outcome": "Form is submitted",
                "fallback": "Try button[type=submit]",
            },
        ],
        "success_criteria": "Form submitted",
    })
    
    mock_llm = MockLLMProvider(responses=[plan_response])
    planner = PlannerAgent(llm=mock_llm)
    
    steps = await planner.plan("Submit the form")
    
    assert len(steps) == 1
    assert steps[0]["type"] == "click"
    assert steps[0]["args"]["selector"] == "#submit"
    assert "metadata" in steps[0]
    assert steps[0]["metadata"]["reason"] == "Submit the form"
    assert steps[0]["metadata"]["fallback"] == "Try button[type=submit]"
