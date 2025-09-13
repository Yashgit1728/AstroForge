"""
LLM provider factory for creating and managing different AI providers.
"""

import logging
from typing import Dict, Type, Optional
from enum import Enum

from .llm_provider import LLMProvider, LLMProviderError
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .groq_provider import GroqProvider

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported LLM provider types."""
    CLAUDE = "claude"
    OPENAI = "openai"
    GROQ = "groq"


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers: Dict[ProviderType, Type[LLMProvider]] = {
        ProviderType.CLAUDE: ClaudeProvider,
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.GROQ: GroqProvider,
    }
    
    @classmethod
    def create_provider(
        self,
        provider_type: ProviderType,
        api_key: str,
        model: Optional[str] = None
    ) -> LLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_type: The type of provider to create
            api_key: API key for the provider
            model: Optional model name (uses provider default if not specified)
            
        Returns:
            Configured LLM provider instance
            
        Raises:
            LLMProviderError: If provider type is not supported or creation fails
        """
        if provider_type not in self._providers:
            raise LLMProviderError(
                f"Unsupported provider type: {provider_type}",
                "factory"
            )
        
        provider_class = self._providers[provider_type]
        
        try:
            if model:
                return provider_class(api_key=api_key, model=model)
            else:
                return provider_class(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to create {provider_type} provider: {e}")
            raise LLMProviderError(
                f"Failed to create {provider_type} provider: {e}",
                "factory"
            )
    
    @classmethod
    def get_supported_providers(cls) -> list[ProviderType]:
        """Get list of supported provider types."""
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_models(cls, provider_type: ProviderType) -> list[str]:
        """
        Get supported models for a provider type.
        
        Args:
            provider_type: The provider type
            
        Returns:
            List of supported model names
            
        Raises:
            LLMProviderError: If provider type is not supported
        """
        if provider_type not in cls._providers:
            raise LLMProviderError(
                f"Unsupported provider type: {provider_type}",
                "factory"
            )
        
        # Create a temporary instance to get supported models
        # This is a bit hacky but works for getting the model list
        provider_class = cls._providers[provider_type]
        temp_instance = provider_class(api_key="dummy", model="dummy")
        return temp_instance.supported_models


class LLMProviderManager:
    """Manager for handling multiple LLM providers with failover support."""
    
    def __init__(self):
        self.providers: Dict[ProviderType, LLMProvider] = {}
        self.primary_provider: Optional[ProviderType] = None
        self.fallback_order: list[ProviderType] = []
    
    def add_provider(
        self,
        provider_type: ProviderType,
        api_key: str,
        model: Optional[str] = None,
        is_primary: bool = False
    ) -> None:
        """
        Add a provider to the manager.
        
        Args:
            provider_type: The type of provider
            api_key: API key for the provider
            model: Optional model name
            is_primary: Whether this should be the primary provider
        """
        provider = LLMProviderFactory.create_provider(
            provider_type=provider_type,
            api_key=api_key,
            model=model
        )
        
        self.providers[provider_type] = provider
        
        if is_primary or self.primary_provider is None:
            self.primary_provider = provider_type
        
        # Add to fallback order if not already present
        if provider_type not in self.fallback_order:
            self.fallback_order.append(provider_type)
        
        logger.info(f"Added {provider_type} provider with model {provider.model}")
    
    def get_provider(self, provider_type: Optional[ProviderType] = None) -> LLMProvider:
        """
        Get a provider instance.
        
        Args:
            provider_type: Specific provider type, or None for primary
            
        Returns:
            LLM provider instance
            
        Raises:
            LLMProviderError: If provider is not available
        """
        if provider_type is None:
            provider_type = self.primary_provider
        
        if provider_type is None or provider_type not in self.providers:
            raise LLMProviderError(
                f"Provider {provider_type} not available",
                "manager"
            )
        
        return self.providers[provider_type]
    
    async def generate_completion_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Generate completion with automatic fallback to other providers.
        
        Tries providers in fallback order until one succeeds.
        """
        last_error = None
        
        for provider_type in self.fallback_order:
            if provider_type not in self.providers:
                continue
            
            try:
                provider = self.providers[provider_type]
                logger.debug(f"Attempting completion with {provider_type}")
                
                return await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            except Exception as e:
                logger.warning(f"Provider {provider_type} failed: {e}")
                last_error = e
                continue
        
        # If we get here, all providers failed
        raise LLMProviderError(
            f"All providers failed. Last error: {last_error}",
            "manager"
        )
    
    async def generate_structured_completion_with_fallback(
        self,
        prompt: str,
        response_schema: Dict,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Generate structured completion with automatic fallback.
        """
        last_error = None
        
        for provider_type in self.fallback_order:
            if provider_type not in self.providers:
                continue
            
            try:
                provider = self.providers[provider_type]
                logger.debug(f"Attempting structured completion with {provider_type}")
                
                return await provider.generate_structured_completion(
                    prompt=prompt,
                    response_schema=response_schema,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            except Exception as e:
                logger.warning(f"Provider {provider_type} failed: {e}")
                last_error = e
                continue
        
        # If we get here, all providers failed
        raise LLMProviderError(
            f"All providers failed. Last error: {last_error}",
            "manager"
        )