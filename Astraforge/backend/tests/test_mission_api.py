"""
Tests for mission management API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.mission import (
    Mission, SpacecraftConfig, TrajectoryPlan, MissionTimeline, 
    MissionConstraints, DateRange, VehicleType, CelestialBody, TransferType
)
from app.models.database import Mission as DBMission
from app.schemas.mission import MissionCreateRequest, MissionUpdateRequest


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def sample_mission_data():
    """Sample mission data for testing."""
    return {
        "name": "Mars Sample Return",
        "description": "A mission to collect samples from Mars and return them to Earth",
        "objectives": [
            "Collect soil samples from Mars surface",
            "Return samples to Earth for analysis",
            "Demonstrate advanced propulsion technology"
        ],
        "spacecraft_config": {
            "vehicle_type": "probe",
            "name": "Mars Sample Return Vehicle",
            "mass_kg": 5000.0,
            "fuel_capacity_kg": 3000.0,
            "thrust_n": 10000.0,
            "specific_impulse_s": 350.0,
            "payload_mass_kg": 500.0,
            "power_w": 2000.0
        },
        "trajectory": {
            "launch_window": {
                "start": "2026-07-01T00:00:00Z",
                "end": "2026-08-31T23:59:59Z"
            },
            "departure_body": "earth",
            "target_body": "mars",
            "transfer_type": "hohmann",
            "maneuvers": [
                {
                    "name": "Trans-Mars Injection",
                    "delta_v_ms": 3200.0,
                    "duration_s": 600.0,
                    "timestamp_days": 0.0
                },
                {
                    "name": "Mars Orbit Insertion",
                    "delta_v_ms": 1500.0,
                    "duration_s": 300.0,
                    "timestamp_days": 260.0
                }
            ],
            "total_delta_v": 4700.0,
            "flight_time_days": 260.0
        },
        "timeline": {
            "launch_date": "2026-07-15T12:00:00Z",
            "major_milestones": [
                {
                    "name": "Launch",
                    "date": "2026-07-15T12:00:00Z",
                    "description": "Launch from Earth"
                },
                {
                    "name": "Mars Arrival",
                    "date": "2027-03-31T12:00:00Z",
                    "description": "Arrive at Mars"
                }
            ],
            "mission_phases": [
                {
                    "name": "Launch Phase",
                    "start_date": "2026-07-15T12:00:00Z",
                    "end_date": "2026-07-16T12:00:00Z",
                    "description": "Launch and initial trajectory correction"
                }
            ]
        },
        "constraints": {
            "max_duration_days": 1000.0,
            "max_delta_v_ms": 15000.0,
            "max_mass_kg": 10000.0,
            "min_success_probability": 0.8,
            "max_cost_usd": 1000000000.0,
            "launch_vehicle_constraints": {}
        },
        "is_public": False,
        "difficulty_rating": 4
    }


class TestMissionCRUD:
    """Test mission CRUD operations."""
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    async def test_create_mission_success(self, mock_service_class, mock_db, client, sample_mission_data):
        """Test successful mission creation."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        expected_mission = Mission(**sample_mission_data)
        mock_service.create_mission.return_value = expected_mission
        
        # Make request
        response = client.post("/api/v1/missions/", json=sample_mission_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_mission_data["name"]
        assert data["description"] == sample_mission_data["description"]
        assert len(data["objectives"]) == 3
        
        # Verify service was called
        mock_service.create_mission.assert_called_once()
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    async def test_create_mission_validation_error(self, mock_service_class, mock_db, client):
        """Test mission creation with validation error."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.create_mission.side_effect = ValueError("Invalid mission data")
        
        # Invalid mission data (missing required fields)
        invalid_data = {
            "name": "Test Mission",
            "description": "Test"
        }
        
        # Make request
        response = client.post("/api/v1/missions/", json=invalid_data)
        
        # Assertions
        assert response.status_code == 400
        assert "Invalid mission data" in response.json()["detail"]
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    async def test_get_mission_success(self, mock_service_class, mock_db, client, sample_mission_data):
        """Test successful mission retrieval."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mission_id = uuid4()
        expected_mission = Mission(id=mission_id, **sample_mission_data)
        mock_service.get_mission.return_value = expected_mission
        
        # Make request
        response = client.get(f"/api/v1/missions/{mission_id}")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mission_id)
        assert data["name"] == sample_mission_data["name"]
        
        # Verify service was called
        mock_service.get_mission.assert_called_once_with(mission_id, None)
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    async def test_get_mission_not_found(self, mock_service_class, mock_db, client):
        """Test mission retrieval when mission not found."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.get_mission.return_value = None
        
        mission_id = uuid4()
        
        # Make request
        response = client.get(f"/api/v1/missions/{mission_id}")
        
        # Assertions
        assert response.status_code == 404
        assert "Mission not found" in response.json()["detail"]
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    async def test_update_mission_success(self, mock_service_class, mock_db, client, sample_mission_data):
        """Test successful mission update."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mission_id = uuid4()
        updated_data = sample_mission_data.copy()
        updated_data["name"] = "Updated Mission Name"
        
        expected_mission = Mission(id=mission_id, **updated_data)
        mock_service.update_mission.return_value = expected_mission
        
        update_request = {"name": "Updated Mission Name"}
        
        # Make request
        response = client.put(f"/api/v1/missions/{mission_id}", json=update_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Mission Name"
        
        # Verify service was called
        mock_service.update_mission.assert_called_once()
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    async def test_delete_mission_success(self, mock_service_class, mock_db, client):
        """Test successful mission deletion."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.delete_mission.return_value = True
        
        mission_id = uuid4()
        
        # Make request
        response = client.delete(f"/api/v1/missions/{mission_id}")
        
        # Assertions
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify service was called
        mock_service.delete_mission.assert_called_once_with(mission_id, None)
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    async def test_delete_mission_not_found(self, mock_service_class, mock_db, client):
        """Test mission deletion when mission not found."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.delete_mission.return_value = False
        
        mission_id = uuid4()
        
        # Make request
        response = client.delete(f"/api/v1/missions/{mission_id}")
        
        # Assertions
        assert response.status_code == 404
        assert "not found or access denied" in response.json()["detail"]


class TestMissionListing:
    """Test mission listing and search functionality."""
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    async def test_list_missions_default(self, mock_service_class, mock_db, client):
        """Test default mission listing."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        from app.schemas.mission import MissionListResponse, MissionSummaryResponse
        
        mock_response = MissionListResponse(
            missions=[],
            total_count=0,
            page=1,
            page_size=20,
            has_next=False,
            has_previous=False
        )
        mock_service.list_missions.return_value = mock_response
        
        # Make request
        response = client.get("/api/v1/missions/")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_count"] == 0
        assert data["missions"] == []
        
        # Verify service was called with defaults
        mock_service.list_missions.assert_called_once()
        call_args = mock_service.list_missions.call_args
        assert call_args.kwargs["page"] == 1
        assert call_args.kwargs["page_size"] == 20
        assert call_args.kwargs["include_public"] == True
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    async def test_list_missions_with_filters(self, mock_service_class, mock_db, client):
        """Test mission listing with filters."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        from app.schemas.mission import MissionListResponse
        
        mock_response = MissionListResponse(
            missions=[],
            total_count=0,
            page=1,
            page_size=10,
            has_next=False,
            has_previous=False
        )
        mock_service.list_missions.return_value = mock_response
        
        # Make request with filters
        response = client.get(
            "/api/v1/missions/?page=1&page_size=10&search=mars&target_body=mars&difficulty_min=3"
        )
        
        # Assertions
        assert response.status_code == 200
        
        # Verify service was called with filters
        mock_service.list_missions.assert_called_once()
        call_args = mock_service.list_missions.call_args
        assert call_args.kwargs["search"] == "mars"
        assert call_args.kwargs["target_body"] == "mars"
        assert call_args.kwargs["difficulty_min"] == 3
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    async def test_search_missions(self, mock_service_class, mock_db, client):
        """Test mission search functionality."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.search_missions.return_value = []
        
        # Make request
        response = client.get("/api/v1/missions/search/?q=mars&limit=5")
        
        # Assertions
        assert response.status_code == 200
        assert response.json() == []
        
        # Verify service was called
        mock_service.search_missions.assert_called_once_with("mars", None, 5)


class TestMissionSimulation:
    """Test mission simulation endpoints."""
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    @patch('app.services.simulation_service.SimulationService')
    async def test_simulate_mission_success(self, mock_sim_service_class, mock_mission_service_class, mock_db, client, sample_mission_data):
        """Test successful mission simulation."""
        # Setup mocks
        mock_mission_service = AsyncMock()
        mock_mission_service_class.return_value = mock_mission_service
        
        mock_sim_service = AsyncMock()
        mock_sim_service_class.return_value = mock_sim_service
        
        mission_id = uuid4()
        mission = Mission(id=mission_id, **sample_mission_data)
        mock_mission_service.get_mission.return_value = mission
        
        from app.models.mission import SimulationResult
        sim_result = SimulationResult(
            mission_id=mission_id,
            success_probability=0.85,
            total_duration_days=260.0,
            fuel_consumption_kg=2800.0,
            cost_estimate_usd=500000000.0,
            risk_factors=[],
            performance_metrics={"efficiency": 0.9}
        )
        mock_sim_service.simulate_mission.return_value = sim_result
        
        simulation_request = {
            "mission_id": str(mission_id),
            "simulation_parameters": {},
            "include_detailed_results": True
        }
        
        # Make request
        response = client.post(f"/api/v1/missions/{mission_id}/simulate", json=simulation_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["mission_id"] == str(mission_id)
        assert data["success_probability"] == 0.85
        assert data["fuel_consumption_kg"] == 2800.0
        
        # Verify services were called
        mock_mission_service.get_mission.assert_called_once()
        mock_sim_service.simulate_mission.assert_called_once()
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    async def test_simulate_mission_not_found(self, mock_mission_service_class, mock_db, client):
        """Test simulation when mission not found."""
        # Setup mocks
        mock_mission_service = AsyncMock()
        mock_mission_service_class.return_value = mock_mission_service
        mock_mission_service.get_mission.return_value = None
        
        mission_id = uuid4()
        simulation_request = {
            "mission_id": str(mission_id),
            "simulation_parameters": {},
            "include_detailed_results": True
        }
        
        # Make request
        response = client.post(f"/api/v1/missions/{mission_id}/simulate", json=simulation_request)
        
        # Assertions
        assert response.status_code == 404
        assert "Mission not found" in response.json()["detail"]


class TestMissionGeneration:
    """Test AI-powered mission generation."""
    
    @patch('app.api.missions.get_db')
    @patch('app.services.mission_service.MissionService')
    @patch('app.ai.ideation_service.MissionIdeationService')
    @patch('app.ai.provider_factory.LLMProviderManager')
    async def test_generate_mission_success(self, mock_provider_manager, mock_ideation_service_class, mock_mission_service_class, mock_db, client, sample_mission_data):
        """Test successful AI mission generation."""
        # Setup mocks
        mock_mission_service = AsyncMock()
        mock_mission_service_class.return_value = mock_mission_service
        
        mock_ideation_service = AsyncMock()
        mock_ideation_service_class.return_value = mock_ideation_service
        
        # Mock AI generation result
        generated_mission = Mission(**sample_mission_data)
        
        class MockGenerationResult:
            def __init__(self):
                self.mission = generated_mission
                self.alternatives = []
                self.metadata = {"provider": "claude", "tokens_used": 1500}
        
        mock_ideation_service.generate_mission.return_value = MockGenerationResult()
        
        # Mock mission saving
        mock_mission_service.create_mission.return_value = generated_mission
        
        generation_request = {
            "prompt": "Create a mission to explore Jupiter's moons",
            "temperature": 0.7,
            "include_alternatives": True
        }
        
        # Make request
        response = client.post("/api/v1/missions/generate", json=generation_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "mission" in data
        assert data["mission"]["name"] == sample_mission_data["name"]
        assert "generation_metadata" in data
        
        # Verify services were called
        mock_ideation_service.generate_mission.assert_called_once()
        mock_mission_service.create_mission.assert_called_once()
    
    @patch('app.api.missions.get_db')
    @patch('app.ai.ideation_service.MissionIdeationService')
    @patch('app.ai.provider_factory.LLMProviderManager')
    async def test_generate_mission_invalid_prompt(self, mock_provider_manager, mock_ideation_service_class, mock_db, client):
        """Test mission generation with invalid prompt."""
        generation_request = {
            "prompt": "short",  # Too short
            "temperature": 0.7
        }
        
        # Make request
        response = client.post("/api/v1/missions/generate", json=generation_request)
        
        # Assertions
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestMissionService:
    """Test mission service business logic."""
    
    async def test_mission_feasibility_validation(self, sample_mission_data):
        """Test mission feasibility validation."""
        # Create mission with insufficient delta-v
        invalid_data = sample_mission_data.copy()
        invalid_data["spacecraft_config"]["fuel_capacity_kg"] = 100.0  # Very low fuel
        
        mission = Mission(**invalid_data)
        issues = mission.validate_mission_feasibility()
        
        # Should have feasibility issues
        assert len(issues) > 0
        assert any("delta-v" in issue.lower() for issue in issues)
    
    async def test_mission_complexity_calculation(self, sample_mission_data):
        """Test mission complexity calculation."""
        mission = Mission(**sample_mission_data)
        complexity = mission.calculate_mission_complexity()
        
        # Should be a reasonable complexity score
        assert 0.0 <= complexity <= 5.0
        assert complexity > 1.0  # Mars mission should be moderately complex


if __name__ == "__main__":
    pytest.main([__file__])
