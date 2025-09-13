"""
Mission domain models for AstraForge space mission simulator.
"""

from .mission import (
    Mission as MissionModel,
    SpacecraftConfig,
    TrajectoryPlan,
    SimulationResult as SimulationResultModel,
    MissionConstraints,
    MissionTimeline,
    Maneuver,
    RiskFactor,
    DateRange,
    TransferType,
    CelestialBody,
    VehicleType,
    RiskLevel
)

from .database import (
    Base,
    Mission,
    SimulationResult,
    VehiclePreset,
    OptimizationJob,
    UserSession
)

__all__ = [
    # Pydantic models
    'MissionModel',
    'SpacecraftConfig', 
    'TrajectoryPlan',
    'SimulationResultModel',
    'MissionConstraints',
    'MissionTimeline',
    'Maneuver',
    'RiskFactor',
    'DateRange',
    'TransferType',
    'CelestialBody',
    'VehicleType',
    'RiskLevel',
    # Database models
    'Base',
    'Mission',
    'SimulationResult',
    'VehiclePreset',
    'OptimizationJob',
    'UserSession'
]