"""
Abstract base class for LLM providers.

This module defines the interface that all LLM providers must implement,
ensuring consistent behavior across different AI services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Response from an LLM provider."""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, model: str):
        """Initialize the provider with API key and model."""
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse containing the generated content
            
        Raises:
            LLMProviderError: If the request fails
        """
        pass
    
    @abstractmethod
    async def generate_structured_completion(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a structured completion that follows a specific schema.
        
        Args:
            prompt: The user prompt
            response_schema: JSON schema for the expected response
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Parsed structured response as dictionary
            
        Raises:
            LLMProviderError: If the request fails or response doesn't match schema
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider."""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Return list of supported models for this provider."""
        pass


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        super().__init__(f"{provider}: {message}")


class LLMRateLimitError(LLMProviderError):
    """Exception raised when rate limit is exceeded."""
    pass


class LLMAuthenticationError(LLMProviderError):
    """Exception raised when authentication fails."""
    pass


class LLMValidationError(LLMProviderError):
    """Exception raised when response validation fails."""
    pass