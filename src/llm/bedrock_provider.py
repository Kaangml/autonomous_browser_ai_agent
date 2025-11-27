"""AWS Bedrock LLM provider using LangChain."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .base import BaseLLMProvider, LLMResponse, Message


class BedrockProvider(BaseLLMProvider):
    """AWS Bedrock provider for Claude, Titan, and other models."""
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region: str = "us-east-1",
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ):
        self._model_id = model_id
        self._region = region
        self._client = None
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
    
    def _get_client(self):
        """Lazy initialization of Bedrock client."""
        if self._client is None:
            from langchain_aws import ChatBedrock
            
            kwargs = {
                "model_id": self._model_id,
                "region_name": self._region,
            }
            
            # Use explicit credentials if provided
            if self._access_key_id and self._secret_access_key:
                import boto3
                session = boto3.Session(
                    aws_access_key_id=self._access_key_id,
                    aws_secret_access_key=self._secret_access_key,
                    region_name=self._region,
                )
                kwargs["client"] = session.client("bedrock-runtime")
            
            self._client = ChatBedrock(**kwargs)
        
        return self._client
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using Bedrock."""
        client = self._get_client()
        
        response = await client.ainvoke(prompt, **kwargs)
        
        return LLMResponse(
            content=response.content,
            raw_response=response,
            model=self._model_id,
            usage=response.usage_metadata if hasattr(response, 'usage_metadata') else None,
        )
    
    async def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Generate chat response using Bedrock."""
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
            model=self._model_id,
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
        return self._model_id
    
    @property
    def provider_name(self) -> str:
        return "bedrock"
