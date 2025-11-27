"""OpenAI LLM provider using LangChain."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .base import BaseLLMProvider, LLMResponse, Message


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider for GPT models."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo",
    ):
        self._api_key = api_key
        self._model = model
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            from langchain_openai import ChatOpenAI
            
            self._client = ChatOpenAI(
                model=self._model,
                api_key=self._api_key,
            )
        
        return self._client
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using OpenAI."""
        client = self._get_client()
        
        response = await client.ainvoke(prompt, **kwargs)
        
        return LLMResponse(
            content=response.content,
            raw_response=response,
            model=self._model,
            usage=response.usage_metadata if hasattr(response, 'usage_metadata') else None,
        )
    
    async def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Generate chat response using OpenAI."""
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        client = self._get_client()
        
        # Convert to LangChain message format
        lc_messages = []
        for msg in messages:
            if msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
        
        response = await client.ainvoke(lc_messages, **kwargs)
        
        return LLMResponse(
            content=response.content,
            raw_response=response,
            model=self._model,
        )
    
    async def complete_json(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate JSON response conforming to schema.
        
        OpenAI supports native JSON mode for better reliability.
        """
        from langchain_openai import ChatOpenAI
        
        # Use JSON mode if available
        client = ChatOpenAI(
            model=self._model,
            api_key=self._api_key,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        
        schema_str = json.dumps(schema, indent=2)
        enhanced_prompt = f"""{prompt}

You MUST respond with valid JSON matching this schema:
{schema_str}

Respond ONLY with the JSON object."""

        response = await client.ainvoke(enhanced_prompt, **kwargs)
        
        return json.loads(response.content)
    
    @property
    def model_name(self) -> str:
        return self._model
    
    @property
    def provider_name(self) -> str:
        return "openai"
