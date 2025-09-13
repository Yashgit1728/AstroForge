"""
Integration tests for mission generation prompts and parsing.
"""

import json
import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.ai.prompt_templates import (
    MissionPromptBuilder,
    MISSION_SPECIFICATION_SCHEMA,
    build_alternative_mission_prompt,
)
from app.ai.response_parser import MissionResponseParser, ParsedMissionResponse, AlternativeMissionResponse


class TestMissionPromptBuilder:
    """Test mission prompt building functionality."""
    
    def test_build_mission_generation_prompt(self):
        """Test building a mission generation prompt."""
        user_prompt = "I want to send a probe to Mars"
        
        prompt_template = MissionPromptBuilder.build_mission_generation_prompt(user_prompt)
        
        assert prompt_template.system_prompt is not None
        assert "space mission planner" in prompt_template.system_prompt.lower()
        assert user_prompt in prompt_template.user_prompt_template
        assert prompt_template.response_schema == MISSION_SPECIFICATION_SCHEMA
    
    def test_build_mission_refinement_prompt(self):
        """Test building a mission refinement prompt."""
        current_mission = {"name": "Mars Probe", "description": "Basic Mars mission"}
        refinement_request = "Make it faster"
        
        prompt_template = MissionPromptBuilder.build_mission_refinement_prompt(
            current_mission, refinement_request
        )
        
        assert prompt_template.system_prompt is not None
        assert refinement_request in prompt_template.user_prompt_template
        assert "Mars Probe" in prompt_template.system_prompt
    
    def test_build_alternative_mission_prompt(self):
        """Test building alternative mission suggestions prompt."""
        original_request = "Send humans to Jupiter"
        issues = "Jupiter is too far for current technology"
        
        prompt_template = build_alternative_mission_prompt(original_request, issues)
        
        assert original_request in prompt_template.user_prompt_template
        assert issues in prompt_template.user_prompt_template
        assert "alternative" in prompt_template.user_prompt_template.lower()


