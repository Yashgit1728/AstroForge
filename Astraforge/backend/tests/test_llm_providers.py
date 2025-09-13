"""
Unit tests for LLM provider implementations.
"""

import json
import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

from app.ai import (
    LLMProvider,
    LLMResponse,
    LLMProviderError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMValidationError,
    ClaudeProvider,
    OpenAIProvider,
    GroqProvider,
    LLMProviderFactory,
    LLMProviderManager,
    ProviderType,
)


class TestLLMProviderFactory:
    """Test the LLM provider factory."""
    
    def test_create_claude_provider(self):
        """Test creating a Claude provider."""
        provider = LLMProviderFactory.create_provider(
            ProviderType.CLAUDE,
            "test-api-key"
        )
        assert isinstance(provider, ClaudeProvider)
        assert provider.api_key == "test-api-key"
        assert provider.provider_name == "claude"
    
    def test_create_openai_provider(self):
        """Test creating an OpenAI provider."""
        provider = LLMProviderFactory.create_provider(
            ProviderType.OPENAI,
            "test-api-key"
        )
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test-api-key"
        assert provider.provider_name == "openai"
    
    def test_create_groq_provider(self):
        """Test creating a Groq provider."""
        provider = LLMProviderFactory.create_provider(
            ProviderType.GROQ,
            "test-api-key"
        )
        assert isinstance(provider, GroqProvider)
        assert provider.api_key == "test-api-key"
        assert provider.provider_name == "groq"
    
    def test_create_provider_with_custom_model(self):
        """Test creating a provider with custom model."""
        provider = LLMProviderFactory.create_provider(
            ProviderType.CLAUDE,
            "test-api-key",
            model="claude-3-opus-20240229"
        )
        assert provider.model == "claude-3-opus-20240229"
    
    def test_unsupported_provider_type(self):
        """Test error handling for unsupported provider type."""
        with pytest.raises(LLMProviderError, match="Unsupported provider type"):
            LLMProviderFactory.create_provider(
                "unsupported",  # type: ignore
                "test-api-key"
            )
    
    def test_get_supported_providers(self):
        """Test getting supported provider types."""
        providers = LLMProviderFactory.get_supported_providers()
        assert ProviderType.CLAUDE in providers
        assert ProviderType.OPENAI in providers
        assert ProviderType.GROQ in providers
    
    def test_get_provider_models(self):
        """Test getting supported models for a provider."""
        models = LLMProviderFactory.get_provider_models(ProviderType.CLAUDE)
        assert "claude-3-sonnet-20240229" in models
        assert "claude-3-opus-20240229" in models


class TestClaudeProvider:
    """Test the Claude provider implementation."""
    
    @pytest.fixture
    def provider(self):
        """Create a Claude provider for testing."""
        return ClaudeProvider("test-api-key")
    
    @pytest.fixture
    def mock_anthropic_response(self):
        """Mock Anthropic API response."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.model = "claude-3-sonnet-20240229"
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)
        mock_response.id = "test-id"
        mock_response.type = "message"
        mock_response.role = "assistant"
        return mock_response
    
    @patch('app.ai.claude_provider.AsyncAnthropic')
    async def test_generate_completion_success(self, mock_anthropic, provider, mock_anthropic_response):
        """Test successful completion generation."""
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic.return_value = mock_client
        
        # Recreate provider to use mocked client
        provider = ClaudeProvider("test-api-key")
        
        response = await provider.generate_completion(
            prompt="Test prompt",
            system_prompt="Test system prompt"
        )
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "claude-3-sonnet-20240229"
        assert response.usage["input_tokens"] == 10
        assert response.usage["output_tokens"] == 20
    
    @patch('app.ai.claude_provider.AsyncAnthropic')
    async def test_generate_completion_rate_limit_error(self, mock_anthropic, provider):
        """Test rate limit error handling."""
        mock_client = AsyncMock()
        mock_client.messages.create.side_effect = Exception("Rate limit exceeded")
        mock_anthropic.return_value = mock_client
        
        # Mock the specific anthropic exceptions
        with patch('app.ai.claude_provider.anthropic.RateLimitError', Exception):
            mock_client.messages.create.side_effect = Exception("Rate limit")
            
            provider = ClaudeProvider("test-api-key")
            
            with pytest.raises(LLMProviderError):
                await provider.generate_completion("Test prompt")
    
    @patch('app.ai.claude_provider.AsyncAnthropic')
    async def test_generate_structured_completion_success(self, mock_anthropic, provider, mock_anthropic_response):
        """Test successful structured completion generation."""
        # Mock response with valid JSON
        mock_anthropic_response.content[0].text = '{"mission": "Mars exploration", "duration": 365}'
        
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic.return_value = mock_client
        
        provider = ClaudeProvider("test-api-key")
        
        schema = {
            "type": "object",
            "properties": {
                "mission": {"type": "string"},
                "duration": {"type": "number"}
            }
        }
        
        response = await provider.generate_structured_completion(
            prompt="Generate mission data",
            response_schema=schema
        )
        
        assert response["mission"] == "Mars exploration"
        assert response["duration"] == 365
    
    @patch('app.ai.claude_provider.AsyncAnthropic')
    async def test_generate_structured_completion_invalid_json(self, mock_anthropic, provider, mock_anthropic_response):
        """Test handling of invalid JSON in structured completion."""
        # Mock response with invalid JSON
        mock_anthropic_response.content[0].text = "Invalid JSON response"
        
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic.return_value = mock_client
        
        provider = ClaudeProvider("test-api-key")
        
        schema = {"type": "object"}
        
        with pytest.raises(LLMValidationError, match="Invalid JSON response"):
            await provider.generate_structured_completion(
                prompt="Generate data",
                response_schema=schema
            )


class TestOpenAIProvider:
    """Test the OpenAI provider implementation."""
    
    @pytest.fixture
    def provider(self):
        """Create an OpenAI provider for testing."""
        return OpenAIProvider("test-api-key")
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock(content="Test response")
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = Mock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        mock_response.id = "test-id"
        mock_response.object = "chat.completion"
        mock_response.created = 1234567890
        return mock_response
    
    @patch('app.ai.openai_provider.AsyncOpenAI')
    async def test_generate_completion_success(self, mock_openai, provider, mock_openai_response):
        """Test successful completion generation."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_client
        
        provider = OpenAIProvider("test-api-key")
        
        response = await provider.generate_completion(
            prompt="Test prompt",
            system_prompt="Test system prompt"
        )
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "gpt-4-turbo-preview"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 20
        assert response.usage["total_tokens"] == 30


