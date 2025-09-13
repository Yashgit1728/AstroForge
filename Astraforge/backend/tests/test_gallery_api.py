"""
Tests for gallery API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.mission import MissionSummaryResponse


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def sample_mission_summary():
    """Sample mission summary for testing."""
    return MissionSummaryResponse(
        id=uuid4(),
        name="Mars Sample Return",
        description="A mission to collect samples from Mars",
        objectives=["Collect samples", "Return to Earth"],
        target_body="mars",
        vehicle_type="probe",
        total_delta_v=4700.0,
        flight_time_days=260.0,
        created_at=datetime.now(),
        user_id="test-user",
        is_public=True,
        difficulty_rating=4,
        has_simulation_results=True
    )


class TestGalleryEndpoints:
    """Test gallery API endpoints."""
    
    @patch('app.api.gallery.get_db')
    @patch('app.api.gallery.GalleryService')
    @patch('app.api.gallery.get_current_user')
    def test_get_featured_missions(self, mock_get_user, mock_service_class, mock_db, client, sample_mission_summary):
        """Test getting featured missions."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_get_user.return_value = None
        
        mock_service.get_featured_missions.return_value = [sample_mission_summary]
        
        # Make request
        response = client.get("/api/v1/gallery/featured?limit=10")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "missions" in data
        assert "total_count" in data
        assert data["total_count"] == 1
        assert len(data["missions"]) == 1
        assert data["missions"][0]["name"] == "Mars Sample Return"
        
        # Verify service call
        mock_service.get_featured_missions.assert_called_once_with(10, None)
    
    @patch('app.api.gallery.get_db')
    @patch('app.api.gallery.GalleryService')
    def test_get_example_missions(self, mock_service_class, mock_db, client, sample_mission_summary):
        """Test getting example missions."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mock_service.get_example_missions.return_value = [sample_mission_summary]
        
        # Make request
        response = client.get("/api/v1/gallery/examples?category=mars&difficulty=4&limit=20")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "missions" in data
        assert "category" in data
        assert "difficulty" in data
        assert "total_count" in data
        assert data["category"] == "mars"
        assert data["difficulty"] == 4
        assert data["total_count"] == 1
        
        # Verify service call
        mock_service.get_example_missions.assert_called_once_with("mars", 4, 20)
    
    @patch('app.api.gallery.get_db')
    @patch('app.api.gallery.GalleryService')
    def test_get_popular_missions(self, mock_service_class, mock_db, client, sample_mission_summary):
        """Test getting popular missions."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mock_service.get_popular_missions.return_value = [sample_mission_summary]
        
        # Make request
        response = client.get("/api/v1/gallery/popular?time_period=week&limit=10")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "missions" in data
        assert "time_period" in data
        assert "total_count" in data
        assert data["time_period"] == "week"
        assert data["total_count"] == 1
        
        # Verify service call
        mock_service.get_popular_missions.assert_called_once_with("week", 10)
    
    @patch('app.api.gallery.get_db')
    @patch('app.api.gallery.GalleryService')
    @patch('app.api.gallery.get_current_user')
    def test_search_missions(self, mock_get_user, mock_service_class, mock_db, client):
        """Test mission search functionality."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_get_user.return_value = None
        
        from app.schemas.mission import MissionListResponse
        mock_response = MissionListResponse(
            missions=[],
            total_count=0,
            page=1,
            page_size=20,
            has_next=False,
            has_previous=False
        )
        mock_service.search_missions_advanced.return_value = mock_response
        
        # Make request
        response = client.get(
            "/api/v1/gallery/search?q=mars&page=1&page_size=20&target_body=mars&difficulty_min=3"
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "missions" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
        
        # Verify service call
        mock_service.search_missions_advanced.assert_called_once()
        call_args = mock_service.search_missions_advanced.call_args
        assert call_args.kwargs["query"] == "mars"
        assert call_args.kwargs["page"] == 1
        assert call_args.kwargs["page_size"] == 20
        assert "target_body" in call_args.kwargs["filters"]
        assert call_args.kwargs["filters"]["target_body"] == "mars"
    
    @patch('app.api.gallery.get_db')
    @patch('app.api.gallery.GalleryService')
    @patch('app.api.gallery.get_current_user')
    def test_advanced_search_missions(self, mock_get_user, mock_service_class, mock_db, client):
        """Test advanced search with POST request."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_get_user.return_value = None
        
        from app.schemas.mission import MissionListResponse
        mock_response = MissionListResponse(
            missions=[],
            total_count=0,
            page=1,
            page_size=20,
            has_next=False,
            has_previous=False
        )
        mock_service.search_missions_advanced.return_value = mock_response
        
        search_request = {
            "query": "mars exploration",
            "filters": {
                "target_body": "mars",
                "difficulty_min": 3,
                "difficulty_max": 5,
                "has_simulation": True,
                "sort_by": "difficulty_rating",
                "sort_order": "desc"
            },
            "page": 1,
            "page_size": 10
        }
        
        # Make request
        response = client.post("/api/v1/gallery/search/advanced", json=search_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "missions" in data
        assert "total_count" in data
        
        # Verify service call
        mock_service.search_missions_advanced.assert_called_once()
    
    @patch('app.api.gallery.get_db')
    @patch('app.api.gallery.GalleryService')
    def test_get_mission_categories(self, mock_service_class, mock_db, client):
        """Test getting mission categories."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mock_categories = {
            "mars": 15,
            "moon": 8,
            "jupiter": 3,
            "venus": 5
        }
        mock_service.get_mission_categories.return_value = mock_categories
        
        # Make request
        response = client.get("/api/v1/gallery/categories")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data == mock_categories
        assert "mars" in data
        assert data["mars"] == 15
        
        # Verify service call
        mock_service.get_mission_categories.assert_called_once()
    
    @patch('app.api.gallery.get_db')
    @patch('app.api.gallery.GalleryService')
    def test_get_difficulty_distribution(self, mock_service_class, mock_db, client):
        """Test getting difficulty distribution."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mock_distribution = {
            1: 5,
            2: 8,
            3: 12,
            4: 7,
            5: 3
        }
        mock_service.get_difficulty_distribution.return_value = mock_distribution
        
        # Make request
        response = client.get("/api/v1/gallery/difficulty-distribution")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        # JSON converts integer keys to strings
        expected_data = {str(k): v for k, v in mock_distribution.items()}
        assert data == expected_data
        assert data["3"] == 12  # JSON keys are strings
        
        # Verify service call
        mock_service.get_difficulty_distribution.assert_called_once()
    
    @patch('app.api.gallery.get_db')
    @patch('app.api.gallery.GalleryService')
    def test_get_gallery_stats(self, mock_service_class, mock_db, client):
        """Test getting comprehensive gallery stats."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mock_stats = {
            "total_missions": 35,
            "simulated_missions": 28,
            "recent_missions": 5,
            "simulation_rate": 0.8
        }
        mock_categories = {"mars": 15, "moon": 8}
        mock_distribution = {1: 5, 2: 8, 3: 12}
        
        mock_service.get_gallery_stats.return_value = mock_stats
        mock_service.get_mission_categories.return_value = mock_categories
        mock_service.get_difficulty_distribution.return_value = mock_distribution
        
        # Make request
        response = client.get("/api/v1/gallery/stats")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_missions"] == 35
        assert data["simulated_missions"] == 28
        assert data["simulation_rate"] == 0.8
        assert "categories" in data
        assert "difficulty_distribution" in data
        assert data["categories"]["mars"] == 15
        
        # Verify service calls
        mock_service.get_gallery_stats.assert_called_once()
        mock_service.get_mission_categories.assert_called_once()
        mock_service.get_difficulty_distribution.assert_called_once()
    
    @patch('app.api.gallery.get_db')
    @patch('app.api.gallery.GalleryService')
    @patch('app.api.gallery.get_current_user')
    def test_get_mission_suggestions(self, mock_get_user, mock_service_class, mock_db, client, sample_mission_summary):
        """Test getting mission suggestions."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mock_get_user.return_value = None
        mock_service.get_featured_missions.return_value = [sample_mission_summary]
        
        # Make request
        response = client.get("/api/v1/gallery/suggestions?limit=5")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Mars Sample Return"
        
        # Verify service call
        mock_service.get_featured_missions.assert_called_once_with(5, None)
    
    def test_search_missions_invalid_query(self, client):
        """Test search with invalid query parameters."""
        # Empty query should fail validation
        response = client.get("/api/v1/gallery/search?q=")
        
        assert response.status_code == 422  # Validation error
    
    def test_popular_missions_invalid_time_period(self, client):
        """Test popular missions with invalid time period."""
        response = client.get("/api/v1/gallery/popular?time_period=invalid")
        
        assert response.status_code == 422  # Validation error


