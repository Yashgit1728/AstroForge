"""
OpenAI LLM provider implementation.
"""

import json
import logging
from typing import Dict, Any, Optional, List

import openai
from openai import AsyncOpenAI

from .llm_provider import (
    LLMProvider,
    LLMResponse,
    LLMProviderError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMValidationError,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=api_key)
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "gpt-4-turbo-preview",
            "gpt-4-1106-preview",
            "gpt-4",
            "gpt-4-32k",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion using OpenAI."""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            # Add any additional parameters
            request_params.update(kwargs)
            
            logger.debug(f"Making OpenAI API request with model {self.model}")
            response = await self.client.chat.completions.create(**request_params)
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                metadata={
                    "id": response.id,
                    "object": response.object,
                    "created": response.created,
                    "finish_reason": response.choices[0].finish_reason,
                }
            )
            
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise LLMRateLimitError(str(e), self.provider_name, "rate_limit")
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {e}")
            raise LLMAuthenticationError(str(e), self.provider_name, "auth_failed")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
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
        """Generate a structured completion using OpenAI."""
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
            # Use function calling for better structured responses if available
            if "gpt-4" in self.model or "gpt-3.5-turbo" in self.model:
                # Try using function calling for more reliable structured output
                function_schema = {
                    "name": "generate_mission_data",
                    "description": "Generate structured mission data",
                    "parameters": response_schema
                }
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    functions=[function_schema],
                    function_call={"name": "generate_mission_data"},
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                if response.choices[0].message.function_call:
                    try:
                        return json.loads(response.choices[0].message.function_call.arguments)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Function call JSON parse failed, falling back to regular completion: {e}")
            
            # Fallback to regular completion with schema instructions
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
                return parsed_response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI JSON response: {e}")
                raise LLMValidationError(
                    f"Invalid JSON response: {e}",
                    self.provider_name,
                    "json_parse_error"
                )
                
        except LLMProviderError:
            # Re-raise provider errors as-is
            raise
        except Exception as e:
            logger.error(f"OpenAI structured completion error: {e}")
            raise LLMProviderError(str(e), self.provider_name)