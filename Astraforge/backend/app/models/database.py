"""
SQLAlchemy database models for AstraForge space mission simulator.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, String, Text, JSON,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Mission(Base):
    """Mission database model."""
    __tablename__ = "missions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Basic mission information
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    objectives = Column(JSON, nullable=False)  # List of objectives
    
    # Mission specification (stored as JSON)
    spacecraft_config = Column(JSON, nullable=False)
    trajectory = Column(JSON, nullable=False)
    timeline = Column(JSON, nullable=False)
    constraints = Column(JSON, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    user_id = Column(String(100), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    difficulty_rating = Column(Integer, default=1, nullable=False)
    
    # Relationships
    simulation_results = relationship("SimulationResult", back_populates="mission", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_missions_user_id', 'user_id'),
        Index('idx_missions_created_at', 'created_at'),
        Index('idx_missions_is_public', 'is_public'),
        Index('idx_missions_difficulty', 'difficulty_rating'),
    )


class SimulationResult(Base):
    """Simulation result database model."""
    __tablename__ = "simulation_results"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to mission
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"), nullable=False)
    
    # Simulation identifier
    simulation_id = Column(UUID(as_uuid=True), default=uuid4, nullable=False)
    
    # Core results
    success_probability = Column(Float, nullable=False)
    total_duration_days = Column(Float, nullable=False)
    fuel_consumption_kg = Column(Float, nullable=False)
    cost_estimate_usd = Column(Float, nullable=False)
    
    # Detailed results (stored as JSON)
    risk_factors = Column(JSON, nullable=False, default=list)
    performance_metrics = Column(JSON, nullable=False, default=dict)
    trajectory_data = Column(JSON, nullable=True)
    fuel_usage_timeline = Column(JSON, nullable=True)
    system_performance = Column(JSON, nullable=True)
    
    # Metadata
    simulation_timestamp = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relationships
    mission = relationship("Mission", back_populates="simulation_results")
    
    # Indexes
    __table_args__ = (
        Index('idx_simulation_results_mission_id', 'mission_id'),
        Index('idx_simulation_results_timestamp', 'simulation_timestamp'),
        Index('idx_simulation_results_success_prob', 'success_probability'),
    )


class VehiclePreset(Base):
    """Vehicle configuration preset database model."""
    __tablename__ = "vehicle_presets"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Preset information
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    vehicle_type = Column(String(50), nullable=False)
    
    # Configuration (stored as JSON)
    configuration = Column(JSON, nullable=False)
    
    # Metadata
    is_public = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    created_by = Column(String(100), nullable=True)
    
    # Performance characteristics for quick filtering
    mass_kg = Column(Float, nullable=False)
    thrust_n = Column(Float, nullable=False)
    specific_impulse_s = Column(Float, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_vehicle_presets_type', 'vehicle_type'),
        Index('idx_vehicle_presets_public', 'is_public'),
        Index('idx_vehicle_presets_mass', 'mass_kg'),
        Index('idx_vehicle_presets_thrust', 'thrust_n'),
    )


class OptimizationJob(Base):
    """Optimization job tracking database model."""
    __tablename__ = "optimization_jobs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to mission
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"), nullable=False)
    
    # Job information
    job_type = Column(String(50), nullable=False)  # 'genetic_algorithm', 'gradient_descent', etc.
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'running', 'completed', 'failed'
    
    # Optimization parameters (stored as JSON)
    parameters = Column(JSON, nullable=False)
    constraints = Column(JSON, nullable=False, default=dict)
    objectives = Column(JSON, nullable=False, default=list)
    
    # Results (stored as JSON)
    results = Column(JSON, nullable=True)
    pareto_front = Column(JSON, nullable=True)
    best_solution = Column(JSON, nullable=True)
    
    # Progress tracking
    progress_percent = Column(Float, default=0.0, nullable=False)
    current_generation = Column(Integer, default=0, nullable=True)
    total_generations = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    mission = relationship("Mission")
    
    # Indexes
    __table_args__ = (
        Index('idx_optimization_jobs_mission_id', 'mission_id'),
        Index('idx_optimization_jobs_status', 'status'),
        Index('idx_optimization_jobs_created_at', 'created_at'),
    )


class UserSession(Base):
    """User session tracking for anonymous and authenticated users."""
    __tablename__ = "user_sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Session information
    session_token = Column(String(255), nullable=False, unique=True)
    user_id = Column(String(100), nullable=True)  # Null for anonymous sessions
    email = Column(String(255), nullable=True)
    
    # Session metadata
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    last_accessed = Column(DateTime, default=datetime.now, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # User preferences (stored as JSON)
    preferences = Column(JSON, nullable=False, default=dict)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_sessions_token', 'session_token'),
        Index('idx_user_sessions_user_id', 'user_id'),
        Index('idx_user_sessions_expires_at', 'expires_at'),
        Index('idx_user_sessions_active', 'is_active'),
    )


# Export all models
__all__ = [
    'Base',
    'Mission',
    'SimulationResult',
    'VehiclePreset',
    'OptimizationJob',
    'UserSession'
]