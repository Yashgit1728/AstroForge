"""
Claude (Anthropic) LLM provider implementation.
"""

import json
import logging
from typing import Dict, Any, Optional, List

import anthropic
from anthropic import AsyncAnthropic

from .llm_provider import (
    LLMProvider,
    LLMResponse,
    LLMProviderError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMValidationError,
)

logger = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    """Claude (Anthropic) LLM provider."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        super().__init__(api_key, model)
        self.client = AsyncAnthropic(api_key=api_key)
    
    @property
    def provider_name(self) -> str:
        return "claude"
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
        ]
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion using Claude."""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 4096,
            }
            
            if system_prompt:
                request_params["system"] = system_prompt
            
            # Add any additional parameters
            request_params.update(kwargs)
            
            logger.debug(f"Making Claude API request with model {self.model}")
            response = await self.client.messages.create(**request_params)
            
            return LLMResponse(
                content=response.content[0].text,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                metadata={
                    "id": response.id,
                    "type": response.type,
                    "role": response.role,
                }
            )
            
        except anthropic.RateLimitError as e:
            logger.error(f"Claude rate limit exceeded: {e}")
            raise LLMRateLimitError(str(e), self.provider_name, "rate_limit")
        except anthropic.AuthenticationError as e:
            logger.error(f"Claude authentication failed: {e}")
            raise LLMAuthenticationError(str(e), self.provider_name, "auth_failed")
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise LLMProviderError(str(e), self.provider_name)
    
    async def generate_structured_completion(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a structured completion using Claude."""
        # Create a system prompt that includes schema instructions
        schema_instruction = f"""
You must respond with valid JSON that matches this exact schema:
{json.dumps(response_schema, indent=2)}

Ensure your response is valid JSON and follows the schema precisely.
"""
        
        if system_prompt:
            combined_system_prompt = f"{system_prompt}\n\n{schema_instruction}"
        else:
            combined_system_prompt = schema_instruction
        
        try:
            response = await self.generate_completion(
                prompt=prompt,
                system_prompt=combined_system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Parse and validate the JSON response
            try:
                parsed_response = json.loads(response.content)
                # Basic validation - could be enhanced with jsonschema
                return parsed_response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude JSON response: {e}")
                raise LLMValidationError(
                    f"Invalid JSON response: {e}",
                    self.provider_name,
                    "json_parse_error"
                )
                
        except LLMProviderError:
            # Re-raise provider errors as-is
            raise
        except Exception as e:
            logger.error(f"Claude structured completion error: {e}")
            raise LLMProviderError(str(e), self.provider_name)