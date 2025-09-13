"""
Vehicle preset service for managing spacecraft configurations.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.database import VehiclePreset
from app.models.mission import SpacecraftConfig, VehicleType


class VehiclePresetService:
    """Service for managing vehicle presets."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_preset(
        self,
        name: str,
        description: str,
        spacecraft_config: SpacecraftConfig,
        is_public: bool = True,
        created_by: Optional[str] = None
    ) -> VehiclePreset:
        """Create a new vehicle preset."""
        preset = VehiclePreset(
            name=name,
            description=description,
            vehicle_type=spacecraft_config.vehicle_type.value,
            configuration=spacecraft_config.model_dump(),
            is_public=is_public,
            created_by=created_by,
            mass_kg=spacecraft_config.mass_kg,
            thrust_n=spacecraft_config.thrust_n,
            specific_impulse_s=spacecraft_config.specific_impulse_s
        )
        
        self.db.add(preset)
        await self.db.commit()
        await self.db.refresh(preset)
        
        return preset
    
    async def get_preset_by_id(self, preset_id: UUID) -> Optional[VehiclePreset]:
        """Get a vehicle preset by ID."""
        result = await self.db.execute(
            select(VehiclePreset).where(VehiclePreset.id == preset_id)
        )
        return result.scalar_one_or_none()
    
    async def get_preset_by_name(self, name: str) -> Optional[VehiclePreset]:
        """Get a vehicle preset by name."""
        result = await self.db.execute(
            select(VehiclePreset).where(VehiclePreset.name == name)
        )
        return result.scalar_one_or_none()
    
    async def list_presets(
        self,
        vehicle_type: Optional[VehicleType] = None,
        is_public: Optional[bool] = None,
        created_by: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[VehiclePreset]:
        """List vehicle presets with optional filtering."""
        query = select(VehiclePreset)
        
        conditions = []
        if vehicle_type:
            conditions.append(VehiclePreset.vehicle_type == vehicle_type.value)
        if is_public is not None:
            conditions.append(VehiclePreset.is_public == is_public)
        if created_by:
            conditions.append(VehiclePreset.created_by == created_by)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.offset(offset).limit(limit).order_by(VehiclePreset.name)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_preset(
        self,
        preset_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        spacecraft_config: Optional[SpacecraftConfig] = None,
        is_public: Optional[bool] = None
    ) -> Optional[VehiclePreset]:
        """Update a vehicle preset."""
        preset = await self.get_preset_by_id(preset_id)
        if not preset:
            return None
        
        if name is not None:
            preset.name = name
        if description is not None:
            preset.description = description
        if spacecraft_config is not None:
            preset.vehicle_type = spacecraft_config.vehicle_type.value
            preset.configuration = spacecraft_config.model_dump()
            preset.mass_kg = spacecraft_config.mass_kg
            preset.thrust_n = spacecraft_config.thrust_n
            preset.specific_impulse_s = spacecraft_config.specific_impulse_s
        if is_public is not None:
            preset.is_public = is_public
        
        await self.db.commit()
        await self.db.refresh(preset)
        
        return preset
    
    async def delete_preset(self, preset_id: UUID) -> bool:
        """Delete a vehicle preset."""
        preset = await self.get_preset_by_id(preset_id)
        if not preset:
            return False
        
        await self.db.delete(preset)
        await self.db.commit()
        
        return True
    
    def get_spacecraft_config(self, preset: VehiclePreset) -> SpacecraftConfig:
        """Convert preset configuration to SpacecraftConfig model."""
        return SpacecraftConfig(**preset.configuration)


# Realistic spacecraft presets data
REALISTIC_VEHICLE_PRESETS = [
    {
        "name": "CubeSat 3U",
        "description": "Standard 3U CubeSat configuration for small payloads and technology demonstrations",
        "config": SpacecraftConfig(
            vehicle_type=VehicleType.CUBESAT,
            name="CubeSat 3U",
            mass_kg=4.0,
            fuel_capacity_kg=0.5,
            thrust_n=0.1,
            specific_impulse_s=220,
            payload_mass_kg=1.5,
            power_w=20
        )
    },
    {
        "name": "CubeSat 6U",
        "description": "Larger 6U CubeSat with enhanced capabilities for Earth observation",
        "config": SpacecraftConfig(
            vehicle_type=VehicleType.CUBESAT,
            name="CubeSat 6U",
            mass_kg=8.0,
            fuel_capacity_kg=1.0,
            thrust_n=0.2,
            specific_impulse_s=230,
            payload_mass_kg=3.0,
            power_w=40
        )
    },
    {
        "name": "SmallSat Standard",
        "description": "Standard small satellite for commercial and scientific missions",
        "config": SpacecraftConfig(
            vehicle_type=VehicleType.SMALL_SAT,
            name="SmallSat Standard",
            mass_kg=150.0,
            fuel_capacity_kg=30.0,
            thrust_n=5.0,
            specific_impulse_s=280,
            payload_mass_kg=50.0,
            power_w=500
        )
    },
    {
        "name": "Medium Satellite",
        "description": "Medium-class satellite for telecommunications and Earth observation",
        "config": SpacecraftConfig(
            vehicle_type=VehicleType.MEDIUM_SAT,
            name="Medium Satellite",
            mass_kg=1500.0,
            fuel_capacity_kg=400.0,
            thrust_n=50.0,
            specific_impulse_s=320,
            payload_mass_kg=600.0,
            power_w=3000
        )
    },
    {
        "name": "Large Geostationary Satellite",
        "description": "Large satellite for geostationary orbit telecommunications",
        "config": SpacecraftConfig(
            vehicle_type=VehicleType.LARGE_SAT,
            name="Large Geostationary Satellite",
            mass_kg=6000.0,
            fuel_capacity_kg=2000.0,
            thrust_n=400.0,
            specific_impulse_s=350,
            payload_mass_kg=2500.0,
            power_w=15000
        )
    },
    {
        "name": "Mars Reconnaissance Probe",
        "description": "Interplanetary probe designed for Mars reconnaissance missions",
        "config": SpacecraftConfig(
            vehicle_type=VehicleType.PROBE,
            name="Mars Reconnaissance Probe",
            mass_kg=2180.0,
            fuel_capacity_kg=800.0,
            thrust_n=90.0,
            specific_impulse_s=330,
            payload_mass_kg=400.0,
            power_w=2000
        )
    },
    {
        "name": "Lunar Lander",
        "description": "Lunar surface lander with descent and landing capabilities",
        "config": SpacecraftConfig(
            vehicle_type=VehicleType.LANDER,
            name="Lunar Lander",
            mass_kg=3500.0,
            fuel_capacity_kg=2200.0,
            thrust_n=15000.0,
            specific_impulse_s=311,
            payload_mass_kg=800.0,
            power_w=1500
        )
    },
    {
        "name": "Mars Rover",
        "description": "Mars surface rover for exploration and sample collection",
        "config": SpacecraftConfig(
            vehicle_type=VehicleType.ROVER,
            name="Mars Rover",
            mass_kg=899.0,
            fuel_capacity_kg=0.0,  # Nuclear powered, no chemical fuel
            thrust_n=0.0,  # Surface mobility, no propulsion
            specific_impulse_s=0.0,
            payload_mass_kg=65.0,
            power_w=110
        )
    },
    {
        "name": "Crew Dragon Capsule",
        "description": "Crewed spacecraft for low Earth orbit and ISS missions",
        "config": SpacecraftConfig(
            vehicle_type=VehicleType.CREWED,
            name="Crew Dragon Capsule",
            mass_kg=12055.0,
            fuel_capacity_kg=1388.0,
            thrust_n=7400.0,
            specific_impulse_s=300,
            payload_mass_kg=6000.0,
            power_w=4000
        )
    },
    {
        "name": "Deep Space Probe",
        "description": "Long-duration probe for outer solar system exploration",
        "config": SpacecraftConfig(
            vehicle_type=VehicleType.PROBE,
            name="Deep Space Probe",
            mass_kg=5712.0,
            fuel_capacity_kg=3132.0,
            thrust_n=890.0,
            specific_impulse_s=325,
            payload_mass_kg=1200.0,
            power_w=470
        )
    }
]


async def seed_vehicle_presets(db_session: AsyncSession) -> None:
    """Seed the database with realistic vehicle presets."""
    service = VehiclePresetService(db_session)
    
    for preset_data in REALISTIC_VEHICLE_PRESETS:
        # Check if preset already exists
        existing = await service.get_preset_by_name(preset_data["name"])
        if existing:
            continue
        
        await service.create_preset(
            name=preset_data["name"],
            description=preset_data["description"],
            spacecraft_config=preset_data["config"],
            is_public=True,
            created_by="system"
        )


def validate_spacecraft_config(config_data: Dict[str, Any]) -> List[str]:
    """Validate spacecraft configuration parameters."""
    errors = []
    
    try:
        # Try to create SpacecraftConfig to validate
        SpacecraftConfig(**config_data)
    except Exception as e:
        errors.append(f"Configuration validation failed: {str(e)}")
    
    # Additional custom validations
    mass_kg = config_data.get("mass_kg", 0)
    fuel_capacity_kg = config_data.get("fuel_capacity_kg", 0)
    thrust_n = config_data.get("thrust_n", 0)
    specific_impulse_s = config_data.get("specific_impulse_s", 0)
    payload_mass_kg = config_data.get("payload_mass_kg", 0)
    
    # Physical constraints
    if fuel_capacity_kg > mass_kg * 0.95:
        errors.append("Fuel capacity cannot exceed 95% of total mass")
    
    if payload_mass_kg > mass_kg * 0.8:
        errors.append("Payload mass cannot exceed 80% of total mass")
    
    if thrust_n > 0 and specific_impulse_s == 0:
        errors.append("Spacecraft with thrust must have specific impulse > 0")
    
    # Vehicle type specific validations
    vehicle_type = config_data.get("vehicle_type")
    if vehicle_type == VehicleType.CUBESAT.value and mass_kg > 50:
        errors.append("CubeSat mass should not exceed 50 kg")
    
    if vehicle_type == VehicleType.ROVER.value and thrust_n > 0:
        errors.append("Rovers should not have propulsive thrust")
    
    return errors