class TestMissionResponseParser:
    """Test mission response parsing functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create a mission response parser."""
        return MissionResponseParser()
    
    @pytest.fixture
    def valid_mission_response(self):
        """Create a valid mission response for testing."""
        return {
            "mission": {
                "name": "Mars Sample Return",
                "description": "Collect samples from Mars surface and return to Earth",
                "objectives": [
                    "Land on Mars surface",
                    "Collect geological samples",
                    "Return samples to Earth"
                ],
                "mission_type": "scientific",
                "difficulty_level": "advanced"
            },
            "spacecraft": {
                "vehicle_type": "Deep Space Probe",
                "mass_kg": 5000,
                "fuel_capacity_kg": 3000,
                "thrust_n": 2000,
                "specific_impulse_s": 350,
                "payload_mass_kg": 500
            },
            "trajectory": {
                "departure_body": "Earth",
                "target_body": "Mars",
                "transfer_type": "hohmann",
                "launch_window_start": "2026-07-15",
                "launch_window_end": "2026-08-15",
                "estimated_duration_days": 520,
                "total_delta_v_ms": 8500
            },
            "mission_phases": [
                {
                    "name": "Launch",
                    "description": "Launch from Earth",
                    "duration_days": 1,
                    "delta_v_ms": 3200
                },
                {
                    "name": "Cruise",
                    "description": "Transit to Mars",
                    "duration_days": 260,
                    "delta_v_ms": 100
                },
                {
                    "name": "Mars Operations",
                    "description": "Surface operations on Mars",
                    "duration_days": 30,
                    "delta_v_ms": 2000
                },
                {
                    "name": "Return",
                    "description": "Return to Earth",
                    "duration_days": 229,
                    "delta_v_ms": 3200
                }
            ],
            "constraints": {
                "max_mission_duration_days": 600,
                "budget_constraint_usd": 2000000000,
                "risk_tolerance": "medium"
            },
            "success_metrics": {
                "primary_success_criteria": [
                    "Successful landing on Mars",
                    "Sample collection completed",
                    "Successful return to Earth"
                ],
                "secondary_success_criteria": [
                    "Extended surface operations",
                    "Additional scientific measurements"
                ],
                "estimated_success_probability": 0.75
            }
        }
    
    def test_parse_valid_mission_response(self, parser, valid_mission_response):
        """Test parsing a valid mission response."""
        user_prompt = "Design a Mars sample return mission"
        
        result = parser.parse_mission_response(
            valid_mission_response,
            user_prompt
        )
        
        assert isinstance(result, ParsedMissionResponse)
        assert result.mission_data["name"] == "Mars Sample Return"
        assert result.mission_data["description"] is not None
        assert len(result.mission_data["objectives"]) == 3
        assert result.confidence_score > 0.5
        assert result.metadata["user_prompt"] == user_prompt
    
    def test_parse_mission_with_validation_issues(self, parser):
        """Test parsing a mission response with validation issues."""
        invalid_response = {
            "mission": {
                "name": "Invalid Mission",
                "description": "Test mission",
                "objectives": ["Test objective"],
                "mission_type": "invalid_type",  # Invalid type
                "difficulty_level": "impossible"  # Invalid difficulty
            },
            "spacecraft": {
                "vehicle_type": "Unknown Vehicle",
                "mass_kg": -100,  # Invalid mass
                "fuel_capacity_kg": 1000000,  # Too much fuel
                "thrust_n": 500,
                "specific_impulse_s": 300,
                "payload_mass_kg": 100
            },
            "trajectory": {
                "departure_body": "Pluto",  # Invalid body
                "target_body": "Alpha Centauri",  # Invalid body
                "transfer_type": "teleportation",  # Invalid transfer
                "launch_window_start": "invalid-date",
                "launch_window_end": "2025-01-01",
                "estimated_duration_days": 50000,  # Too long
                "total_delta_v_ms": 100000  # Too much delta-v
            },
            "mission_phases": [],
            "constraints": {
                "max_mission_duration_days": 100,
                "budget_constraint_usd": 1000000000,
                "risk_tolerance": "extreme"  # Invalid risk level
            }
        }
        
        result = parser.parse_mission_response(invalid_response, "Test prompt")
        
        assert isinstance(result, ParsedMissionResponse)
        assert len(result.validation_issues) > 0
        assert result.confidence_score < 0.8  # Should be lower due to issues
        
        # Check that fallback values were used
        assert result.mission_data["spacecraft"]["mass_kg"] > 0
        assert result.mission_data["trajectory"]["departure_body"] is not None
    
    def test_parse_alternative_mission_response(self, parser):
        """Test parsing alternative mission suggestions."""
        alternative_response = {
            "feasibility_analysis": {
                "is_feasible": False,
                "issues": [
                    "Mission duration exceeds current technology limits",
                    "Fuel requirements too high for available launch vehicles"
                ],
                "recommendations": [
                    "Consider robotic mission instead of crewed",
                    "Use gravity assists to reduce fuel requirements"
                ]
            },
            "alternatives": [
                {
                    "name": "Robotic Mars Mission",
                    "description": "Unmanned mission to Mars with sample return",
                    "advantages": ["Lower cost", "Reduced risk", "Proven technology"],
                    "trade_offs": ["No human presence", "Limited flexibility"],
                    "estimated_cost_usd": 500000000,
                    "estimated_duration_days": 400,
                    "success_probability": 0.85
                },
                {
                    "name": "Mars Orbital Mission",
                    "description": "Orbital reconnaissance of Mars",
                    "advantages": ["Much lower cost", "High success probability"],
                    "trade_offs": ["No surface operations", "Limited science return"],
                    "estimated_cost_usd": 200000000,
                    "estimated_duration_days": 300,
                    "success_probability": 0.95
                }
            ]
        }
        
        result = parser.parse_alternative_response(alternative_response, "Original request")
        
        assert isinstance(result, AlternativeMissionResponse)
        assert not result.is_feasible
        assert len(result.issues) == 2
        assert len(result.recommendations) == 2
        assert len(result.alternatives) == 2
        assert result.alternatives[0]["name"] == "Robotic Mars Mission"
    
    def test_parse_empty_response(self, parser):
        """Test parsing an empty or malformed response."""
        with pytest.raises(ValueError, match="Invalid mission response format"):
            parser.parse_mission_response({}, "Test prompt")
    
    def test_validation_rules_initialization(self, parser):
        """Test that validation rules are properly initialized."""
        rules = parser.validation_rules
        
        assert "mass_limits" in rules
        assert "valid_bodies" in rules
        assert "valid_transfer_types" in rules
        assert rules["mass_limits"]["min"] > 0
        assert rules["mass_limits"]["max"] > rules["mass_limits"]["min"]
    
    def test_numeric_field_validation(self, parser):
        """Test numeric field validation helper."""
        issues = []
        
        # Valid value
        result = parser._validate_numeric_field(100, "test_field", {"min": 0, "max": 200}, issues)
        assert result == 100
        assert len(issues) == 0
        
        # Below minimum
        result = parser._validate_numeric_field(-10, "test_field", {"min": 0, "max": 200}, issues)
        assert result == 0
        assert len(issues) == 1
        
        # Above maximum
        issues.clear()
        result = parser._validate_numeric_field(300, "test_field", {"min": 0, "max": 200}, issues)
        assert result == 200
        assert len(issues) == 1
        
        # Invalid type
        issues.clear()
        result = parser._validate_numeric_field("invalid", "test_field", {"min": 0, "max": 200}, issues)
        assert result == 0  # Should return minimum
        assert len(issues) == 1
    
    def test_date_parsing(self, parser):
        """Test date parsing functionality."""
        issues = []
        
        # Valid date
        result = parser._parse_date("2025-06-15", issues)
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 15
        assert len(issues) == 0
        
        # Invalid date format
        result = parser._parse_date("invalid-date", issues)
        assert result is not None  # Should return today's date
        assert len(issues) == 1
        
        # None date
        issues.clear()
        result = parser._parse_date(None, issues)
        assert result is not None  # Should return today's date
        assert len(issues) == 0
    
    def test_confidence_score_calculation(self, parser):
        """Test confidence score calculation."""
        # No issues, complete response
        complete_response = {
            "mission": {},
            "spacecraft": {},
            "trajectory": {},
            "mission_phases": [],
            "constraints": {},
            "success_metrics": {}
        }
        score = parser._calculate_confidence_score([], complete_response)
        assert score == 1.0
        
        # With validation issues
        issues = ["Issue 1", "Issue 2", "Issue 3"]
        score = parser._calculate_confidence_score(issues, complete_response)
        assert score < 1.0
        
        # Incomplete response
        incomplete_response = {"mission": {}}
        score = parser._calculate_confidence_score([], incomplete_response)
        assert score < 1.0