class TestGalleryService:
    """Test gallery service business logic."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def gallery_service(self, mock_db_session):
        """Gallery service with mocked database."""
        from app.services.gallery_service import GalleryService
        return GalleryService(mock_db_session)
    
    async def test_get_featured_missions_empty_result(self, gallery_service, mock_db_session):
        """Test getting featured missions when no missions exist."""
        # Mock empty database result
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        # Get featured missions
        missions = await gallery_service.get_featured_missions(limit=10)
        
        # Assertions
        assert missions == []
        mock_db_session.execute.assert_called_once()
    
    async def test_search_missions_advanced_with_filters(self, gallery_service, mock_db_session):
        """Test advanced search with multiple filters."""
        # Mock database results
        mock_missions_result = AsyncMock()
        mock_missions_result.scalars.return_value.all.return_value = []
        
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 0
        
        mock_db_session.execute.side_effect = [mock_missions_result, mock_count_result]
        
        # Perform search
        filters = {
            "target_body": "mars",
            "difficulty_min": 3,
            "has_simulation": True,
            "sort_by": "created_at",
            "sort_order": "desc"
        }
        
        result = await gallery_service.search_missions_advanced(
            query="mars mission",
            filters=filters,
            user_id="test-user",
            page=1,
            page_size=20
        )
        
        # Assertions
        assert result.total_count == 0
        assert result.page == 1
        assert result.page_size == 20
        assert result.missions == []
        
        # Verify database calls
        assert mock_db_session.execute.call_count == 2
    
    async def test_get_gallery_stats_calculation(self, gallery_service, mock_db_session):
        """Test gallery stats calculation."""
        # Mock database results for different queries
        mock_results = [
            AsyncMock(),  # total missions
            AsyncMock(),  # simulated missions  
            AsyncMock()   # recent missions
        ]
        
        mock_results[0].scalar.return_value = 100  # total
        mock_results[1].scalar.return_value = 75   # simulated
        mock_results[2].scalar.return_value = 10   # recent
        
        mock_db_session.execute.side_effect = mock_results
        
        # Get stats
        stats = await gallery_service.get_gallery_stats()
        
        # Assertions
        assert stats["total_missions"] == 100
        assert stats["simulated_missions"] == 75
        assert stats["recent_missions"] == 10
        assert stats["simulation_rate"] == 0.75
        
        # Verify database calls
        assert mock_db_session.execute.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__])