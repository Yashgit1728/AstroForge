"""
Mission API schemas for request/response validation.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.mission import (
    Mission as MissionModel,
    SimulationResult as SimulationResultModel,
    SpacecraftConfig,
    TrajectoryPlan,
    MissionConstraints,
    MissionTimeline,
    TransferType,
    CelestialBody,
    VehicleType,
    RiskLevel
)


# Request schemas
class MissionCreateRequest(BaseModel):
    """Request schema for creating a new mission."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    objectives: List[str] = Field(..., min_length=1, max_length=10)
    spacecraft_config: SpacecraftConfig
    trajectory: TrajectoryPlan
    timeline: MissionTimeline
    constraints: MissionConstraints
    is_public: bool = Field(default=False)
    difficulty_rating: int = Field(default=1, ge=1, le=5)


class MissionUpdateRequest(BaseModel):
    """Request schema for updating an existing mission."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    objectives: Optional[List[str]] = Field(None, min_length=1, max_length=10)
    spacecraft_config: Optional[SpacecraftConfig] = None
    trajectory: Optional[TrajectoryPlan] = None
    timeline: Optional[MissionTimeline] = None
    constraints: Optional[MissionConstraints] = None
    is_public: Optional[bool] = None
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5)


class MissionGenerateRequest(BaseModel):
    """Request schema for AI-powered mission generation."""
    prompt: str = Field(..., min_length=10, max_length=1000)
    user_id: Optional[str] = Field(None, max_length=100)
    provider_preference: Optional[str] = Field(None, pattern="^(claude|openai|groq)$")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    include_alternatives: bool = Field(default=True)


class SimulationRequest(BaseModel):
    """Request schema for mission simulation."""
    mission_id: UUID
    simulation_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    include_detailed_results: bool = Field(default=True)


class OptimizationRequest(BaseModel):
    """Request schema for mission optimization."""
    mission_id: UUID
    optimization_type: str = Field(..., pattern="^(genetic_algorithm|gradient_descent)$")
    objectives: List[str] = Field(..., min_length=1, max_length=5)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)


# Response schemas
class MissionResponse(BaseModel):
    """Response schema for mission data."""
    id: UUID
    name: str
    description: str
    objectives: List[str]
    spacecraft_config: SpacecraftConfig
    trajectory: TrajectoryPlan
    timeline: MissionTimeline
    constraints: MissionConstraints
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str]
    is_public: bool
    difficulty_rating: int
    latest_simulation: Optional[SimulationResultModel] = None
    
    @classmethod
    def from_model(cls, mission: MissionModel) -> "MissionResponse":
        """Create response from mission model."""
        return cls(
            id=mission.id,
            name=mission.name,
            description=mission.description,
            objectives=mission.objectives,
            spacecraft_config=mission.spacecraft_config,
            trajectory=mission.trajectory,
            timeline=mission.timeline,
            constraints=mission.constraints,
            created_at=mission.created_at,
            updated_at=mission.updated_at,
            user_id=mission.user_id,
            is_public=mission.is_public,
            difficulty_rating=mission.difficulty_rating,
            latest_simulation=mission.latest_simulation
        )


class MissionSummaryResponse(BaseModel):
    """Response schema for mission summary (used in lists)."""
    id: UUID
    name: str
    description: str
    objectives: List[str]
    target_body: CelestialBody
    vehicle_type: VehicleType
    total_delta_v: float
    flight_time_days: float
    created_at: datetime
    user_id: Optional[str]
    is_public: bool
    difficulty_rating: int
    has_simulation_results: bool = False
    
    @classmethod
    def from_model(cls, mission: MissionModel) -> "MissionSummaryResponse":
        """Create summary response from mission model."""
        return cls(
            id=mission.id,
            name=mission.name,
            description=mission.description,
            objectives=mission.objectives,
            target_body=mission.trajectory.target_body,
            vehicle_type=mission.spacecraft_config.vehicle_type,
            total_delta_v=mission.trajectory.total_delta_v,
            flight_time_days=mission.trajectory.flight_time_days,
            created_at=mission.created_at,
            user_id=mission.user_id,
            is_public=mission.is_public,
            difficulty_rating=mission.difficulty_rating,
            has_simulation_results=mission.latest_simulation is not None
        )


class MissionListResponse(BaseModel):
    """Response schema for paginated mission lists."""
    missions: List[MissionSummaryResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class SimulationResponse(BaseModel):
    """Response schema for simulation results."""
    simulation_id: UUID
    mission_id: UUID
    success_probability: float
    total_duration_days: float
    fuel_consumption_kg: float
    cost_estimate_usd: float
    risk_factors: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    simulation_timestamp: datetime
    trajectory_data: Optional[Dict[str, Any]] = None
    fuel_usage_timeline: Optional[List[Dict[str, float]]] = None
    system_performance: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_model(cls, result: SimulationResultModel) -> "SimulationResponse":
        """Create response from simulation result model."""
        return cls(
            simulation_id=result.simulation_id,
            mission_id=result.mission_id,
            success_probability=result.success_probability,
            total_duration_days=result.total_duration_days,
            fuel_consumption_kg=result.fuel_consumption_kg,
            cost_estimate_usd=result.cost_estimate_usd,
            risk_factors=result.risk_factors,
            performance_metrics=result.performance_metrics,
            simulation_timestamp=result.simulation_timestamp,
            trajectory_data=result.trajectory_data,
            fuel_usage_timeline=result.fuel_usage_timeline,
            system_performance=result.system_performance
        )


class OptimizationResponse(BaseModel):
    """Response schema for optimization results."""
    job_id: UUID
    mission_id: UUID
    status: str
    progress_percent: float
    results: Optional[Dict[str, Any]] = None
    pareto_front: Optional[List[Dict[str, Any]]] = None
    best_solution: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class MissionGenerationResponse(BaseModel):
    """Response schema for AI-generated missions."""
    mission: MissionResponse
    alternatives: Optional[List[MissionSummaryResponse]] = None
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    retry_after: Optional[int] = None


# Export all schemas
__all__ = [
    'MissionCreateRequest',
    'MissionUpdateRequest', 
    'MissionGenerateRequest',
    'SimulationRequest',
    'OptimizationRequest',
    'MissionResponse',
    'MissionSummaryResponse',
    'MissionListResponse',
    'SimulationResponse',
    'OptimizationResponse',
    'MissionGenerationResponse',
    'ErrorResponse'
]