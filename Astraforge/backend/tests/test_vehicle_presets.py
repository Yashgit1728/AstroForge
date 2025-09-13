"""
Tests for vehicle preset service.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import Base, VehiclePreset
from app.models.mission import SpacecraftConfig, VehicleType
from app.services.vehicle_presets import (
    VehiclePresetService, 
    seed_vehicle_presets, 
    validate_spacecraft_config,
    REALISTIC_VEHICLE_PRESETS
)


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def preset_service(test_session):
    """Create vehicle preset service."""
    return VehiclePresetService(test_session)


@pytest.fixture
def sample_spacecraft_config():
    """Create sample spacecraft configuration."""
    return SpacecraftConfig(
        vehicle_type=VehicleType.MEDIUM_SAT,
        name="Test Satellite",
        mass_kg=1000.0,
        fuel_capacity_kg=400.0,
        thrust_n=500.0,
        specific_impulse_s=300.0,
        payload_mass_kg=200.0,
        power_w=2000.0
    )


class TestVehiclePresetService:
    """Test VehiclePresetService functionality."""
    
    @pytest.mark.asyncio
    async def test_create_preset(self, preset_service: VehiclePresetService, sample_spacecraft_config):
        """Test creating a vehicle preset."""
        preset = await preset_service.create_preset(
            name="Test Preset",
            description="A test spacecraft configuration",
            spacecraft_config=sample_spacecraft_config,
            is_public=True,
            created_by="test_user"
        )
        
        assert preset.id is not None
        assert preset.name == "Test Preset"
        assert preset.description == "A test spacecraft configuration"
        assert preset.vehicle_type == VehicleType.MEDIUM_SAT.value
        assert preset.is_public is True
        assert preset.created_by == "test_user"
        assert preset.mass_kg == 1000.0
        assert preset.thrust_n == 500.0
        assert preset.specific_impulse_s == 300.0
    
    @pytest.mark.asyncio
    async def test_get_preset_by_id(self, preset_service: VehiclePresetService, sample_spacecraft_config):
        """Test getting a preset by ID."""
        # Create preset
        created_preset = await preset_service.create_preset(
            name="Test Preset",
            description="Test description",
            spacecraft_config=sample_spacecraft_config
        )
        
        # Get preset by ID
        retrieved_preset = await preset_service.get_preset_by_id(created_preset.id)
        
        assert retrieved_preset is not None
        assert retrieved_preset.id == created_preset.id
        assert retrieved_preset.name == "Test Preset"
    
    @pytest.mark.asyncio
    async def test_get_preset_by_name(self, preset_service: VehiclePresetService, sample_spacecraft_config):
        """Test getting a preset by name."""
        # Create preset
        await preset_service.create_preset(
            name="Unique Preset Name",
            description="Test description",
            spacecraft_config=sample_spacecraft_config
        )
        
        # Get preset by name
        retrieved_preset = await preset_service.get_preset_by_name("Unique Preset Name")
        
        assert retrieved_preset is not None
        assert retrieved_preset.name == "Unique Preset Name"
    
    @pytest.mark.asyncio
    async def test_list_presets(self, preset_service: VehiclePresetService, sample_spacecraft_config):
        """Test listing presets with filtering."""
        # Create multiple presets
        cubesat_config = SpacecraftConfig(
            vehicle_type=VehicleType.CUBESAT,
            name="CubeSat",
            mass_kg=4.0,
            fuel_capacity_kg=0.5,
            thrust_n=0.1,
            specific_impulse_s=220,
            payload_mass_kg=1.5
        )
        
        await preset_service.create_preset(
            name="Medium Sat Preset",
            description="Medium satellite",
            spacecraft_config=sample_spacecraft_config,
            is_public=True
        )
        
        await preset_service.create_preset(
            name="CubeSat Preset",
            description="Small CubeSat",
            spacecraft_config=cubesat_config,
            is_public=False
        )
        
        # Test listing all presets
        all_presets = await preset_service.list_presets()
        assert len(all_presets) == 2
        
        # Test filtering by vehicle type
        medium_presets = await preset_service.list_presets(vehicle_type=VehicleType.MEDIUM_SAT)
        assert len(medium_presets) == 1
        assert medium_presets[0].name == "Medium Sat Preset"
        
        # Test filtering by public status
        public_presets = await preset_service.list_presets(is_public=True)
        assert len(public_presets) == 1
        assert public_presets[0].name == "Medium Sat Preset"
    
    @pytest.mark.asyncio
    async def test_update_preset(self, preset_service: VehiclePresetService, sample_spacecraft_config):
        """Test updating a preset."""
        # Create preset
        preset = await preset_service.create_preset(
            name="Original Name",
            description="Original description",
            spacecraft_config=sample_spacecraft_config
        )
        
        # Update preset
        updated_config = SpacecraftConfig(
            vehicle_type=VehicleType.LARGE_SAT,
            name="Updated Satellite",
            mass_kg=2000.0,
            fuel_capacity_kg=800.0,
            thrust_n=1000.0,
            specific_impulse_s=350.0,
            payload_mass_kg=500.0
        )
        
        updated_preset = await preset_service.update_preset(
            preset_id=preset.id,
            name="Updated Name",
            description="Updated description",
            spacecraft_config=updated_config,
            is_public=False
        )
        
        assert updated_preset is not None
        assert updated_preset.name == "Updated Name"
        assert updated_preset.description == "Updated description"
        assert updated_preset.vehicle_type == VehicleType.LARGE_SAT.value
        assert updated_preset.is_public is False
        assert updated_preset.mass_kg == 2000.0
    
    @pytest.mark.asyncio
    async def test_delete_preset(self, preset_service: VehiclePresetService, sample_spacecraft_config):
        """Test deleting a preset."""
        # Create preset
        preset = await preset_service.create_preset(
            name="To Delete",
            description="Will be deleted",
            spacecraft_config=sample_spacecraft_config
        )
        
        # Delete preset
        success = await preset_service.delete_preset(preset.id)
        assert success is True
        
        # Verify deletion
        deleted_preset = await preset_service.get_preset_by_id(preset.id)
        assert deleted_preset is None
    
    @pytest.mark.asyncio
    async def test_get_spacecraft_config(self, preset_service: VehiclePresetService, sample_spacecraft_config):
        """Test converting preset to SpacecraftConfig."""
        # Create preset
        preset = await preset_service.create_preset(
            name="Config Test",
            description="Test configuration conversion",
            spacecraft_config=sample_spacecraft_config
        )
        
        # Convert back to SpacecraftConfig
        config = preset_service.get_spacecraft_config(preset)
        
        assert isinstance(config, SpacecraftConfig)
        assert config.vehicle_type == VehicleType.MEDIUM_SAT
        assert config.name == "Test Satellite"
        assert config.mass_kg == 1000.0
        assert config.fuel_capacity_kg == 400.0


class TestVehiclePresetSeeding:
    """Test vehicle preset seeding functionality."""
    
    @pytest.mark.asyncio
    async def test_seed_vehicle_presets(self, test_session: AsyncSession):
        """Test seeding realistic vehicle presets."""
        # Seed presets
        await seed_vehicle_presets(test_session)
        
        # Verify presets were created
        service = VehiclePresetService(test_session)
        presets = await service.list_presets()
        
        assert len(presets) == len(REALISTIC_VEHICLE_PRESETS)
        
        # Check specific presets
        cubesat_preset = await service.get_preset_by_name("CubeSat 3U")
        assert cubesat_preset is not None
        assert cubesat_preset.vehicle_type == VehicleType.CUBESAT.value
        assert cubesat_preset.mass_kg == 4.0
        
        mars_rover_preset = await service.get_preset_by_name("Mars Rover")
        assert mars_rover_preset is not None
        assert mars_rover_preset.vehicle_type == VehicleType.ROVER.value
        assert mars_rover_preset.thrust_n == 0.0  # Rovers don't have propulsion
    
    @pytest.mark.asyncio
    async def test_seed_idempotent(self, test_session: AsyncSession):
        """Test that seeding is idempotent (can be run multiple times)."""
        # Seed twice
        await seed_vehicle_presets(test_session)
        await seed_vehicle_presets(test_session)
        
        # Should still have the same number of presets
        service = VehiclePresetService(test_session)
        presets = await service.list_presets()
        
        assert len(presets) == len(REALISTIC_VEHICLE_PRESETS)


class TestVehicleConfigValidation:
    """Test vehicle configuration validation."""
    
    def test_valid_configuration(self):
        """Test validation of valid configuration."""
        config_data = {
            "vehicle_type": VehicleType.MEDIUM_SAT.value,
            "name": "Test Satellite",
            "mass_kg": 1000.0,
            "fuel_capacity_kg": 400.0,
            "thrust_n": 500.0,
            "specific_impulse_s": 300.0,
            "payload_mass_kg": 200.0,
            "power_w": 2000.0
        }
        
        errors = validate_spacecraft_config(config_data)
        assert len(errors) == 0
    
    def test_excessive_fuel_capacity(self):
        """Test validation of excessive fuel capacity."""
        config_data = {
            "vehicle_type": VehicleType.MEDIUM_SAT.value,
            "name": "Test Satellite",
            "mass_kg": 1000.0,
            "fuel_capacity_kg": 980.0,  # 98% of total mass
            "thrust_n": 500.0,
            "specific_impulse_s": 300.0,
            "payload_mass_kg": 10.0,
            "power_w": 2000.0
        }
        
        errors = validate_spacecraft_config(config_data)
        assert len(errors) > 0
        assert any("Fuel capacity cannot exceed 95%" in error for error in errors)
    
    def test_excessive_payload_mass(self):
        """Test validation of excessive payload mass."""
        config_data = {
            "vehicle_type": VehicleType.MEDIUM_SAT.value,
            "name": "Test Satellite",
            "mass_kg": 1000.0,
            "fuel_capacity_kg": 100.0,
            "thrust_n": 500.0,
            "specific_impulse_s": 300.0,
            "payload_mass_kg": 850.0,  # 85% of total mass
            "power_w": 2000.0
        }
        
        errors = validate_spacecraft_config(config_data)
        assert len(errors) > 0
        assert any("Payload mass cannot exceed 80%" in error for error in errors)
    
    def test_cubesat_mass_validation(self):
        """Test CubeSat specific mass validation."""
        config_data = {
            "vehicle_type": VehicleType.CUBESAT.value,
            "name": "Heavy CubeSat",
            "mass_kg": 100.0,  # Too heavy for CubeSat
            "fuel_capacity_kg": 10.0,
            "thrust_n": 1.0,
            "specific_impulse_s": 200.0,
            "payload_mass_kg": 20.0,
            "power_w": 50.0
        }
        
        errors = validate_spacecraft_config(config_data)
        assert len(errors) > 0
        assert any("CubeSat mass should not exceed 50 kg" in error for error in errors)
    
    def test_rover_thrust_validation(self):
        """Test rover specific thrust validation."""
        config_data = {
            "vehicle_type": VehicleType.ROVER.value,
            "name": "Flying Rover",
            "mass_kg": 500.0,
            "fuel_capacity_kg": 0.0,
            "thrust_n": 100.0,  # Rovers shouldn't have thrust
            "specific_impulse_s": 0.0,
            "payload_mass_kg": 50.0,
            "power_w": 200.0
        }
        
        errors = validate_spacecraft_config(config_data)
        assert len(errors) > 0
        assert any("Rovers should not have propulsive thrust" in error for error in errors)


if __name__ == "__main__":
    pytest.main([__file__])