"""
Vehicle presets API endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.database import VehiclePreset
from app.models.mission import SpacecraftConfig, VehicleType
from app.services.vehicle_presets import VehiclePresetService, validate_spacecraft_config
from app.schemas.vehicle_presets import (
    VehiclePresetCreate,
    VehiclePresetUpdate,
    VehiclePresetResponse,
    VehiclePresetListResponse
)

router = APIRouter(prefix="/vehicle-presets", tags=["vehicle-presets"])


@router.post("/", response_model=VehiclePresetResponse)
async def create_vehicle_preset(
    preset_data: VehiclePresetCreate,
    db: AsyncSession = Depends(get_db)
) -> VehiclePresetResponse:
    """Create a new vehicle preset."""
    service = VehiclePresetService(db)
    
    # Validate spacecraft configuration
    config_errors = validate_spacecraft_config(preset_data.spacecraft_config.model_dump())
    if config_errors:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid spacecraft configuration: {'; '.join(config_errors)}"
        )
    
    # Check if preset name already exists
    existing = await service.get_preset_by_name(preset_data.name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle preset with name '{preset_data.name}' already exists"
        )
    
    preset = await service.create_preset(
        name=preset_data.name,
        description=preset_data.description,
        spacecraft_config=preset_data.spacecraft_config,
        is_public=preset_data.is_public,
        created_by=preset_data.created_by
    )
    
    return VehiclePresetResponse.from_db_model(preset)


@router.get("/", response_model=VehiclePresetListResponse)
async def list_vehicle_presets(
    vehicle_type: Optional[VehicleType] = Query(None, description="Filter by vehicle type"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of presets to return"),
    offset: int = Query(0, ge=0, description="Number of presets to skip"),
    db: AsyncSession = Depends(get_db)
) -> VehiclePresetListResponse:
    """List vehicle presets with optional filtering."""
    service = VehiclePresetService(db)
    
    presets = await service.list_presets(
        vehicle_type=vehicle_type,
        is_public=is_public,
        created_by=created_by,
        limit=limit,
        offset=offset
    )
    
    preset_responses = [VehiclePresetResponse.from_db_model(preset) for preset in presets]
    
    return VehiclePresetListResponse(
        presets=preset_responses,
        total=len(preset_responses),
        limit=limit,
        offset=offset
    )


@router.get("/{preset_id}", response_model=VehiclePresetResponse)
async def get_vehicle_preset(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> VehiclePresetResponse:
    """Get a vehicle preset by ID."""
    service = VehiclePresetService(db)
    
    preset = await service.get_preset_by_id(preset_id)
    if not preset:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle preset with ID {preset_id} not found"
        )
    
    return VehiclePresetResponse.from_db_model(preset)


@router.get("/by-name/{preset_name}", response_model=VehiclePresetResponse)
async def get_vehicle_preset_by_name(
    preset_name: str,
    db: AsyncSession = Depends(get_db)
) -> VehiclePresetResponse:
    """Get a vehicle preset by name."""
    service = VehiclePresetService(db)
    
    preset = await service.get_preset_by_name(preset_name)
    if not preset:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle preset with name '{preset_name}' not found"
        )
    
    return VehiclePresetResponse.from_db_model(preset)


@router.put("/{preset_id}", response_model=VehiclePresetResponse)
async def update_vehicle_preset(
    preset_id: UUID,
    preset_data: VehiclePresetUpdate,
    db: AsyncSession = Depends(get_db)
) -> VehiclePresetResponse:
    """Update a vehicle preset."""
    service = VehiclePresetService(db)
    
    # Check if preset exists
    existing = await service.get_preset_by_id(preset_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle preset with ID {preset_id} not found"
        )
    
    # Validate spacecraft configuration if provided
    if preset_data.spacecraft_config:
        config_errors = validate_spacecraft_config(preset_data.spacecraft_config.model_dump())
        if config_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid spacecraft configuration: {'; '.join(config_errors)}"
            )
    
    # Check if new name conflicts with existing preset
    if preset_data.name and preset_data.name != existing.name:
        name_conflict = await service.get_preset_by_name(preset_data.name)
        if name_conflict:
            raise HTTPException(
                status_code=400,
                detail=f"Vehicle preset with name '{preset_data.name}' already exists"
            )
    
    updated_preset = await service.update_preset(
        preset_id=preset_id,
        name=preset_data.name,
        description=preset_data.description,
        spacecraft_config=preset_data.spacecraft_config,
        is_public=preset_data.is_public
    )
    
    if not updated_preset:
        raise HTTPException(
            status_code=500,
            detail="Failed to update vehicle preset"
        )
    
    return VehiclePresetResponse.from_db_model(updated_preset)


@router.delete("/{preset_id}")
async def delete_vehicle_preset(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """Delete a vehicle preset."""
    service = VehiclePresetService(db)
    
    success = await service.delete_preset(preset_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle preset with ID {preset_id} not found"
        )
    
    return {"message": "Vehicle preset deleted successfully"}


@router.post("/seed")
async def seed_vehicle_presets(
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """Seed the database with realistic vehicle presets."""
    from app.services.vehicle_presets import seed_vehicle_presets
    
    await seed_vehicle_presets(db)
    
    return {"message": "Vehicle presets seeded successfully"}


@router.get("/{preset_id}/spacecraft-config", response_model=SpacecraftConfig)
async def get_spacecraft_config(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> SpacecraftConfig:
    """Get the spacecraft configuration from a vehicle preset."""
    service = VehiclePresetService(db)
    
    preset = await service.get_preset_by_id(preset_id)
    if not preset:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle preset with ID {preset_id} not found"
        )
    
    return service.get_spacecraft_config(preset)