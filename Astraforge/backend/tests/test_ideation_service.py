"""
Tests for the mission ideation service.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

from app.ai import (
    MissionIdeationService,
    MissionGenerationError,
    create_ideation_service,
    LLMProviderManager,
    ProviderType,
    ParsedMissionResponse,
    AlternativeMissionResponse,
)


class TestMissionIdeationService:
    """Test the mission ideation service."""
    
    @pytest.fixture
    def mock_provider_manager(self):
        """Create a mock provider manager."""
        manager = Mock(spec=LLMProviderManager)
        manager.generate_structured_completion_with_fallback = AsyncMock()
        manager.generate_completion_with_fallback = AsyncMock()
        manager.get_provider = Mock()
        manager.primary_provider = ProviderType.CLAUDE
        manager.fallback_order = [ProviderType.CLAUDE, ProviderType.OPENAI]
        manager.providers = {ProviderType.CLAUDE: Mock()}
        return manager
    
    @pytest.fixture
    def ideation_service(self, mock_provider_manager):
        """Create an ideation service with mocked provider manager."""
        return MissionIdeationService(mock_provider_manager)
    
    @pytest.fixture
    def valid_ai_response(self):
        """Create a valid AI response for testing."""
        return {
            "mission": {
                "name": "Mars Exploration Mission",
                "description": "Robotic mission to explore Mars surface",
                "objectives": ["Land on Mars", "Collect samples", "Analyze geology"],
                "mission_type": "scientific",
                "difficulty_level": "advanced"
            },
            "spacecraft": {
                "vehicle_type": "Probe",
                "mass_kg": 3000,
                "fuel_capacity_kg": 1800,
                "thrust_n": 1500,
                "specific_impulse_s": 320,
                "payload_mass_kg": 400
            },
            "trajectory": {
                "departure_body": "Earth",
                "target_body": "Mars",
                "transfer_type": "hohmann",
                "launch_window_start": "2026-07-01",
                "launch_window_end": "2026-08-01",
                "estimated_duration_days": 300,
                "total_delta_v_ms": 6000
            },
            "mission_phases": [
                {
                    "name": "Launch",
                    "description": "Launch from Earth",
                    "duration_days": 1,
                    "delta_v_ms": 3200
                },
                {
                    "name": "Transit",
                    "description": "Travel to Mars",
                    "duration_days": 260,
                    "delta_v_ms": 100
                },
                {
                    "name": "Mars Operations",
                    "description": "Surface operations",
                    "duration_days": 39,
                    "delta_v_ms": 2700
                }
            ],
            "constraints": {
                "max_mission_duration_days": 400,
                "budget_constraint_usd": 1500000000,
                "risk_tolerance": "medium"
            }
        }
    
    @pytest.mark.asyncio
    async def test_generate_mission_success(self, ideation_service, mock_provider_manager, valid_ai_response):
        """Test successful mission generation."""
        # Mock the provider response
        mock_provider_manager.generate_structured_completion_with_fallback.return_value = valid_ai_response
        
        user_prompt = "Design a mission to explore Mars"
        result = await ideation_service.generate_mission(user_prompt)
        
        assert isinstance(result, ParsedMissionResponse)
        assert result.mission_data["name"] == "Mars Exploration Mission"
        assert len(result.mission_data["objectives"]) == 3
        assert result.confidence_score > 0.0
        assert result.metadata["user_prompt"] == user_prompt
        
        # Verify the provider was called correctly
        mock_provider_manager.generate_structured_completion_with_fallback.assert_called_once()
        call_args = mock_provider_manager.generate_structured_completion_with_fallback.call_args
        assert user_prompt in call_args.kwargs["prompt"]
    
    @pytest.mark.asyncio
    async def test_generate_mission_with_provider_preference(self, ideation_service, mock_provider_manager, valid_ai_response):
        """Test mission generation with specific provider preference."""
        # Mock provider
        mock_provider = AsyncMock()
        mock_provider.generate_structured_completion.return_value = valid_ai_response
        mock_provider_manager.get_provider.return_value = mock_provider
        
        user_prompt = "Design a lunar mission"
        result = await ideation_service.generate_mission(
            user_prompt,
            provider_preference=ProviderType.OPENAI
        )
        
        assert isinstance(result, ParsedMissionResponse)
        mock_provider_manager.get_provider.assert_called_once_with(ProviderType.OPENAI)
        mock_provider.generate_structured_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_mission_with_retries(self, ideation_service, mock_provider_manager, valid_ai_response):
        """Test mission generation with retry logic."""
        # First call fails, second succeeds
        mock_provider_manager.generate_structured_completion_with_fallback.side_effect = [
            Exception("Temporary failure"),
            valid_ai_response
        ]
        
        user_prompt = "Design a mission to Venus"
        result = await ideation_service.generate_mission(user_prompt)
        
        assert isinstance(result, ParsedMissionResponse)
        assert mock_provider_manager.generate_structured_completion_with_fallback.call_count == 2
    
    @pytest.mark.asyncio
    async def test_generate_mission_max_retries_exceeded(self, ideation_service, mock_provider_manager):
        """Test mission generation when max retries are exceeded."""
        # All calls fail
        mock_provider_manager.generate_structured_completion_with_fallback.side_effect = Exception("Persistent failure")
        
        user_prompt = "Design a mission to Jupiter"
        
        with pytest.raises(MissionGenerationError, match="Failed to generate mission after"):
            await ideation_service.generate_mission(user_prompt)
        
        assert mock_provider_manager.generate_structured_completion_with_fallback.call_count == ideation_service.max_retries
    
    @pytest.mark.asyncio
    async def test_refine_mission(self, ideation_service, mock_provider_manager, valid_ai_response):
        """Test mission refinement functionality."""
        mock_provider_manager.generate_structured_completion_with_fallback.return_value = valid_ai_response
        
        current_mission = {"name": "Basic Mars Mission", "description": "Simple Mars mission"}
        refinement_request = "Make it more ambitious with sample return"
        
        result = await ideation_service.refine_mission(current_mission, refinement_request)
        
        assert isinstance(result, ParsedMissionResponse)
        assert result.metadata["operation"] == "refinement"
        
        # Verify the refinement prompt was used
        call_args = mock_provider_manager.generate_structured_completion_with_fallback.call_args
        assert refinement_request in call_args.kwargs["prompt"]
    
    @pytest.mark.asyncio
    async def test_generate_alternatives(self, ideation_service, mock_provider_manager):
        """Test alternative mission generation."""
        alternative_response = {
            "feasibility_analysis": {
                "is_feasible": False,
                "issues": ["Too expensive", "Technology not ready"],
                "recommendations": ["Use robotic mission", "Reduce scope"]
            },
            "alternatives": [
                {
                    "name": "Robotic Alternative",
                    "description": "Unmanned mission with similar objectives",
                    "advantages": ["Lower cost", "Reduced risk"],
                    "trade_offs": ["No human presence"],
                    "estimated_cost_usd": 500000000,
                    "estimated_duration_days": 200,
                    "success_probability": 0.9
                }
            ]
        }
        
        mock_provider_manager.generate_structured_completion_with_fallback.return_value = alternative_response
        
        original_request = "Send humans to Mars"
        issues = ["Budget too high", "Technology not ready"]
        
        result = await ideation_service.generate_alternatives(original_request, issues)
        
        assert isinstance(result, AlternativeMissionResponse)
        assert not result.is_feasible
        assert len(result.issues) == 2
        assert len(result.alternatives) == 1
        assert result.alternatives[0]["name"] == "Robotic Alternative"
    
    @pytest.mark.asyncio
    async def test_validate_mission_concept(self, ideation_service, mock_provider_manager):
        """Test mission concept validation."""
        mock_response = Mock()
        mock_response.content = "This mission concept is technically feasible with current technology. Complexity level: 3/5."
        mock_provider_manager.generate_completion_with_fallback.return_value = mock_response
        
        concept = "Small satellite constellation for Earth observation"
        result = await ideation_service.validate_mission_concept(concept)
        
        assert result["concept"] == concept
        assert "feasible" in result["analysis"]
        assert result["confidence"] == 0.8
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_validate_mission_concept_error_handling(self, ideation_service, mock_provider_manager):
        """Test mission concept validation error handling."""
        mock_provider_manager.generate_completion_with_fallback.side_effect = Exception("API error")
        
        concept = "Impossible mission to the sun"
        result = await ideation_service.validate_mission_concept(concept)
        
        assert result["concept"] == concept
        assert "Unable to analyze" in result["analysis"]
        assert "error" in result
        assert result["confidence"] == 0.0
    
    def test_feasibility_check_fuel_mass_issue(self, ideation_service):
        """Test feasibility check for fuel mass issues."""
        parsed_mission = Mock()
        parsed_mission.mission_data = {
            "spacecraft_config": {
                "mass_kg": 1000,
                "fuel_capacity_kg": 950,  # 95% of total mass - too much
                "thrust_n": 1000,
                "specific_impulse_s": 300,
            },
            "trajectory": {
                "total_delta_v": 5000,
                "flight_time_days": 100,
            },
            "constraints": {
                "max_duration_days": 200,
            }
        }
        
        issues = ideation_service._check_mission_feasibility(parsed_mission)
        
        assert any("Fuel mass exceeds 90%" in issue for issue in issues)
    
    def test_feasibility_check_delta_v_issue(self, ideation_service):
        """Test feasibility check for delta-v capability issues."""
        parsed_mission = Mock()
        parsed_mission.mission_data = {
            "spacecraft_config": {
                "mass_kg": 1000,
                "fuel_capacity_kg": 200,  # Low fuel capacity
                "thrust_n": 1000,
                "specific_impulse_s": 300,
            },
            "trajectory": {
                "total_delta_v": 10000,  # Very high delta-v requirement
                "flight_time_days": 100,
            },
            "constraints": {
                "max_duration_days": 200,
            }
        }
        
        issues = ideation_service._check_mission_feasibility(parsed_mission)
        
        assert any("Required delta-v" in issue and "exceeds spacecraft capability" in issue for issue in issues)
    
    def test_get_provider_status(self, ideation_service, mock_provider_manager):
        """Test getting provider status."""
        mock_provider = Mock()
        mock_provider.provider_name = "claude"
        mock_provider.model = "claude-3-sonnet-20240229"
        mock_provider.supported_models = ["claude-3-sonnet-20240229", "claude-3-opus-20240229"]
        
        mock_provider_manager.providers = {ProviderType.CLAUDE: mock_provider}
        
        status = ideation_service.get_provider_status()
        
        assert "providers" in status
        assert "primary_provider" in status
        assert "fallback_order" in status
        assert ProviderType.CLAUDE in status["providers"]
        assert status["providers"][ProviderType.CLAUDE]["name"] == "claude"


class TestCreateIdeationService:
    """Test the ideation service factory function."""
    
    @patch('app.ai.ideation_service.LLMProviderManager')
    def test_create_ideation_service_with_all_providers(self, mock_manager_class):
        """Test creating ideation service with all providers."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        service = create_ideation_service(
            openai_api_key="openai-key",
            anthropic_api_key="anthropic-key",
            groq_api_key="groq-key",
            primary_provider=ProviderType.OPENAI
        )
        
        assert isinstance(service, MissionIdeationService)
        assert mock_manager.add_provider.call_count == 3
        
        # Check that providers were added with correct parameters
        calls = mock_manager.add_provider.call_args_list
        provider_types = [call[0][0] for call in calls]
        assert ProviderType.CLAUDE in provider_types
        assert ProviderType.OPENAI in provider_types
        assert ProviderType.GROQ in provider_types
    
    @patch('app.ai.ideation_service.LLMProviderManager')
    def test_create_ideation_service_single_provider(self, mock_manager_class):
        """Test creating ideation service with single provider."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        service = create_ideation_service(
            anthropic_api_key="anthropic-key",
            primary_provider=ProviderType.CLAUDE
        )
        
        assert isinstance(service, MissionIdeationService)
        assert mock_manager.add_provider.call_count == 1
        
        # Check that only Claude provider was added
        call_args = mock_manager.add_provider.call_args
        assert call_args[0][0] == ProviderType.CLAUDE
        assert call_args.kwargs["is_primary"] is True
    
    def test_create_ideation_service_no_api_keys(self):
        """Test creating ideation service with no API keys raises error."""
        with pytest.raises(ValueError, match="At least one API key must be provided"):
            create_ideation_service()
    
    @patch('app.ai.ideation_service.LLMProviderManager')
    def test_create_ideation_service_partial_keys(self, mock_manager_class):
        """Test creating ideation service with partial API keys."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        service = create_ideation_service(
            openai_api_key="openai-key",
            groq_api_key="groq-key",  # No Anthropic key
            primary_provider=ProviderType.GROQ
        )
        
        assert isinstance(service, MissionIdeationService)
        assert mock_manager.add_provider.call_count == 2
        
        # Check that only OpenAI and Groq providers were added
        calls = mock_manager.add_provider.call_args_list
        provider_types = [call[0][0] for call in calls]
        assert ProviderType.OPENAI in provider_types
        assert ProviderType.GROQ in provider_types
        assert ProviderType.CLAUDE not in provider_types


class TestMissionGenerationError:
    """Test the mission generation error class."""
    
    def test_mission_generation_error_basic(self):
        """Test basic mission generation error."""
        error = MissionGenerationError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {}
    
    def test_mission_generation_error_with_details(self):
        """Test mission generation error with details."""
        details = {"provider": "claude", "attempt": 3}
        error = MissionGenerationError("Test error with details", details)
        
        assert error.message == "Test error with details"
        assert error.details == details