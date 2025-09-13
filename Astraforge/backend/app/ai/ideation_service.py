"""
Mission ideation service for AI-powered mission generation.

This service orchestrates the complete mission generation workflow,
including LLM provider management, prompt generation, response parsing,
and validation with feasibility checking.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from .llm_provider import LLMProviderError, LLMRateLimitError, LLMAuthenticationError
from .provider_factory import LLMProviderManager, ProviderType
from .prompt_templates import (
    MissionPromptBuilder,
    build_alternative_mission_prompt,
)
from .response_parser import (
    MissionResponseParser,
    ParsedMissionResponse,
    AlternativeMissionResponse,
)
from ..models.mission import Mission

logger = logging.getLogger(__name__)


class MissionIdeationService:
    """Service for AI-powered mission ideation and generation."""
    
    def __init__(self, provider_manager: LLMProviderManager):
        """
        Initialize the ideation service.
        
        Args:
            provider_manager: Configured LLM provider manager
        """
        self.provider_manager = provider_manager
        self.response_parser = MissionResponseParser()
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
    
    async def generate_mission(
        self,
        user_prompt: str,
        user_id: Optional[str] = None,
        provider_preference: Optional[ProviderType] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ParsedMissionResponse:
        """
        Generate a mission specification from a user prompt.
        
        Args:
            user_prompt: User's mission description
            user_id: Optional user ID for tracking
            provider_preference: Preferred LLM provider
            temperature: Sampling temperature for generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            ParsedMissionResponse with generated mission data
            
        Raises:
            MissionGenerationError: If generation fails after retries
        """
        logger.info(f"Generating mission for prompt: {user_prompt[:100]}...")
        
        # Build the prompt template
        prompt_template = MissionPromptBuilder.build_mission_generation_prompt(user_prompt)
        
        # Attempt generation with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Generate structured response
                if provider_preference:
                    provider = self.provider_manager.get_provider(provider_preference)
                    response_data = await provider.generate_structured_completion(
                        prompt=prompt_template.user_prompt_template,
                        response_schema=prompt_template.response_schema,
                        system_prompt=prompt_template.system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                else:
                    # Use fallback mechanism
                    response_data = await self.provider_manager.generate_structured_completion_with_fallback(
                        prompt=prompt_template.user_prompt_template,
                        response_schema=prompt_template.response_schema,
                        system_prompt=prompt_template.system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                
                # Parse and validate the response
                parsed_response = self.response_parser.parse_mission_response(
                    response_data=response_data,
                    user_prompt=user_prompt,
                    provider_metadata={
                        "attempt": attempt + 1,
                        "provider_preference": provider_preference,
                        "temperature": temperature,
                    }
                )
                
                # Perform feasibility check
                feasibility_issues = await self._check_mission_feasibility(parsed_response)
                if feasibility_issues:
                    parsed_response.validation_issues.extend(feasibility_issues)
                    # Reduce confidence score based on feasibility issues
                    parsed_response.confidence_score *= (1.0 - len(feasibility_issues) * 0.1)
                
                logger.info(f"Mission generated successfully on attempt {attempt + 1}")
                return parsed_response
                
            except LLMRateLimitError as e:
                logger.warning(f"Rate limit hit on attempt {attempt + 1}: {e}")
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                
            except LLMAuthenticationError as e:
                logger.error(f"Authentication failed: {e}")
                raise MissionGenerationError(f"Authentication failed: {e}")
                
            except Exception as e:
                logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        # All retries failed
        raise MissionGenerationError(f"Failed to generate mission after {self.max_retries} attempts: {last_error}")
    
    async def refine_mission(
        self,
        current_mission_data: Dict[str, Any],
        refinement_request: str,
        user_id: Optional[str] = None,
        provider_preference: Optional[ProviderType] = None,
    ) -> ParsedMissionResponse:
        """
        Refine an existing mission based on user feedback.
        
        Args:
            current_mission_data: Current mission specification
            refinement_request: User's refinement request
            user_id: Optional user ID for tracking
            provider_preference: Preferred LLM provider
            
        Returns:
            ParsedMissionResponse with refined mission data
        """
        logger.info(f"Refining mission: {refinement_request[:100]}...")
        
        # Build refinement prompt
        prompt_template = MissionPromptBuilder.build_mission_refinement_prompt(
            current_mission_data, refinement_request
        )
        
        try:
            # Generate refined mission
            if provider_preference:
                provider = self.provider_manager.get_provider(provider_preference)
                response_data = await provider.generate_structured_completion(
                    prompt=prompt_template.user_prompt_template,
                    response_schema=prompt_template.response_schema,
                    system_prompt=prompt_template.system_prompt,
                )
            else:
                response_data = await self.provider_manager.generate_structured_completion_with_fallback(
                    prompt=prompt_template.user_prompt_template,
                    response_schema=prompt_template.response_schema,
                    system_prompt=prompt_template.system_prompt,
                )
            
            # Parse response
            parsed_response = self.response_parser.parse_mission_response(
                response_data=response_data,
                user_prompt=refinement_request,
                provider_metadata={
                    "operation": "refinement",
                    "provider_preference": provider_preference,
                }
            )
            
            logger.info("Mission refined successfully")
            return parsed_response
            
        except Exception as e:
            logger.error(f"Mission refinement failed: {e}")
            raise MissionGenerationError(f"Failed to refine mission: {e}")
    
    async def generate_alternatives(
        self,
        original_request: str,
        identified_issues: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> AlternativeMissionResponse:
        """
        Generate alternative mission approaches when the original is not feasible.
        
        Args:
            original_request: Original mission request
            identified_issues: List of identified feasibility issues
            user_id: Optional user ID for tracking
            
        Returns:
            AlternativeMissionResponse with alternative approaches
        """
        logger.info(f"Generating alternatives for: {original_request[:100]}...")
        
        # Build alternative mission prompt
        issues_text = "; ".join(identified_issues) if identified_issues else None
        prompt_template = build_alternative_mission_prompt(original_request, issues_text)
        
        try:
            # Generate alternatives
            response_data = await self.provider_manager.generate_structured_completion_with_fallback(
                prompt=prompt_template.user_prompt_template,
                response_schema=prompt_template.response_schema,
                system_prompt=prompt_template.system_prompt,
            )
            
            # Parse alternatives
            alternatives_response = self.response_parser.parse_alternative_response(
                response_data=response_data,
                original_request=original_request,
            )
            
            logger.info(f"Generated {len(alternatives_response.alternatives)} alternatives")
            return alternatives_response
            
        except Exception as e:
            logger.error(f"Alternative generation failed: {e}")
            raise MissionGenerationError(f"Failed to generate alternatives: {e}")
    
    async def validate_mission_concept(
        self,
        mission_concept: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate a mission concept for basic feasibility.
        
        Args:
            mission_concept: Brief mission concept description
            user_id: Optional user ID for tracking
            
        Returns:
            Dictionary with validation results
        """
        logger.info(f"Validating mission concept: {mission_concept[:100]}...")
        
        validation_prompt = f"""
        Analyze the following mission concept for basic feasibility:
        
        "{mission_concept}"
        
        Provide a brief assessment covering:
        1. Technical feasibility with current technology
        2. Estimated complexity level (1-5 scale)
        3. Major challenges or risks
        4. Recommended approach or mission type
        
        Keep the response concise and practical.
        """
        
        try:
            response = await self.provider_manager.generate_completion_with_fallback(
                prompt=validation_prompt,
                system_prompt="You are a space mission feasibility analyst. Provide practical, realistic assessments.",
                temperature=0.3,  # Lower temperature for more consistent analysis
            )
            
            return {
                "concept": mission_concept,
                "analysis": response.content,
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": 0.8,
            }
            
        except Exception as e:
            logger.error(f"Mission concept validation failed: {e}")
            return {
                "concept": mission_concept,
                "analysis": "Unable to analyze mission concept due to technical issues.",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": 0.0,
            }
    
    async def _check_mission_feasibility(
        self,
        parsed_mission: ParsedMissionResponse,
    ) -> List[str]:
        """
        Check mission feasibility and return list of issues.
        
        Args:
            parsed_mission: Parsed mission response to check
            
        Returns:
            List of feasibility issues
        """
        issues = []
        mission_data = parsed_mission.mission_data
        
        try:
            # Check spacecraft configuration
            spacecraft = mission_data.get("spacecraft_config", {})
            mass = spacecraft.get("mass_kg", 0)
            fuel = spacecraft.get("fuel_capacity_kg", 0)
            thrust = spacecraft.get("thrust_n", 0)
            isp = spacecraft.get("specific_impulse_s", 0)
            
            # Basic physics checks
            if fuel > mass * 0.9:
                issues.append("Fuel mass exceeds 90% of total spacecraft mass")
            
            if thrust <= 0:
                issues.append("Spacecraft has no propulsion capability")
            
            # Delta-v feasibility check
            trajectory = mission_data.get("trajectory", {})
            required_delta_v = trajectory.get("total_delta_v", 0)
            
            if mass > 0 and fuel > 0 and isp > 0:
                dry_mass = mass - fuel
                if dry_mass > 0:
                    theoretical_delta_v = isp * 9.81 * (mass / dry_mass)
                    if required_delta_v > theoretical_delta_v * 1.1:  # 10% margin
                        issues.append(f"Required delta-v ({required_delta_v:.0f} m/s) exceeds spacecraft capability ({theoretical_delta_v:.0f} m/s)")
            
            # Mission duration checks
            duration = trajectory.get("flight_time_days", 0)
            constraints = mission_data.get("constraints", {})
            max_duration = constraints.get("max_duration_days", 3650)
            
            if duration > max_duration:
                issues.append(f"Mission duration ({duration:.0f} days) exceeds constraints ({max_duration:.0f} days)")
            
            # Destination feasibility
            target = trajectory.get("target_body")
            if target and str(target).lower() in ["jupiter", "saturn"]:
                if duration < 365:
                    issues.append(f"Mission to {target} is unrealistically short ({duration:.0f} days)")
            
        except Exception as e:
            logger.warning(f"Feasibility check failed: {e}")
            issues.append("Unable to complete feasibility analysis")
        
        return issues
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all configured providers."""
        status = {
            "providers": {},
            "primary_provider": self.provider_manager.primary_provider,
            "fallback_order": self.provider_manager.fallback_order,
        }
        
        for provider_type, provider in self.provider_manager.providers.items():
            status["providers"][provider_type] = {
                "name": provider.provider_name,
                "model": provider.model,
                "supported_models": provider.supported_models,
            }
        
        return status


class MissionGenerationError(Exception):
    """Exception raised when mission generation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


