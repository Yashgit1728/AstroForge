"""
AI integration module for AstraForge.

This module provides LLM provider abstractions and implementations
for generating mission specifications and other AI-powered features.
"""

from .llm_provider import (
    LLMProvider,
    LLMResponse,
    LLMProviderError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMValidationError,
)
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .groq_provider import GroqProvider
from .provider_factory import (
    LLMProviderFactory,
    LLMProviderManager,
    ProviderType,
)
from .prompt_templates import MissionPromptBuilder
from .response_parser import MissionResponseParser, ParsedMissionResponse, AlternativeMissionResponse
from .ideation_service import MissionIdeationService, MissionGenerationError, create_ideation_service

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMAuthenticationError",
    "LLMValidationError",
    "ClaudeProvider",
    "OpenAIProvider",
    "GroqProvider",
    "LLMProviderFactory",
    "LLMProviderManager",
    "ProviderType",
    "MissionPromptBuilder",
    "MissionResponseParser",
    "ParsedMissionResponse",
    "AlternativeMissionResponse",
    "MissionIdeationService",
    "MissionGenerationError",
    "create_ideation_service",
]