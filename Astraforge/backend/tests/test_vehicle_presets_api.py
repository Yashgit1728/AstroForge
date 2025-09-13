"""
Tests for vehicle presets API endpoints.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.database import Base
from app.models.mission import SpacecraftConfig, VehicleType
from app.core.database import get_db


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
async def test_client(test_session):
    """Create test client with database dependency override."""
    
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_preset_data():
    """Sample vehicle preset data for testing."""
    return {
        "name": "Test Medium Satellite",
        "description": "A test medium satellite configuration",
        "spacecraft_config": {
            "vehicle_type": "medium_sat",
            "name": "Test Satellite",
            "mass_kg": 1000.0,
            "fuel_capacity_kg": 400.0,
            "thrust_n": 500.0,
            "specific_impulse_s": 300.0,
            "payload_mass_kg": 200.0,
            "power_w": 2000.0
        },
        "is_public": True,
        "created_by": "test_user"
    }


class TestVehiclePresetsAPI:
    """Test vehicle presets API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_vehicle_preset(self, test_client: AsyncClient, sample_preset_data):
        """Test creating a vehicle preset via API."""
        response = await test_client.post("/api/v1/vehicle-presets/", json=sample_preset_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == sample_preset_data["name"]
        assert data["description"] == sample_preset_data["description"]
        assert data["vehicle_type"] == "medium_sat"
        assert data["is_public"] is True
        assert data["created_by"] == "test_user"
        assert data["mass_kg"] == 1000.0
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_duplicate_preset_name(self, test_client: AsyncClient, sample_preset_data):
        """Test creating a preset with duplicate name fails."""
        # Create first preset
        response1 = await test_client.post("/api/v1/vehicle-presets/", json=sample_preset_data)
        assert response1.status_code == 200
        
        # Try to create second preset with same name
        response2 = await test_client.post("/api/v1/vehicle-presets/", json=sample_preset_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_invalid_spacecraft_config(self, test_client: AsyncClient):
        """Test creating preset with invalid spacecraft config fails."""
        invalid_data = {
            "name": "Invalid Preset",
            "description": "Invalid configuration",
            "spacecraft_config": {
                "vehicle_type": "medium_sat",
                "name": "Invalid Satellite",
                "mass_kg": 1000.0,
                "fuel_capacity_kg": 980.0,  # Exceeds 95% of total mass
                "thrust_n": 500.0,
                "specific_impulse_s": 300.0,
                "payload_mass_kg": 10.0,
                "power_w": 2000.0
            },
            "is_public": True
        }
        
        response = await test_client.post("/api/v1/vehicle-presets/", json=invalid_data)
        assert response.status_code == 422  # Pydantic validation error
        # The error should be in the detail field for validation errors
        error_detail = response.json()
        assert "detail" in error_detail
    
    @pytest.mark.asyncio
    async def test_list_vehicle_presets(self, test_client: AsyncClient, sample_preset_data):
        """Test listing vehicle presets."""
        # Create a preset first
        await test_client.post("/api/v1/vehicle-presets/", json=sample_preset_data)
        
        # List presets
        response = await test_client.get("/api/v1/vehicle-presets/")
        assert response.status_code == 200
        
        data = response.json()
        assert "presets" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert len(data["presets"]) == 1
        assert data["presets"][0]["name"] == sample_preset_data["name"]
    
    @pytest.mark.asyncio
    async def test_list_presets_with_filters(self, test_client: AsyncClient):
        """Test listing presets with filters."""
        # Create multiple presets
        medium_sat_data = {
            "name": "Medium Sat",
            "spacecraft_config": {
                "vehicle_type": "medium_sat",
                "name": "Medium Satellite",
                "mass_kg": 1000.0,
                "fuel_capacity_kg": 400.0,
                "thrust_n": 500.0,
                "specific_impulse_s": 300.0,
                "payload_mass_kg": 200.0,
                "power_w": 2000.0
            },
            "is_public": True
        }
        
        cubesat_data = {
            "name": "CubeSat",
            "spacecraft_config": {
                "vehicle_type": "cubesat",
                "name": "Test CubeSat",
                "mass_kg": 4.0,
                "fuel_capacity_kg": 0.5,
                "thrust_n": 0.1,
                "specific_impulse_s": 220.0,
                "payload_mass_kg": 1.5,
                "power_w": 20.0
            },
            "is_public": False
        }
        
        await test_client.post("/api/v1/vehicle-presets/", json=medium_sat_data)
        await test_client.post("/api/v1/vehicle-presets/", json=cubesat_data)
        
        # Filter by vehicle type
        response = await test_client.get("/api/v1/vehicle-presets/?vehicle_type=medium_sat")
        assert response.status_code == 200
        data = response.json()
        assert len(data["presets"]) == 1
        assert data["presets"][0]["vehicle_type"] == "medium_sat"
        
        # Filter by public status
        response = await test_client.get("/api/v1/vehicle-presets/?is_public=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data["presets"]) == 1
        assert data["presets"][0]["is_public"] is True
    
    @pytest.mark.asyncio
    async def test_get_vehicle_preset_by_id(self, test_client: AsyncClient, sample_preset_data):
        """Test getting a vehicle preset by ID."""
        # Create preset
        create_response = await test_client.post("/api/v1/vehicle-presets/", json=sample_preset_data)
        preset_id = create_response.json()["id"]
        
        # Get preset by ID
        response = await test_client.get(f"/api/v1/vehicle-presets/{preset_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == preset_id
        assert data["name"] == sample_preset_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_preset(self, test_client: AsyncClient):
        """Test getting a nonexistent preset returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await test_client.get(f"/api/v1/vehicle-presets/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_vehicle_preset_by_name(self, test_client: AsyncClient, sample_preset_data):
        """Test getting a vehicle preset by name."""
        # Create preset
        await test_client.post("/api/v1/vehicle-presets/", json=sample_preset_data)
        
        # Get preset by name
        preset_name = sample_preset_data["name"]
        response = await test_client.get(f"/api/v1/vehicle-presets/by-name/{preset_name}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == preset_name
    
    @pytest.mark.asyncio
    async def test_update_vehicle_preset(self, test_client: AsyncClient, sample_preset_data):
        """Test updating a vehicle preset."""
        # Create preset
        create_response = await test_client.post("/api/v1/vehicle-presets/", json=sample_preset_data)
        preset_id = create_response.json()["id"]
        
        # Update preset
        update_data = {
            "name": "Updated Satellite",
            "description": "Updated description",
            "is_public": False
        }
        
        response = await test_client.put(f"/api/v1/vehicle-presets/{preset_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Satellite"
        assert data["description"] == "Updated description"
        assert data["is_public"] is False
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_preset(self, test_client: AsyncClient):
        """Test updating a nonexistent preset returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"name": "Updated Name"}
        
        response = await test_client.put(f"/api/v1/vehicle-presets/{fake_id}", json=update_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_delete_vehicle_preset(self, test_client: AsyncClient, sample_preset_data):
        """Test deleting a vehicle preset."""
        # Create preset
        create_response = await test_client.post("/api/v1/vehicle-presets/", json=sample_preset_data)
        preset_id = create_response.json()["id"]
        
        # Delete preset
        response = await test_client.delete(f"/api/v1/vehicle-presets/{preset_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify deletion
        get_response = await test_client.get(f"/api/v1/vehicle-presets/{preset_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_preset(self, test_client: AsyncClient):
        """Test deleting a nonexistent preset returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await test_client.delete(f"/api/v1/vehicle-presets/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_seed_vehicle_presets(self, test_client: AsyncClient):
        """Test seeding vehicle presets via API."""
        response = await test_client.post("/api/v1/vehicle-presets/seed")
        assert response.status_code == 200
        assert "seeded successfully" in response.json()["message"]
        
        # Verify presets were created
        list_response = await test_client.get("/api/v1/vehicle-presets/")
        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data["presets"]) > 0  # Should have seeded presets
    
    @pytest.mark.asyncio
    async def test_get_spacecraft_config(self, test_client: AsyncClient, sample_preset_data):
        """Test getting spacecraft configuration from preset."""
        # Create preset
        create_response = await test_client.post("/api/v1/vehicle-presets/", json=sample_preset_data)
        preset_id = create_response.json()["id"]
        
        # Get spacecraft config
        response = await test_client.get(f"/api/v1/vehicle-presets/{preset_id}/spacecraft-config")
        assert response.status_code == 200
        
        data = response.json()
        assert data["vehicle_type"] == "medium_sat"
        assert data["name"] == "Test Satellite"
        assert data["mass_kg"] == 1000.0
        assert data["fuel_capacity_kg"] == 400.0
    
    @pytest.mark.asyncio
    async def test_pagination(self, test_client: AsyncClient):
        """Test pagination in preset listing."""
        # Create multiple presets
        for i in range(5):
            preset_data = {
                "name": f"Test Preset {i}",
                "spacecraft_config": {
                    "vehicle_type": "small_sat",
                    "name": f"Satellite {i}",
                    "mass_kg": 100.0 + i * 10,
                    "fuel_capacity_kg": 20.0,
                    "thrust_n": 10.0,
                    "specific_impulse_s": 250.0,
                    "payload_mass_kg": 30.0,
                    "power_w": 200.0
                },
                "is_public": True
            }
            await test_client.post("/api/v1/vehicle-presets/", json=preset_data)
        
        # Test pagination
        response = await test_client.get("/api/v1/vehicle-presets/?limit=3&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["presets"]) == 3
        assert data["limit"] == 3
        assert data["offset"] == 0
        
        # Test second page
        response = await test_client.get("/api/v1/vehicle-presets/?limit=3&offset=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["presets"]) == 2  # Remaining presets
        assert data["offset"] == 3


if __name__ == "__main__":
    pytest.main([__file__])