class TestGroqProvider:
    """Test the Groq provider implementation."""
    
    @pytest.fixture
    def provider(self):
        """Create a Groq provider for testing."""
        return GroqProvider("test-api-key")
    
    def test_provider_properties(self, provider):
        """Test provider properties."""
        assert provider.provider_name == "groq"
        assert "mixtral-8x7b-32768" in provider.supported_models
        assert "llama2-70b-4096" in provider.supported_models


class TestLLMProviderManager:
    """Test the LLM provider manager."""
    
    @pytest.fixture
    def manager(self):
        """Create a provider manager for testing."""
        return LLMProviderManager()
    
    def test_add_provider(self, manager):
        """Test adding a provider to the manager."""
        manager.add_provider(
            ProviderType.CLAUDE,
            "test-api-key",
            is_primary=True
        )
        
        assert ProviderType.CLAUDE in manager.providers
        assert manager.primary_provider == ProviderType.CLAUDE
        assert ProviderType.CLAUDE in manager.fallback_order
    
    def test_get_provider(self, manager):
        """Test getting a provider from the manager."""
        manager.add_provider(ProviderType.CLAUDE, "test-api-key")
        
        provider = manager.get_provider(ProviderType.CLAUDE)
        assert isinstance(provider, ClaudeProvider)
    
    def test_get_primary_provider(self, manager):
        """Test getting the primary provider."""
        manager.add_provider(ProviderType.CLAUDE, "test-api-key", is_primary=True)
        
        provider = manager.get_provider()  # No specific type = primary
        assert isinstance(provider, ClaudeProvider)
    
    def test_provider_not_available_error(self, manager):
        """Test error when requesting unavailable provider."""
        with pytest.raises(LLMProviderError, match="not available"):
            manager.get_provider(ProviderType.CLAUDE)
    
    @patch('app.ai.claude_provider.AsyncAnthropic')
    async def test_completion_with_fallback_success(self, mock_anthropic, manager):
        """Test successful completion with fallback."""
        # Mock successful response
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.model = "claude-3-sonnet-20240229"
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)
        mock_response.id = "test-id"
        mock_response.type = "message"
        mock_response.role = "assistant"
        
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        manager.add_provider(ProviderType.CLAUDE, "test-api-key")
        
        response = await manager.generate_completion_with_fallback("Test prompt")
        assert response.content == "Test response"
    
    async def test_completion_with_fallback_all_fail(self, manager):
        """Test fallback when all providers fail."""
        # Don't add any providers
        
        with pytest.raises(LLMProviderError, match="All providers failed"):
            await manager.generate_completion_with_fallback("Test prompt")