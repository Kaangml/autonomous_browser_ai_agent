"""Tests for LLM providers using mock provider."""

import pytest
import json

from llm.mock_provider import MockLLMProvider
from llm.base import Message


@pytest.mark.asyncio
async def test_mock_provider_complete():
    """Test basic completion with mock provider."""
    responses = ["Hello, world!", "Second response"]
    provider = MockLLMProvider(responses=responses)
    
    result = await provider.complete("Test prompt")
    
    assert result.content == "Hello, world!"
    assert result.model == "mock-model"
    assert provider.call_count == 1


@pytest.mark.asyncio
async def test_mock_provider_cycles_responses():
    """Test that mock provider cycles through responses."""
    responses = ["First", "Second"]
    provider = MockLLMProvider(responses=responses)
    
    r1 = await provider.complete("p1")
    r2 = await provider.complete("p2")
    r3 = await provider.complete("p3")
    
    assert r1.content == "First"
    assert r2.content == "Second"
    assert r3.content == "First"  # Cycles back


@pytest.mark.asyncio
async def test_mock_provider_chat():
    """Test chat completion with mock provider."""
    provider = MockLLMProvider(responses=["Chat response"])
    
    messages = [
        Message(role="system", content="You are helpful"),
        Message(role="user", content="Hello"),
    ]
    
    result = await provider.chat(messages)
    
    assert result.content == "Chat response"
    assert provider.call_count == 1


@pytest.mark.asyncio
async def test_mock_provider_complete_json():
    """Test JSON completion with mock provider."""
    json_response = json.dumps({"action": "click", "selector": "#btn"})
    provider = MockLLMProvider(responses=[json_response])
    
    schema = {"type": "object"}
    result = await provider.complete_json("prompt", schema)
    
    assert result["action"] == "click"
    assert result["selector"] == "#btn"


@pytest.mark.asyncio
async def test_mock_provider_with_handler():
    """Test mock provider with custom response handler."""
    def handler(prompt: str) -> str:
        if "search" in prompt.lower():
            return json.dumps({"action": "goto", "url": "https://google.com"})
        return json.dumps({"action": "noop"})
    
    provider = MockLLMProvider(response_handler=handler)
    
    r1 = await provider.complete("Search for something")
    r2 = await provider.complete("Do nothing")
    
    assert "goto" in r1.content
    assert "noop" in r2.content


@pytest.mark.asyncio
async def test_mock_provider_call_history():
    """Test that mock provider tracks call history."""
    provider = MockLLMProvider()
    
    await provider.complete("First prompt")
    await provider.chat([Message(role="user", content="Hello")])
    
    assert len(provider.call_history) == 2
    assert provider.call_history[0]["type"] == "complete"
    assert provider.call_history[0]["prompt"] == "First prompt"
    assert provider.call_history[1]["type"] == "chat"


@pytest.mark.asyncio
async def test_mock_provider_reset():
    """Test resetting mock provider state."""
    provider = MockLLMProvider(responses=["response"])
    
    await provider.complete("prompt")
    assert provider.call_count == 1
    
    provider.reset()
    
    assert provider.call_count == 0
    assert len(provider.call_history) == 0
