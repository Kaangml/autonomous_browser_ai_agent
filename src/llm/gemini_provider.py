"""Google Gemini LLM provider using LangChain."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .base import BaseLLMProvider, LLMResponse, Message


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro",
    ):
        self._api_key = api_key
        self._model = model
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Gemini client."""
        if self._client is None:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            self._client = ChatGoogleGenerativeAI(
                model=self._model,
                google_api_key=self._api_key,
            )
        
        return self._client
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using Gemini."""
        client = self._get_client()
        
        response = await client.ainvoke(prompt, **kwargs)
        
        return LLMResponse(
            content=response.content,
            raw_response=response,
            model=self._model,
        )
    
    async def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Generate chat response using Gemini."""
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
        """Generate JSON response conforming to schema."""
        schema_str = json.dumps(schema, indent=2)
        enhanced_prompt = f"""{prompt}

You MUST respond with valid JSON matching this schema:
{schema_str}

Respond ONLY with the JSON object, no other text."""

        response = await self.complete(enhanced_prompt, **kwargs)
        
        # Parse JSON from response
        content = response.content.strip()
        # Handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        
        return json.loads(content)
    
    @property
    def model_name(self) -> str:
        return self._model
    
    @property
    def provider_name(self) -> str:
        return "gemini"
