"""
Mission domain models using Pydantic v2 for validation and serialization.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, validator, field_validator
import numpy as np


class TransferType(str, Enum):
    """Types of orbital transfer maneuvers."""
    HOHMANN = "hohmann"
    BI_ELLIPTIC = "bi_elliptic"
    DIRECT = "direct"
    GRAVITY_ASSIST = "gravity_assist"


class CelestialBody(str, Enum):
    """Celestial bodies for mission planning."""
    EARTH = "earth"
    MOON = "moon"
    MARS = "mars"
    VENUS = "venus"
    JUPITER = "jupiter"
    SATURN = "saturn"
    ASTEROID_BELT = "asteroid_belt"


class VehicleType(str, Enum):
    """Spacecraft vehicle types."""
    SMALL_SAT = "small_sat"
    CUBESAT = "cubesat"
    MEDIUM_SAT = "medium_sat"
    LARGE_SAT = "large_sat"
    PROBE = "probe"
    LANDER = "lander"
    ROVER = "rover"
    CREWED = "crewed"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DateRange(BaseModel):
    """Date range for launch windows."""
    start: datetime
    end: datetime
    
    @field_validator('end')
    @classmethod
    def validate_end_after_start(cls, v, info):
        if 'start' in info.data and v <= info.data['start']:
            raise ValueError('End date must be after start date')
        return v


class Maneuver(BaseModel):
    """Orbital maneuver specification."""
    name: str = Field(..., min_length=1, max_length=100)
    delta_v_ms: float = Field(..., ge=0, le=15000, description="Delta-v in m/s")
    duration_s: float = Field(..., ge=0, le=86400, description="Burn duration in seconds")
    timestamp_days: float = Field(..., ge=0, description="Time from mission start in days")
    
    @field_validator('delta_v_ms')
    @classmethod
    def validate_delta_v(cls, v):
        if v > 12000:  # Typical upper limit for chemical propulsion
            raise ValueError('Delta-v exceeds typical chemical propulsion limits')
        return v


class RiskFactor(BaseModel):
    """Risk factor assessment."""
    category: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    probability: float = Field(..., ge=0.0, le=1.0, description="Risk probability (0-1)")
    impact: RiskLevel
    mitigation: Optional[str] = Field(None, max_length=500)


class SpacecraftConfig(BaseModel):
    """Spacecraft configuration and specifications."""
    vehicle_type: VehicleType
    name: str = Field(..., min_length=1, max_length=100)
    mass_kg: float = Field(..., gt=0, le=500000, description="Total spacecraft mass in kg")
    fuel_capacity_kg: float = Field(..., ge=0, le=400000, description="Fuel capacity in kg")
    thrust_n: float = Field(..., ge=0, le=1000000, description="Maximum thrust in Newtons")
    specific_impulse_s: float = Field(..., ge=0, le=500, description="Specific impulse in seconds")
    payload_mass_kg: float = Field(..., ge=0, description="Payload mass in kg")
    power_w: float = Field(default=1000, gt=0, le=100000, description="Power generation in Watts")
    
    @field_validator('payload_mass_kg')
    @classmethod
    def validate_payload_mass(cls, v, info):
        if 'mass_kg' in info.data and v >= info.data['mass_kg']:
            raise ValueError('Payload mass must be less than total spacecraft mass')
        return v
    
    @field_validator('fuel_capacity_kg')
    @classmethod
    def validate_fuel_capacity(cls, v, info):
        if 'mass_kg' in info.data and v >= info.data['mass_kg'] * 0.9:
            raise ValueError('Fuel capacity cannot exceed 90% of total mass')
        return v
    
    @property
    def mass_ratio(self) -> float:
        """Calculate mass ratio (wet mass / dry mass)."""
        dry_mass = self.mass_kg - self.fuel_capacity_kg
        return self.mass_kg / dry_mass if dry_mass > 0 else 1.0
    
    @property
    def thrust_to_weight_ratio(self) -> float:
        """Calculate thrust-to-weight ratio at Earth surface."""
        earth_gravity = 9.81  # m/s²
        weight_n = self.mass_kg * earth_gravity
        return self.thrust_n / weight_n


class TrajectoryPlan(BaseModel):
    """Mission trajectory planning specification."""
    launch_window: DateRange
    departure_body: CelestialBody
    target_body: CelestialBody
    transfer_type: TransferType
    maneuvers: List[Maneuver] = Field(default_factory=list)
    total_delta_v: float = Field(..., ge=0, le=50000, description="Total mission delta-v in m/s")
    flight_time_days: float = Field(..., gt=0, le=3650, description="Total flight time in days")
    
    @field_validator('maneuvers')
    @classmethod
    def validate_maneuvers(cls, v):
        if len(v) > 20:  # Reasonable limit for mission complexity
            raise ValueError('Too many maneuvers (max 20)')
        
        # Check for chronological order
        timestamps = [m.timestamp_days for m in v]
        if timestamps != sorted(timestamps):
            raise ValueError('Maneuvers must be in chronological order')
        
        return v
    
    @field_validator('total_delta_v')
    @classmethod
    def validate_total_delta_v(cls, v, info):
        if 'maneuvers' in info.data:
            calculated_delta_v = sum(m.delta_v_ms for m in info.data['maneuvers'])
            if abs(v - calculated_delta_v) > 100:  # Allow 100 m/s tolerance
                raise ValueError('Total delta-v does not match sum of maneuvers')
        return v
    
    @field_validator('target_body')
    @classmethod
    def validate_different_bodies(cls, v, info):
        if 'departure_body' in info.data and v == info.data['departure_body']:
            raise ValueError('Target body must be different from departure body')
        return v


class MissionConstraints(BaseModel):
    """Mission constraints and limitations."""
    max_duration_days: float = Field(default=3650, gt=0, le=10950, description="Maximum mission duration")
    max_delta_v_ms: float = Field(default=15000, gt=0, le=50000, description="Maximum delta-v budget")
    max_mass_kg: float = Field(default=10000, gt=0, le=500000, description="Maximum spacecraft mass")
    min_success_probability: float = Field(default=0.8, ge=0.0, le=1.0, description="Minimum success probability")
    max_cost_usd: Optional[float] = Field(default=None, gt=0, description="Maximum mission cost")
    launch_vehicle_constraints: Dict[str, Any] = Field(default_factory=dict)


class MissionTimeline(BaseModel):
    """Mission timeline with key milestones."""
    launch_date: datetime
    major_milestones: List[Dict[str, Any]] = Field(default_factory=list)
    mission_phases: List[Dict[str, Any]] = Field(default_factory=list)
    
    @field_validator('major_milestones')
    @classmethod
    def validate_milestones(cls, v):
        required_fields = ['name', 'date', 'description']
        for milestone in v:
            if not all(field in milestone for field in required_fields):
                raise ValueError(f'Milestone must contain fields: {required_fields}')
        return v


class SimulationResult(BaseModel):
    """Results from mission simulation."""
    mission_id: UUID
    simulation_id: UUID = Field(default_factory=uuid4)
    success_probability: float = Field(..., ge=0.0, le=1.0, description="Mission success probability")
    total_duration_days: float = Field(..., gt=0, description="Actual mission duration")
    fuel_consumption_kg: float = Field(..., ge=0, description="Total fuel consumed")
    cost_estimate_usd: float = Field(..., gt=0, description="Estimated mission cost")
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    simulation_timestamp: datetime = Field(default_factory=lambda: datetime.now())
    
    # Detailed results
    trajectory_data: Optional[Dict[str, Any]] = Field(default=None, description="Detailed trajectory data")
    fuel_usage_timeline: Optional[List[Dict[str, float]]] = Field(default=None)
    system_performance: Optional[Dict[str, Any]] = Field(default=None)
    
    @field_validator('performance_metrics')
    @classmethod
    def validate_performance_metrics(cls, v):
        # Ensure all metric values are finite
        for key, value in v.items():
            if not np.isfinite(value):
                raise ValueError(f'Performance metric {key} must be finite')
        return v


class Mission(BaseModel):
    """Complete mission specification."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    objectives: List[str] = Field(..., min_length=1, max_length=10)
    
    # Core mission components
    spacecraft_config: SpacecraftConfig
    trajectory: TrajectoryPlan
    timeline: MissionTimeline
    constraints: MissionConstraints
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    user_id: Optional[str] = Field(default=None, max_length=100)
    is_public: bool = Field(default=False)
    difficulty_rating: int = Field(default=1, ge=1, le=5, description="Mission difficulty (1-5)")
    
    # Optional simulation results
    latest_simulation: Optional[SimulationResult] = Field(default=None)
    
    @field_validator('objectives')
    @classmethod
    def validate_objectives(cls, v):
        for objective in v:
            if len(objective.strip()) < 5:
                raise ValueError('Each objective must be at least 5 characters long')
        return v
    
    @field_validator('updated_at')
    @classmethod
    def validate_updated_at(cls, v, info):
        if 'created_at' in info.data and v < info.data['created_at']:
            raise ValueError('Updated timestamp cannot be before created timestamp')
        return v
    
    def calculate_mission_complexity(self) -> float:
        """Calculate mission complexity score based on various factors."""
        complexity = 0.0
        
        # Trajectory complexity
        complexity += len(self.trajectory.maneuvers) * 0.1
        complexity += self.trajectory.total_delta_v / 1000 * 0.2
        
        # Distance factor
        distance_factors = {
            CelestialBody.MOON: 1.0,
            CelestialBody.MARS: 2.0,
            CelestialBody.VENUS: 1.5,
            CelestialBody.JUPITER: 3.0,
            CelestialBody.SATURN: 4.0,
            CelestialBody.ASTEROID_BELT: 2.5
        }
        complexity += distance_factors.get(self.trajectory.target_body, 1.0)
        
        # Duration factor
        complexity += self.trajectory.flight_time_days / 365 * 0.5
        
        return min(complexity, 5.0)  # Cap at 5.0
    
    def validate_mission_feasibility(self) -> List[str]:
        """Validate mission feasibility and return list of issues."""
        issues = []
        
        # Check if spacecraft has enough delta-v capability
        theoretical_delta_v = self.spacecraft_config.specific_impulse_s * 9.81 * np.log(self.spacecraft_config.mass_ratio)
        if theoretical_delta_v < self.trajectory.total_delta_v:
            issues.append(f"Insufficient delta-v capability: need {self.trajectory.total_delta_v:.0f} m/s, have {theoretical_delta_v:.0f} m/s")
        
        # Check thrust-to-weight ratio for certain mission types
        if self.spacecraft_config.thrust_to_weight_ratio < 0.1:
            issues.append("Very low thrust-to-weight ratio may cause mission timeline issues")
        
        # Check mission duration vs constraints
        if self.trajectory.flight_time_days > self.constraints.max_duration_days:
            issues.append(f"Mission duration exceeds constraints: {self.trajectory.flight_time_days:.0f} > {self.constraints.max_duration_days:.0f} days")
        
        return issues


# Export all models
__all__ = [
    'Mission',
    'SpacecraftConfig', 
    'TrajectoryPlan',
    'SimulationResult',
    'MissionConstraints',
    'MissionTimeline',
    'Maneuver',
    'RiskFactor',
    'DateRange',
    'TransferType',
    'CelestialBody',
    'VehicleType',
    'RiskLevel'
]