"""LLM configuration and provider settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    BEDROCK = "bedrock"
    GEMINI = "gemini"
    OPENAI = "openai"
    MOCK = "mock"  # For testing


@dataclass
class BedrockConfig:
    """AWS Bedrock configuration."""
    access_key_id: Optional[str] = field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID"))
    secret_access_key: Optional[str] = field(default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY"))
    region: str = field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    model_id: str = field(default_factory=lambda: os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"))
    
    @property
    def is_configured(self) -> bool:
        return bool(self.access_key_id and self.secret_access_key)


@dataclass
class GeminiConfig:
    """Google Gemini configuration."""
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-pro"))
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass
class OpenAIConfig:
    """OpenAI configuration."""
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4-turbo"))
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass
class AgentConfig:
    """Multi-agent system configuration."""
    max_planning_steps: int = field(default_factory=lambda: int(os.getenv("MAX_PLANNING_STEPS", "10")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    planning_lookahead: int = field(default_factory=lambda: int(os.getenv("PLANNING_LOOKAHEAD", "4")))
    
    # Provider assignments for each agent role
    orchestrator_provider: LLMProvider = field(
        default_factory=lambda: LLMProvider(os.getenv("ORCHESTRATOR_PROVIDER", "bedrock"))
    )
    planner_provider: LLMProvider = field(
        default_factory=lambda: LLMProvider(os.getenv("PLANNER_PROVIDER", "bedrock"))
    )
    executor_provider: LLMProvider = field(
        default_factory=lambda: LLMProvider(os.getenv("EXECUTOR_PROVIDER", "bedrock"))
    )


@dataclass
class LLMConfig:
    """Master LLM configuration container."""
    bedrock: BedrockConfig = field(default_factory=BedrockConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    
    def get_available_providers(self) -> list[LLMProvider]:
        """Return list of configured providers."""
        available = []
        if self.bedrock.is_configured:
            available.append(LLMProvider.BEDROCK)
        if self.gemini.is_configured:
            available.append(LLMProvider.GEMINI)
        if self.openai.is_configured:
            available.append(LLMProvider.OPENAI)
        return available
    
    def has_any_provider(self) -> bool:
        """Check if at least one provider is configured."""
        return len(self.get_available_providers()) > 0
    
    @classmethod
    def load(cls) -> "LLMConfig":
        """Load configuration from environment."""
        return cls()


# Global config instance
_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    """Get or create the global LLM configuration."""
    global _config
    if _config is None:
        _config = LLMConfig.load()
    return _config
