"""
Pydantic schemas for vehicle preset API endpoints.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.mission import SpacecraftConfig, VehicleType
from app.models.database import VehiclePreset


class VehiclePresetCreate(BaseModel):
    """Schema for creating a vehicle preset."""
    name: str = Field(..., min_length=1, max_length=100, description="Preset name")
    description: Optional[str] = Field(None, max_length=1000, description="Preset description")
    spacecraft_config: SpacecraftConfig = Field(..., description="Spacecraft configuration")
    is_public: bool = Field(default=True, description="Whether preset is publicly available")
    created_by: Optional[str] = Field(None, max_length=100, description="Creator identifier")


class VehiclePresetUpdate(BaseModel):
    """Schema for updating a vehicle preset."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Preset name")
    description: Optional[str] = Field(None, max_length=1000, description="Preset description")
    spacecraft_config: Optional[SpacecraftConfig] = Field(None, description="Spacecraft configuration")
    is_public: Optional[bool] = Field(None, description="Whether preset is publicly available")


class VehiclePresetResponse(BaseModel):
    """Schema for vehicle preset response."""
    id: UUID = Field(..., description="Preset unique identifier")
    name: str = Field(..., description="Preset name")
    description: Optional[str] = Field(None, description="Preset description")
    vehicle_type: VehicleType = Field(..., description="Vehicle type")
    spacecraft_config: SpacecraftConfig = Field(..., description="Spacecraft configuration")
    is_public: bool = Field(..., description="Whether preset is publicly available")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator identifier")
    
    # Performance characteristics for quick reference
    mass_kg: float = Field(..., description="Spacecraft mass in kg")
    thrust_n: float = Field(..., description="Maximum thrust in Newtons")
    specific_impulse_s: float = Field(..., description="Specific impulse in seconds")
    
    @classmethod
    def from_db_model(cls, preset: VehiclePreset) -> "VehiclePresetResponse":
        """Create response model from database model."""
        return cls(
            id=preset.id,
            name=preset.name,
            description=preset.description,
            vehicle_type=VehicleType(preset.vehicle_type),
            spacecraft_config=SpacecraftConfig(**preset.configuration),
            is_public=preset.is_public,
            created_at=preset.created_at,
            updated_at=preset.updated_at,
            created_by=preset.created_by,
            mass_kg=preset.mass_kg,
            thrust_n=preset.thrust_n,
            specific_impulse_s=preset.specific_impulse_s
        )


class VehiclePresetListResponse(BaseModel):
    """Schema for vehicle preset list response."""
    presets: List[VehiclePresetResponse] = Field(..., description="List of vehicle presets")
    total: int = Field(..., description="Total number of presets returned")
    limit: int = Field(..., description="Maximum number of presets requested")
    offset: int = Field(..., description="Number of presets skipped")


class VehiclePresetSummary(BaseModel):
    """Schema for vehicle preset summary (lightweight)."""
    id: UUID = Field(..., description="Preset unique identifier")
    name: str = Field(..., description="Preset name")
    vehicle_type: VehicleType = Field(..., description="Vehicle type")
    mass_kg: float = Field(..., description="Spacecraft mass in kg")
    thrust_n: float = Field(..., description="Maximum thrust in Newtons")
    is_public: bool = Field(..., description="Whether preset is publicly available")
    
    @classmethod
    def from_db_model(cls, preset: VehiclePreset) -> "VehiclePresetSummary":
        """Create summary model from database model."""
        return cls(
            id=preset.id,
            name=preset.name,
            vehicle_type=VehicleType(preset.vehicle_type),
            mass_kg=preset.mass_kg,
            thrust_n=preset.thrust_n,
            is_public=preset.is_public
        )


class VehicleTypeStats(BaseModel):
    """Schema for vehicle type statistics."""
    vehicle_type: VehicleType = Field(..., description="Vehicle type")
    count: int = Field(..., description="Number of presets of this type")
    avg_mass_kg: float = Field(..., description="Average mass in kg")
    avg_thrust_n: float = Field(..., description="Average thrust in Newtons")
    avg_specific_impulse_s: float = Field(..., description="Average specific impulse in seconds")


class VehiclePresetStatsResponse(BaseModel):
    """Schema for vehicle preset statistics response."""
    total_presets: int = Field(..., description="Total number of presets")
    public_presets: int = Field(..., description="Number of public presets")
    private_presets: int = Field(..., description="Number of private presets")
    vehicle_type_stats: List[VehicleTypeStats] = Field(..., description="Statistics by vehicle type")