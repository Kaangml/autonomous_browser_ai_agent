"""Factory for creating LLM providers based on configuration."""

from __future__ import annotations

from typing import Optional

from config.llm_config import LLMConfig, LLMProvider, get_llm_config
from .base import BaseLLMProvider


def get_llm_provider(
    provider: Optional[LLMProvider] = None,
    config: Optional[LLMConfig] = None,
) -> BaseLLMProvider:
    """Create and return an LLM provider instance.
    
    Args:
        provider: Specific provider to use. If None, uses first available.
        config: LLM configuration. If None, loads from environment.
        
    Returns:
        Configured LLM provider instance.
        
    Raises:
        ValueError: If requested provider is not configured or no providers available.
    """
    config = config or get_llm_config()
    
    # If no specific provider requested, find the first available
    if provider is None:
        available = config.get_available_providers()
        if not available:
            # Fall back to mock for development/testing
            from .mock_provider import MockLLMProvider
            return MockLLMProvider()
        provider = available[0]
    
    # Handle mock provider
    if provider == LLMProvider.MOCK:
        from .mock_provider import MockLLMProvider
        return MockLLMProvider()
    
    # Create the requested provider
    if provider == LLMProvider.BEDROCK:
        if not config.bedrock.is_configured:
            raise ValueError("Bedrock provider not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
        
        from .bedrock_provider import BedrockProvider
        return BedrockProvider(
            model_id=config.bedrock.model_id,
            region=config.bedrock.region,
            access_key_id=config.bedrock.access_key_id,
            secret_access_key=config.bedrock.secret_access_key,
        )
    
    if provider == LLMProvider.GEMINI:
        if not config.gemini.is_configured:
            raise ValueError("Gemini provider not configured. Set GEMINI_API_KEY.")
        
        from .gemini_provider import GeminiProvider
        return GeminiProvider(
            api_key=config.gemini.api_key,
            model=config.gemini.model,
        )
    
    if provider == LLMProvider.OPENAI:
        if not config.openai.is_configured:
            raise ValueError("OpenAI provider not configured. Set OPENAI_API_KEY.")
        
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=config.openai.api_key,
            model=config.openai.model,
        )
    
    raise ValueError(f"Unknown provider: {provider}")


def get_provider_for_role(role: str, config: Optional[LLMConfig] = None) -> BaseLLMProvider:
    """Get the configured provider for a specific agent role.
    
    Args:
        role: One of 'orchestrator', 'planner', 'executor'
        config: LLM configuration. If None, loads from environment.
        
    Returns:
        LLM provider configured for that role.
    """
    config = config or get_llm_config()
    
    role_to_provider = {
        "orchestrator": config.agent.orchestrator_provider,
        "planner": config.agent.planner_provider,
        "executor": config.agent.executor_provider,
    }
    
    provider = role_to_provider.get(role)
    if provider is None:
        raise ValueError(f"Unknown role: {role}")
    
    return get_llm_provider(provider, config)
