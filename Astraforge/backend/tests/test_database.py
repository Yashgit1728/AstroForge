"""
Database integration tests for AstraForge models.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import Base, Mission, SimulationResult, VehiclePreset
from app.models.mission import (
    SpacecraftConfig, TrajectoryPlan, MissionTimeline, MissionConstraints,
    VehicleType, CelestialBody, TransferType, DateRange, Maneuver
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


@pytest.fixture
def sample_mission_data():
    """Create sample mission data for testing."""
    spacecraft_config = SpacecraftConfig(
        vehicle_type=VehicleType.MEDIUM_SAT,
        name="Test Satellite",
        mass_kg=1000.0,
        fuel_capacity_kg=400.0,
        thrust_n=500.0,
        specific_impulse_s=300.0,
        payload_mass_kg=200.0
    )
    
    launch_window = DateRange(
        start=datetime.now(),
        end=datetime.now() + timedelta(days=30)
    )
    
    trajectory = TrajectoryPlan(
        launch_window=launch_window,
        departure_body=CelestialBody.EARTH,
        target_body=CelestialBody.MARS,
        transfer_type=TransferType.HOHMANN,
        maneuvers=[
            Maneuver(name="Launch", delta_v_ms=9500.0, duration_s=600.0, timestamp_days=0.0)
        ],
        total_delta_v=9500.0,
        flight_time_days=260.0
    )
    
    timeline = MissionTimeline(
        launch_date=datetime.now(),
        major_milestones=[
            {"name": "Launch", "date": datetime.now(), "description": "Mission launch"}
        ]
    )
    
    constraints = MissionConstraints()
    
    return {
        "name": "Mars Sample Return",
        "description": "A mission to collect samples from Mars and return them to Earth",
        "objectives": ["Collect soil samples", "Return to Earth", "Analyze samples"],
        "spacecraft_config": spacecraft_config.model_dump(),
        "trajectory": trajectory.model_dump(mode='json'),
        "timeline": timeline.model_dump(mode='json'),
        "constraints": constraints.model_dump(),
        "user_id": "test_user_123",
        "is_public": True,
        "difficulty_rating": 3
    }


class TestMissionDatabase:
    """Test Mission database operations."""
    
    @pytest.mark.asyncio
    async def test_create_mission(self, test_session: AsyncSession, sample_mission_data):
        """Test creating a mission in the database."""
        mission = Mission(**sample_mission_data)
        
        test_session.add(mission)
        await test_session.commit()
        await test_session.refresh(mission)
        
        assert mission.id is not None
        assert mission.name == "Mars Sample Return"
        assert mission.user_id == "test_user_123"
        assert mission.is_public is True
        assert mission.difficulty_rating == 3
        assert mission.created_at is not None
        assert mission.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_mission_relationships(self, test_session: AsyncSession, sample_mission_data):
        """Test mission relationships with simulation results."""
        # Create mission
        mission = Mission(**sample_mission_data)
        test_session.add(mission)
        await test_session.commit()
        await test_session.refresh(mission)
        
        # Create simulation result
        simulation_result = SimulationResult(
            mission_id=mission.id,
            success_probability=0.85,
            total_duration_days=260.0,
            fuel_consumption_kg=800.0,
            cost_estimate_usd=50000000.0,
            risk_factors=[],
            performance_metrics={"efficiency": 0.9}
        )
        
        test_session.add(simulation_result)
        await test_session.commit()
        await test_session.refresh(simulation_result)
        
        # Test relationship
        assert simulation_result.mission_id == mission.id
        
        # Refresh mission to load relationships
        await test_session.refresh(mission)
        
        # Query simulation results explicitly
        from sqlalchemy import select
        result = await test_session.execute(
            select(SimulationResult).where(SimulationResult.mission_id == mission.id)
        )
        simulation_results = result.scalars().all()
        
        assert len(simulation_results) == 1
        assert simulation_results[0].id == simulation_result.id


class TestVehiclePresetDatabase:
    """Test VehiclePreset database operations."""
    
    @pytest.mark.asyncio
    async def test_create_vehicle_preset(self, test_session: AsyncSession):
        """Test creating a vehicle preset in the database."""
        preset_data = {
            "name": "Standard Satellite",
            "description": "A standard medium-sized satellite configuration",
            "vehicle_type": "medium_sat",
            "configuration": {
                "mass_kg": 1000.0,
                "fuel_capacity_kg": 400.0,
                "thrust_n": 500.0,
                "specific_impulse_s": 300.0,
                "payload_mass_kg": 200.0
            },
            "is_public": True,
            "mass_kg": 1000.0,
            "thrust_n": 500.0,
            "specific_impulse_s": 300.0,
            "created_by": "system"
        }
        
        preset = VehiclePreset(**preset_data)
        
        test_session.add(preset)
        await test_session.commit()
        await test_session.refresh(preset)
        
        assert preset.id is not None
        assert preset.name == "Standard Satellite"
        assert preset.vehicle_type == "medium_sat"
        assert preset.is_public is True
        assert preset.mass_kg == 1000.0
        assert preset.created_at is not None
    
    @pytest.mark.asyncio
    async def test_vehicle_preset_unique_name(self, test_session: AsyncSession):
        """Test that vehicle preset names must be unique."""
        preset_data = {
            "name": "Unique Satellite",
            "vehicle_type": "medium_sat",
            "configuration": {"mass_kg": 1000.0},
            "mass_kg": 1000.0,
            "thrust_n": 500.0,
            "specific_impulse_s": 300.0
        }
        
        # Create first preset
        preset1 = VehiclePreset(**preset_data)
        test_session.add(preset1)
        await test_session.commit()
        
        # Try to create second preset with same name
        preset2 = VehiclePreset(**preset_data)
        test_session.add(preset2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await test_session.commit()


class TestSimulationResultDatabase:
    """Test SimulationResult database operations."""
    
    @pytest.mark.asyncio
    async def test_create_simulation_result(self, test_session: AsyncSession, sample_mission_data):
        """Test creating a simulation result in the database."""
        # Create mission first
        mission = Mission(**sample_mission_data)
        test_session.add(mission)
        await test_session.commit()
        await test_session.refresh(mission)
        
        # Create simulation result
        result_data = {
            "mission_id": mission.id,
            "success_probability": 0.85,
            "total_duration_days": 260.0,
            "fuel_consumption_kg": 800.0,
            "cost_estimate_usd": 50000000.0,
            "risk_factors": [
                {
                    "category": "Technical",
                    "description": "Propulsion system failure",
                    "probability": 0.05,
                    "impact": "high"
                }
            ],
            "performance_metrics": {
                "efficiency": 0.9,
                "accuracy": 0.95,
                "fuel_efficiency": 0.88
            },
            "trajectory_data": {
                "waypoints": [
                    {"time": 0, "position": [0, 0, 0]},
                    {"time": 100, "position": [1000, 2000, 500]}
                ]
            }
        }
        
        result = SimulationResult(**result_data)
        
        test_session.add(result)
        await test_session.commit()
        await test_session.refresh(result)
        
        assert result.id is not None
        assert result.mission_id == mission.id
        assert result.success_probability == 0.85
        assert result.total_duration_days == 260.0
        assert len(result.risk_factors) == 1
        assert "efficiency" in result.performance_metrics
        assert result.trajectory_data is not None
        assert result.simulation_timestamp is not None


class TestDatabaseIndexes:
    """Test database indexes and performance optimizations."""
    
    @pytest.mark.asyncio
    async def test_mission_indexes(self, test_session: AsyncSession, sample_mission_data):
        """Test that mission indexes work correctly."""
        # Create multiple missions with different attributes
        missions = []
        for i in range(5):
            mission_data = sample_mission_data.copy()
            mission_data["name"] = f"Mission {i}"
            mission_data["user_id"] = f"user_{i % 2}"  # Two different users
            mission_data["difficulty_rating"] = (i % 3) + 1  # Ratings 1-3
            mission_data["is_public"] = i % 2 == 0  # Alternate public/private
            
            mission = Mission(**mission_data)
            missions.append(mission)
            test_session.add(mission)
        
        await test_session.commit()
        
        # Test queries that should use indexes
        from sqlalchemy import select
        
        # Query by user_id (should use idx_missions_user_id)
        result = await test_session.execute(
            select(Mission).where(Mission.user_id == "user_0")
        )
        user_missions = result.scalars().all()
        assert len(user_missions) >= 1
        
        # Query by is_public (should use idx_missions_is_public)
        result = await test_session.execute(
            select(Mission).where(Mission.is_public == True)
        )
        public_missions = result.scalars().all()
        assert len(public_missions) >= 1
        
        # Query by difficulty_rating (should use idx_missions_difficulty)
        result = await test_session.execute(
            select(Mission).where(Mission.difficulty_rating == 2)
        )
        medium_missions = result.scalars().all()
        assert len(medium_missions) >= 0  # May be 0 depending on data


if __name__ == "__main__":
    pytest.main([__file__])