"""
Integration tests for the complete AI integration layer.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import os

from app.ai import (
    create_ideation_service,
    MissionIdeationService,
    ProviderType,
    LLMProviderFactory,
)


class TestAIIntegrationLayer:
    """Test the complete AI integration layer."""
    
    def test_import_all_ai_components(self):
        """Test that all AI components can be imported successfully."""
        from app.ai import (
            LLMProvider,
            LLMResponse,
            LLMProviderError,
            ClaudeProvider,
            OpenAIProvider,
            GroqProvider,
            LLMProviderFactory,
            LLMProviderManager,
            ProviderType,
            MissionPromptBuilder,
            MissionResponseParser,
            ParsedMissionResponse,
            AlternativeMissionResponse,
            MissionIdeationService,
            MissionGenerationError,
            create_ideation_service,
        )
        
        # Verify all imports are successful
        assert LLMProvider is not None
        assert LLMResponse is not None
        assert ClaudeProvider is not None
        assert OpenAIProvider is not None
        assert GroqProvider is not None
        assert MissionIdeationService is not None
    
    def test_provider_factory_creates_all_providers(self):
        """Test that the provider factory can create all provider types."""
        # Test Claude provider
        claude_provider = LLMProviderFactory.create_provider(
            ProviderType.CLAUDE,
            "test-api-key"
        )
        assert claude_provider.provider_name == "claude"
        assert "claude" in claude_provider.model.lower()
        
        # Test OpenAI provider
        openai_provider = LLMProviderFactory.create_provider(
            ProviderType.OPENAI,
            "test-api-key"
        )
        assert openai_provider.provider_name == "openai"
        assert "gpt" in openai_provider.model.lower()
        
        # Test Groq provider
        groq_provider = LLMProviderFactory.create_provider(
            ProviderType.GROQ,
            "test-api-key"
        )
        assert groq_provider.provider_name == "groq"
        assert groq_provider.model is not None
    
    def test_provider_supported_models(self):
        """Test that providers report their supported models correctly."""
        for provider_type in [ProviderType.CLAUDE, ProviderType.OPENAI, ProviderType.GROQ]:
            models = LLMProviderFactory.get_provider_models(provider_type)
            assert isinstance(models, list)
            assert len(models) > 0
            
            # Each model should be a string
            for model in models:
                assert isinstance(model, str)
                assert len(model) > 0
    
    @patch.dict(os.environ, {
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'OPENAI_API_KEY': 'test-openai-key',
        'GROQ_API_KEY': 'test-groq-key'
    })
    def test_ideation_service_creation_from_environment(self):
        """Test creating ideation service from environment variables."""
        # This would normally read from environment
        service = create_ideation_service(
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            groq_api_key=os.getenv('GROQ_API_KEY'),
        )
        
        assert isinstance(service, MissionIdeationService)
        
        # Check provider status
        status = service.get_provider_status()
        assert "providers" in status
        assert len(status["providers"]) == 3  # All three providers should be configured
    
    @pytest.mark.asyncio
    async def test_end_to_end_mission_generation_flow(self):
        """Test the complete end-to-end mission generation flow."""
        # Create a mock ideation service
        with patch('app.ai.ideation_service.LLMProviderManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            # Mock the AI response
            mock_ai_response = {
                "mission": {
                    "name": "Europa Ice Probe",
                    "description": "Robotic mission to study Europa's subsurface ocean",
                    "objectives": ["Penetrate ice shell", "Analyze ocean composition", "Search for life signs"],
                    "mission_type": "scientific",
                    "difficulty_level": "expert"
                },
                "spacecraft": {
                    "vehicle_type": "Probe",
                    "mass_kg": 4000,
                    "fuel_capacity_kg": 2400,
                    "thrust_n": 2000,
                    "specific_impulse_s": 340,
                    "payload_mass_kg": 600
                },
                "trajectory": {
                    "departure_body": "Earth",
                    "target_body": "Jupiter",
                    "transfer_type": "gravity_assist",
                    "launch_window_start": "2030-01-01",
                    "launch_window_end": "2030-02-01",
                    "estimated_duration_days": 2190,  # ~6 years
                    "total_delta_v_ms": 12000
                },
                "mission_phases": [
                    {
                        "name": "Launch and Earth Escape",
                        "description": "Launch from Earth and escape Earth's gravity",
                        "duration_days": 30,
                        "delta_v_ms": 3200
                    },
                    {
                        "name": "Interplanetary Cruise",
                        "description": "Travel to Jupiter system with gravity assists",
                        "duration_days": 2000,
                        "delta_v_ms": 2000
                    },
                    {
                        "name": "Jupiter System Insertion",
                        "description": "Enter Jupiter orbit and approach Europa",
                        "duration_days": 100,
                        "delta_v_ms": 4000
                    },
                    {
                        "name": "Europa Operations",
                        "description": "Ice penetration and ocean analysis",
                        "duration_days": 60,
                        "delta_v_ms": 2800
                    }
                ],
                "constraints": {
                    "max_mission_duration_days": 2500,
                    "budget_constraint_usd": 3000000000,
                    "risk_tolerance": "high"
                }
            }
            
            mock_manager.generate_structured_completion_with_fallback = AsyncMock(return_value=mock_ai_response)
            
            # Create the service
            service = create_ideation_service(anthropic_api_key="test-key")
            
            # Test mission generation
            user_prompt = "Design a mission to explore Europa's subsurface ocean"
            result = await service.generate_mission(user_prompt)
            
            # Verify the result
            assert result.mission_data["name"] == "Europa Ice Probe"
            assert len(result.mission_data["objectives"]) == 3
            assert result.mission_data["spacecraft_config"]["mass_kg"] == 4000
            assert result.mission_data["trajectory"]["target_body"].value == "jupiter"
            assert result.confidence_score > 0.0
            
            # Verify feasibility check was performed
            # Europa missions are complex, so there might be some validation issues
            assert isinstance(result.validation_issues, list)
            
            # Test mission concept validation
            concept_result = await service.validate_mission_concept("Small probe to Europa")
            assert "concept" in concept_result
            assert "analysis" in concept_result
    
    def test_ai_layer_error_handling(self):
        """Test error handling throughout the AI layer."""
        # Test provider creation with invalid type
        with pytest.raises(Exception):
            LLMProviderFactory.create_provider("invalid_provider", "test-key")
        
        # Test ideation service creation with no API keys
        with pytest.raises(ValueError, match="At least one API key must be provided"):
            create_ideation_service()
    
    def test_provider_abstraction_consistency(self):
        """Test that all providers implement the same interface consistently."""
        providers = [
            LLMProviderFactory.create_provider(ProviderType.CLAUDE, "test-key"),
            LLMProviderFactory.create_provider(ProviderType.OPENAI, "test-key"),
            LLMProviderFactory.create_provider(ProviderType.GROQ, "test-key"),
        ]
        
        for provider in providers:
            # All providers should have these properties
            assert hasattr(provider, 'provider_name')
            assert hasattr(provider, 'model')
            assert hasattr(provider, 'supported_models')
            assert hasattr(provider, 'api_key')
            
            # All providers should have these methods
            assert hasattr(provider, 'generate_completion')
            assert hasattr(provider, 'generate_structured_completion')
            
            # Properties should return expected types
            assert isinstance(provider.provider_name, str)
            assert isinstance(provider.model, str)
            assert isinstance(provider.supported_models, list)
            assert len(provider.supported_models) > 0
    
    def test_mission_prompt_and_schema_consistency(self):
        """Test that mission prompts and schemas are consistent."""
        from app.ai.prompt_templates import (
            MissionPromptBuilder,
            MISSION_SPECIFICATION_SCHEMA,
            build_alternative_mission_prompt,
        )
        
        # Test mission generation prompt
        prompt_template = MissionPromptBuilder.build_mission_generation_prompt("Test mission")
        assert prompt_template.system_prompt is not None
        assert "Test mission" in prompt_template.user_prompt_template
        assert prompt_template.response_schema == MISSION_SPECIFICATION_SCHEMA
        
        # Test alternative mission prompt
        alt_prompt = build_alternative_mission_prompt("Original request", "Issues")
        assert "Original request" in alt_prompt.user_prompt_template
        assert "Issues" in alt_prompt.user_prompt_template
        
        # Verify schema has required sections
        required_sections = ["mission", "spacecraft", "trajectory", "mission_phases", "constraints"]
        schema_properties = MISSION_SPECIFICATION_SCHEMA["properties"]
        
        for section in required_sections:
            assert section in schema_properties
            assert "type" in schema_properties[section]
    
    def test_response_parser_validation_rules(self):
        """Test that response parser validation rules are comprehensive."""
        from app.ai.response_parser import MissionResponseParser
        
        parser = MissionResponseParser()
        rules = parser.validation_rules
        
        # Check that all expected validation rules exist
        expected_rules = [
            "mass_limits",
            "fuel_capacity_limits", 
            "thrust_limits",
            "specific_impulse_limits",
            "delta_v_limits",
            "duration_limits",
            "valid_bodies",
            "valid_transfer_types",
            "valid_mission_types",
        ]
        
        for rule in expected_rules:
            assert rule in rules
            
        # Check that numeric limits have min/max
        numeric_rules = ["mass_limits", "fuel_capacity_limits", "thrust_limits"]
        for rule in numeric_rules:
            assert "min" in rules[rule]
            assert "max" in rules[rule]
            assert rules[rule]["min"] < rules[rule]["max"]
        
        # Check that enum lists are not empty
        enum_rules = ["valid_bodies", "valid_transfer_types", "valid_mission_types"]
        for rule in enum_rules:
            assert isinstance(rules[rule], list)
            assert len(rules[rule]) > 0