# Factory function for creating ideation service
def create_ideation_service(
    openai_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    groq_api_key: Optional[str] = None,
    primary_provider: ProviderType = ProviderType.CLAUDE,
) -> MissionIdeationService:
    """
    Create a mission ideation service with configured providers.
    
    Args:
        openai_api_key: OpenAI API key
        anthropic_api_key: Anthropic API key
        groq_api_key: Groq API key
        primary_provider: Primary provider to use
        
    Returns:
        Configured MissionIdeationService
        
    Raises:
        ValueError: If no valid API keys are provided
    """
    provider_manager = LLMProviderManager()
    
    # Add providers based on available API keys
    providers_added = 0
    
    if anthropic_api_key:
        provider_manager.add_provider(
            ProviderType.CLAUDE,
            anthropic_api_key,
            is_primary=(primary_provider == ProviderType.CLAUDE)
        )
        providers_added += 1
    
    if openai_api_key:
        provider_manager.add_provider(
            ProviderType.OPENAI,
            openai_api_key,
            is_primary=(primary_provider == ProviderType.OPENAI)
        )
        providers_added += 1
    
    if groq_api_key:
        provider_manager.add_provider(
            ProviderType.GROQ,
            groq_api_key,
            is_primary=(primary_provider == ProviderType.GROQ)
        )
        providers_added += 1
    
    if providers_added == 0:
        raise ValueError("At least one API key must be provided")
    
    logger.info(f"Created ideation service with {providers_added} providers")
    return MissionIdeationService(provider_manager)