class TestIntegrationMissionGeneration:
    """Integration tests for the complete mission generation flow."""
    
    @pytest.fixture
    def parser(self):
        return MissionResponseParser()
    
    def test_end_to_end_mission_generation_flow(self, parser):
        """Test the complete flow from prompt to parsed mission."""
        # 1. Build prompt
        user_request = "Design a lunar sample return mission"
        prompt_template = MissionPromptBuilder.build_mission_generation_prompt(user_request)
        
        assert user_request in prompt_template.user_prompt_template
        assert prompt_template.response_schema is not None
        
        # 2. Simulate AI response (this would normally come from LLM)
        mock_ai_response = {
            "mission": {
                "name": "Lunar Sample Return",
                "description": "Automated mission to collect lunar samples",
                "objectives": ["Land on Moon", "Collect samples", "Return to Earth"],
                "mission_type": "scientific",
                "difficulty_level": "intermediate"
            },
            "spacecraft": {
                "vehicle_type": "Probe",
                "mass_kg": 2000,
                "fuel_capacity_kg": 1200,
                "thrust_n": 1000,
                "specific_impulse_s": 320,
                "payload_mass_kg": 200
            },
            "trajectory": {
                "departure_body": "Earth",
                "target_body": "Moon",
                "transfer_type": "hohmann",
                "launch_window_start": "2025-03-01",
                "launch_window_end": "2025-03-15",
                "estimated_duration_days": 14,
                "total_delta_v_ms": 3200
            },
            "mission_phases": [
                {
                    "name": "Launch",
                    "description": "Launch from Earth",
                    "duration_days": 1,
                    "delta_v_ms": 3200
                },
                {
                    "name": "Lunar Operations",
                    "description": "Land and collect samples",
                    "duration_days": 7,
                    "delta_v_ms": 0
                },
                {
                    "name": "Return",
                    "description": "Return to Earth",
                    "duration_days": 6,
                    "delta_v_ms": 0
                }
            ],
            "constraints": {
                "max_mission_duration_days": 30,
                "budget_constraint_usd": 500000000,
                "risk_tolerance": "medium"
            }
        }
        
        # 3. Parse response
        parsed_result = parser.parse_mission_response(mock_ai_response, user_request)
        
        # 4. Verify parsed result
        assert isinstance(parsed_result, ParsedMissionResponse)
        assert parsed_result.mission_data["name"] == "Lunar Sample Return"
        assert len(parsed_result.mission_data["objectives"]) == 3
        assert parsed_result.mission_data["spacecraft_config"]["mass_kg"] == 2000
        assert parsed_result.confidence_score > 0.7
        
        # 5. Verify the mission data can be used to create a Mission object
        mission_data = parsed_result.mission_data
        assert "spacecraft_config" in mission_data
        assert "trajectory" in mission_data
        assert "timeline" in mission_data
        assert "constraints" in mission_data