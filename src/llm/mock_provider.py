"""Mock LLM provider for testing without real API calls."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from .base import BaseLLMProvider, LLMResponse, Message


class MockLLMProvider(BaseLLMProvider):
    """Mock provider for unit testing.
    
    Can be configured with custom response handlers or fixed responses.
    """
    
    def __init__(
        self,
        responses: Optional[List[str]] = None,
        response_handler: Optional[Callable[[str], str]] = None,
    ):
        """Initialize mock provider.
        
        Args:
            responses: List of canned responses to return in order
            response_handler: Custom function to generate responses
        """
        self._responses = responses or []
        self._response_handler = response_handler
        self._call_count = 0
        self._call_history: List[Dict[str, Any]] = []
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Return mock completion."""
        self._call_history.append({"type": "complete", "prompt": prompt, "kwargs": kwargs})
        
        content = self._get_response(prompt)
        self._call_count += 1
        
        return LLMResponse(
            content=content,
            model="mock-model",
            usage={"input_tokens": len(prompt), "output_tokens": len(content)},
        )
    
    async def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Return mock chat response."""
        self._call_history.append({"type": "chat", "messages": messages, "kwargs": kwargs})
        
        # Use last user message as prompt
        prompt = messages[-1].content if messages else ""
        content = self._get_response(prompt)
        self._call_count += 1
        
        return LLMResponse(
            content=content,
            model="mock-model",
        )
    
    async def complete_json(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Return mock JSON response."""
        self._call_history.append({"type": "complete_json", "prompt": prompt, "schema": schema, "kwargs": kwargs})
        
        content = self._get_response(prompt)
        self._call_count += 1
        
        # Try to parse as JSON, or return empty dict
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}
    
    def _get_response(self, prompt: str) -> str:
        """Get the next response."""
        if self._response_handler:
            return self._response_handler(prompt)
        
        if self._responses:
            idx = self._call_count % len(self._responses)
            return self._responses[idx]
        
        return '{"action": "noop", "reason": "mock response"}'
    
    @property
    def model_name(self) -> str:
        return "mock-model"
    
    @property
    def provider_name(self) -> str:
        return "mock"
    
    # Test helpers
    @property
    def call_count(self) -> int:
        return self._call_count
    
    @property
    def call_history(self) -> List[Dict[str, Any]]:
        return self._call_history
    
    def reset(self) -> None:
        """Reset call history and count."""
        self._call_count = 0
        self._call_history.clear()
