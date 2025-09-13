"""
Response parser for AI-generated mission specifications.

This module handles parsing, validation, and transformation of AI responses
into structured mission data that can be used by the application.
"""

import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, ValidationError, Field, validator

from ..models.mission import (
    Mission,
    SpacecraftConfig,
    TrajectoryPlan,
    MissionConstraints,
    MissionTimeline,
    DateRange,
    Maneuver,
    RiskFactor,
    CelestialBody,
    VehicleType,
    TransferType,
    RiskLevel,
)

logger = logging.getLogger(__name__)


class ParsedMissionResponse(BaseModel):
    """Parsed and validated mission response from AI."""
    
    mission_data: Dict[str, Any]  # Raw mission data that can be used to create Mission
    validation_issues: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None


class AlternativeMissionResponse(BaseModel):
    """Parsed alternative mission suggestions."""
    
    is_feasible: bool
    issues: List[str]
    recommendations: List[str]
    alternatives: List[Dict[str, Any]]
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)


class MissionResponseParser:
    """Parser for AI-generated mission responses."""
    
    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for mission parameters."""
        return {
            "mass_limits": {"min": 1, "max": 500000},  # kg
            "fuel_capacity_limits": {"min": 0, "max": 400000},  # kg
            "thrust_limits": {"min": 0.001, "max": 10000000},  # N
            "specific_impulse_limits": {"min": 200, "max": 500},  # s
            "delta_v_limits": {"min": 0, "max": 50000},  # m/s
            "duration_limits": {"min": 1, "max": 3650},  # days
            "success_probability_limits": {"min": 0.0, "max": 1.0},
            "valid_bodies": ["Earth", "Moon", "Mars", "Venus", "Jupiter", "Saturn", "Asteroid Belt", "Deep Space"],
            "valid_transfer_types": ["hohmann", "bi-elliptic", "direct", "gravity_assist"],
            "valid_mission_types": ["exploration", "communication", "scientific", "commercial", "military"],
            "valid_difficulty_levels": ["beginner", "intermediate", "advanced", "expert"],
            "valid_risk_levels": ["low", "medium", "high"],
        }
    
    def parse_mission_response(
        self,
        response_data: Dict[str, Any],
        user_prompt: str,
        provider_metadata: Optional[Dict[str, Any]] = None
    ) -> ParsedMissionResponse:
        """
        Parse and validate a mission generation response.
        
        Args:
            response_data: Raw response data from AI provider
            user_prompt: Original user prompt for context
            provider_metadata: Optional metadata from the AI provider
            
        Returns:
            ParsedMissionResponse with validated mission data
            
        Raises:
            ValueError: If response cannot be parsed or is invalid
        """
        validation_issues = []
        
        try:
            # Extract and validate main sections
            mission_data = response_data.get("mission", {})
            spacecraft_data = response_data.get("spacecraft", {})
            trajectory_data = response_data.get("trajectory", {})
            phases_data = response_data.get("mission_phases", [])
            constraints_data = response_data.get("constraints", {})
            
            # Parse and validate each section
            parsed_mission = self._parse_mission_info(mission_data, validation_issues)
            parsed_spacecraft = self._parse_spacecraft_config(spacecraft_data, validation_issues)
            parsed_trajectory = self._parse_trajectory_plan(trajectory_data, validation_issues)
            parsed_timeline = self._parse_mission_timeline(phases_data, validation_issues)
            parsed_constraints = self._parse_constraints(constraints_data, validation_issues)
            
            # Combine into mission data structure
            mission_data_result = {
                "name": parsed_mission["name"],
                "description": parsed_mission["description"],
                "objectives": parsed_mission["objectives"],
                "spacecraft_config": parsed_spacecraft,
                "trajectory": parsed_trajectory,
                "timeline": parsed_timeline,
                "constraints": parsed_constraints,
                "difficulty_rating": self._map_difficulty_to_rating(parsed_mission.get("difficulty_level", "intermediate")),
            }
            
            # Calculate confidence score based on validation issues
            confidence_score = self._calculate_confidence_score(validation_issues, response_data)
            
            return ParsedMissionResponse(
                mission_data=mission_data_result,
                validation_issues=validation_issues,
                confidence_score=confidence_score,
                metadata={
                    "user_prompt": user_prompt,
                    "provider_metadata": provider_metadata,
                    "parsed_at": datetime.utcnow().isoformat(),
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to parse mission response: {e}")
            raise ValueError(f"Invalid mission response format: {e}")
    
    def parse_alternative_response(
        self,
        response_data: Dict[str, Any],
        original_request: str
    ) -> AlternativeMissionResponse:
        """
        Parse alternative mission suggestions response.
        
        Args:
            response_data: Raw response data from AI provider
            original_request: Original mission request
            
        Returns:
            AlternativeMissionResponse with parsed alternatives
        """
        try:
            feasibility = response_data.get("feasibility_analysis", {})
            alternatives = response_data.get("alternatives", [])
            
            return AlternativeMissionResponse(
                is_feasible=feasibility.get("is_feasible", False),
                issues=feasibility.get("issues", []),
                recommendations=feasibility.get("recommendations", []),
                alternatives=alternatives,
                confidence_score=0.8  # Default confidence for alternatives
            )
            
        except Exception as e:
            logger.error(f"Failed to parse alternative response: {e}")
            raise ValueError(f"Invalid alternative response format: {e}")
    
    def _parse_mission_info(self, data: Dict[str, Any], issues: List[str]) -> Dict[str, Any]:
        """Parse and validate mission information."""
        result = {}
        
        # Required fields
        result["name"] = data.get("name", "Unnamed Mission")
        result["description"] = data.get("description", "")
        result["objectives"] = data.get("objectives", [])
        
        # Validate mission type
        mission_type = data.get("mission_type", "scientific")
        if mission_type not in self.validation_rules["valid_mission_types"]:
            issues.append(f"Invalid mission type: {mission_type}")
            mission_type = "scientific"  # Default fallback
        result["mission_type"] = mission_type
        
        # Validate difficulty level
        difficulty = data.get("difficulty_level", "intermediate")
        if difficulty not in self.validation_rules["valid_difficulty_levels"]:
            issues.append(f"Invalid difficulty level: {difficulty}")
            difficulty = "intermediate"  # Default fallback
        result["difficulty_level"] = difficulty
        
        return result
    
    def _parse_spacecraft_config(self, data: Dict[str, Any], issues: List[str]) -> Dict[str, Any]:
        """Parse and validate spacecraft configuration."""
        # Validate mass
        mass = self._validate_numeric_field(
            data.get("mass_kg", 1000),
            "mass_kg",
            self.validation_rules["mass_limits"],
            issues
        )
        
        # Validate fuel capacity
        fuel_capacity = self._validate_numeric_field(
            data.get("fuel_capacity_kg", 500),
            "fuel_capacity_kg",
            self.validation_rules["fuel_capacity_limits"],
            issues
        )
        
        # Validate thrust
        thrust = self._validate_numeric_field(
            data.get("thrust_n", 1000),
            "thrust_n",
            self.validation_rules["thrust_limits"],
            issues
        )
        
        # Validate specific impulse
        specific_impulse = self._validate_numeric_field(
            data.get("specific_impulse_s", 300),
            "specific_impulse_s",
            self.validation_rules["specific_impulse_limits"],
            issues
        )
        
        # Validate payload mass
        payload_mass = self._validate_numeric_field(
            data.get("payload_mass_kg", 100),
            "payload_mass_kg",
            {"min": 0, "max": mass * 0.5},  # Payload can't exceed 50% of total mass
            issues
        )
        
        # Cross-validation: fuel + payload shouldn't exceed total mass
        if fuel_capacity + payload_mass > mass * 0.9:  # Allow 10% for structure
            issues.append("Fuel and payload mass exceed reasonable spacecraft mass budget")
        
        # Map vehicle type to enum
        vehicle_type_str = data.get("vehicle_type", "probe").lower().replace(" ", "_")
        vehicle_type = self._map_vehicle_type(vehicle_type_str, issues)
        
        return {
            "vehicle_type": vehicle_type,
            "name": data.get("vehicle_type", "Generic Spacecraft"),
            "mass_kg": mass,
            "fuel_capacity_kg": fuel_capacity,
            "thrust_n": thrust,
            "specific_impulse_s": specific_impulse,
            "payload_mass_kg": payload_mass,
        }
    
    def _parse_trajectory_plan(self, data: Dict[str, Any], issues: List[str]) -> Dict[str, Any]:
        """Parse and validate trajectory plan."""
        # Map and validate celestial bodies
        departure_body = self._map_celestial_body(data.get("departure_body", "Earth"), issues)
        target_body = self._map_celestial_body(data.get("target_body", "Moon"), issues)
        
        # Map and validate transfer type
        transfer_type = self._map_transfer_type(data.get("transfer_type", "hohmann"), issues)
        
        # Parse dates
        launch_start = self._parse_date(data.get("launch_window_start"), issues)
        launch_end = self._parse_date(data.get("launch_window_end"), issues)
        
        # Validate duration
        duration = self._validate_numeric_field(
            data.get("estimated_duration_days", 30),
            "estimated_duration_days",
            self.validation_rules["duration_limits"],
            issues
        )
        
        # Validate delta-v
        delta_v = self._validate_numeric_field(
            data.get("total_delta_v_ms", 3000),
            "total_delta_v_ms",
            self.validation_rules["delta_v_limits"],
            issues
        )
        
        return {
            "launch_window": {
                "start": datetime.combine(launch_start, datetime.min.time()),
                "end": datetime.combine(launch_end, datetime.min.time()),
            },
            "departure_body": departure_body,
            "target_body": target_body,
            "transfer_type": transfer_type,
            "maneuvers": [],  # Will be populated by simulation
            "total_delta_v": delta_v,
            "flight_time_days": duration,
        }
    
    def _parse_mission_timeline(self, phases_data: List[Dict[str, Any]], issues: List[str]) -> Dict[str, Any]:
        """Parse and validate mission timeline from phases data."""
        # Create basic timeline structure
        launch_date = datetime.now() + timedelta(days=30)  # Default launch in 30 days
        
        major_milestones = []
        mission_phases = []
        
        for i, phase_data in enumerate(phases_data):
            try:
                duration = self._validate_numeric_field(
                    phase_data.get("duration_days", 1),
                    f"phase_{i}_duration_days",
                    {"min": 0, "max": 365},
                    issues
                )
                
                # Create milestone
                milestone = {
                    "name": phase_data.get("name", f"Phase {i+1}"),
                    "date": launch_date + timedelta(days=sum(p.get("duration_days", 0) for p in phases_data[:i])),
                    "description": phase_data.get("description", ""),
                }
                major_milestones.append(milestone)
                
                # Create phase
                phase = {
                    "name": phase_data.get("name", f"Phase {i+1}"),
                    "description": phase_data.get("description", ""),
                    "duration_days": duration,
                    "start_day": sum(p.get("duration_days", 0) for p in phases_data[:i]),
                }
                mission_phases.append(phase)
                
            except Exception as e:
                issues.append(f"Invalid phase {i}: {e}")
        
        return {
            "launch_date": launch_date,
            "major_milestones": major_milestones,
            "mission_phases": mission_phases,
        }
    
    def _parse_constraints(self, data: Dict[str, Any], issues: List[str]) -> Dict[str, Any]:
        """Parse and validate mission constraints."""
        max_duration = self._validate_numeric_field(
            data.get("max_mission_duration_days", 365),
            "max_mission_duration_days",
            self.validation_rules["duration_limits"],
            issues
        )
        
        budget = self._validate_numeric_field(
            data.get("budget_constraint_usd", 100000000),
            "budget_constraint_usd",
            {"min": 1000000, "max": 10000000000},
            issues
        )
        
        return {
            "max_duration_days": max_duration,
            "max_delta_v_ms": 15000,  # Default reasonable limit
            "max_mass_kg": 10000,     # Default reasonable limit
            "min_success_probability": 0.8,
            "max_cost_usd": budget,
        }
    
    def _map_difficulty_to_rating(self, difficulty_level: str) -> int:
        """Map difficulty level string to numeric rating."""
        mapping = {
            "beginner": 1,
            "intermediate": 2,
            "advanced": 3,
            "expert": 4,
        }
        return mapping.get(difficulty_level.lower(), 2)
    
    def _map_vehicle_type(self, vehicle_type_str: str, issues: List[str]) -> VehicleType:
        """Map vehicle type string to enum."""
        # Try to match common vehicle type patterns
        vehicle_type_str = vehicle_type_str.lower().replace(" ", "_")
        
        mapping = {
            "small_satellite": VehicleType.SMALL_SAT,
            "small_sat": VehicleType.SMALL_SAT,
            "cubesat": VehicleType.CUBESAT,
            "medium_satellite": VehicleType.MEDIUM_SAT,
            "medium_sat": VehicleType.MEDIUM_SAT,
            "large_satellite": VehicleType.LARGE_SAT,
            "large_sat": VehicleType.LARGE_SAT,
            "probe": VehicleType.PROBE,
            "deep_space_probe": VehicleType.PROBE,
            "lander": VehicleType.LANDER,
            "rover": VehicleType.ROVER,
            "crewed": VehicleType.CREWED,
        }
        
        if vehicle_type_str in mapping:
            return mapping[vehicle_type_str]
        
        # Default fallback
        issues.append(f"Unknown vehicle type: {vehicle_type_str}, using probe")
        return VehicleType.PROBE
    
    def _map_celestial_body(self, body_str: str, issues: List[str]) -> CelestialBody:
        """Map celestial body string to enum."""
        body_str = body_str.lower().replace(" ", "_")
        
        mapping = {
            "earth": CelestialBody.EARTH,
            "moon": CelestialBody.MOON,
            "mars": CelestialBody.MARS,
            "venus": CelestialBody.VENUS,
            "jupiter": CelestialBody.JUPITER,
            "saturn": CelestialBody.SATURN,
            "asteroid_belt": CelestialBody.ASTEROID_BELT,
        }
        
        if body_str in mapping:
            return mapping[body_str]
        
        # Default fallback
        issues.append(f"Unknown celestial body: {body_str}, using Earth")
        return CelestialBody.EARTH
    
    def _map_transfer_type(self, transfer_str: str, issues: List[str]) -> TransferType:
        """Map transfer type string to enum."""
        transfer_str = transfer_str.lower().replace("-", "_")
        
        mapping = {
            "hohmann": TransferType.HOHMANN,
            "bi_elliptic": TransferType.BI_ELLIPTIC,
            "direct": TransferType.DIRECT,
            "gravity_assist": TransferType.GRAVITY_ASSIST,
        }
        
        if transfer_str in mapping:
            return mapping[transfer_str]
        
        # Default fallback
        issues.append(f"Unknown transfer type: {transfer_str}, using Hohmann")
        return TransferType.HOHMANN
    
    def _validate_numeric_field(
        self,
        value: Union[int, float],
        field_name: str,
        limits: Dict[str, Union[int, float]],
        issues: List[str]
    ) -> float:
        """Validate a numeric field against limits."""
        try:
            numeric_value = float(value)
            
            if numeric_value < limits["min"]:
                issues.append(f"{field_name} below minimum: {numeric_value} < {limits['min']}")
                return limits["min"]
            
            if numeric_value > limits["max"]:
                issues.append(f"{field_name} above maximum: {numeric_value} > {limits['max']}")
                return limits["max"]
            
            return numeric_value
            
        except (ValueError, TypeError):
            issues.append(f"Invalid numeric value for {field_name}: {value}")
            return limits["min"]
    
    def _parse_date(self, date_str: Optional[str], issues: List[str]) -> date:
        """Parse a date string."""
        if not date_str:
            return date.today()
        
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            issues.append(f"Invalid date format: {date_str}")
            return date.today()
    
    def _calculate_confidence_score(
        self,
        validation_issues: List[str],
        response_data: Dict[str, Any]
    ) -> float:
        """Calculate confidence score based on validation issues and response quality."""
        base_score = 1.0
        
        # Deduct points for validation issues
        issue_penalty = len(validation_issues) * 0.1
        base_score -= issue_penalty
        
        # Bonus for completeness
        required_sections = ["mission", "spacecraft", "trajectory", "mission_phases", "constraints", "success_metrics"]
        completeness = sum(1 for section in required_sections if section in response_data) / len(required_sections)
        base_score *= completeness
        
        # Ensure score is within valid range
        return max(0.1, min(1.0, base_score))