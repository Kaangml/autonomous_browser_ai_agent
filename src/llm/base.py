"""Base LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    raw_response: Optional[Any] = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
        }


@dataclass
class Message:
    """Chat message."""
    role: str  # "system", "user", "assistant"
    content: str


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    All providers (Bedrock, Gemini, OpenAI) must implement this interface.
    """
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate a completion for the given prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.)
            
        Returns:
            LLMResponse with the generated content
        """
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Generate a response for a chat conversation.
        
        Args:
            messages: List of Message objects representing the conversation
            **kwargs: Provider-specific parameters
            
        Returns:
            LLMResponse with the assistant's response
        """
        pass
    
    @abstractmethod
    async def complete_json(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate a JSON response matching the provided schema.
        
        This is crucial for structured agent outputs (plans, actions).
        
        Args:
            prompt: The input prompt
            schema: JSON schema that the response must conform to
            **kwargs: Provider-specific parameters
            
        Returns:
            Parsed JSON dict matching the schema
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (bedrock, gemini, openai)."""
        pass
