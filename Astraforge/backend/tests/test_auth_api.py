"""
Tests for authentication API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.database import UserSession as DBUserSession
from app.services.auth_service import AuthService


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_supabase_user():
    """Mock Supabase user data."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "metadata": {"name": "Test User"}
    }


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""
    
    @patch('app.api.auth.get_db')
    @patch('app.services.auth_service.AuthService')
    async def test_login_success(self, mock_service_class, mock_db, client, mock_supabase_user):
        """Test successful login with JWT token."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mock_service.verify_jwt_token.return_value = mock_supabase_user
        mock_service.create_authenticated_session.return_value = "session-token-123"
        
        login_request = {
            "jwt_token": "valid-jwt-token",
            "preferences": {"theme": "dark"}
        }
        
        # Make request
        response = client.post("/api/v1/auth/login", json=login_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["session_token"] == "session-token-123"
        assert data["user_id"] == mock_supabase_user["user_id"]
        assert data["email"] == mock_supabase_user["email"]
        assert data["is_authenticated"] == True
        
        # Verify service calls
        mock_service.verify_jwt_token.assert_called_once_with("valid-jwt-token")
        mock_service.create_authenticated_session.assert_called_once()
    
    @patch('app.api.auth.get_db')
    @patch('app.services.auth_service.AuthService')
    async def test_login_invalid_token(self, mock_service_class, mock_db, client):
        """Test login with invalid JWT token."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mock_service.verify_jwt_token.return_value = None  # Invalid token
        
        login_request = {
            "jwt_token": "invalid-jwt-token",
            "preferences": {}
        }
        
        # Make request
        response = client.post("/api/v1/auth/login", json=login_request)
        
        # Assertions
        assert response.status_code == 401
        assert "Invalid JWT token" in response.json()["detail"]
    
    @patch('app.api.auth.get_db')
    @patch('app.services.auth_service.AuthService')
    async def test_create_anonymous_session(self, mock_service_class, mock_db, client):
        """Test creating anonymous session."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mock_service.create_anonymous_session.return_value = "anon-session-123"
        
        session_request = {
            "email": "test@example.com",
            "preferences": {"theme": "light"}
        }
        
        # Make request
        response = client.post("/api/v1/auth/anonymous", json=session_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["session_token"] == "anon-session-123"
        assert data["user_id"] is None
        assert data["email"] == "test@example.com"
        assert data["is_authenticated"] == False
        
        # Verify service call
        mock_service.create_anonymous_session.assert_called_once_with(
            email="test@example.com",
            preferences={"theme": "light"}
        )
    
    @patch('app.api.auth.get_auth_context')
    @patch('app.api.auth.get_db')
    @patch('app.services.auth_service.AuthService')
    async def test_logout(self, mock_service_class, mock_db, mock_auth_context, client):
        """Test logout functionality."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        from app.core.auth import AuthContext
        mock_auth_context.return_value = AuthContext(
            user_id="test-user-123",
            session_token="session-token-123",
            is_authenticated=True
        )
        
        # Make request
        response = client.post("/api/v1/auth/logout")
        
        # Assertions
        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]
        
        # Verify service call
        mock_service.revoke_session.assert_called_once_with("session-token-123")
    
    @patch('app.api.auth.get_auth_context')
    @patch('app.api.auth.get_db')
    @patch('app.services.auth_service.AuthService')
    async def test_refresh_session(self, mock_service_class, mock_db, mock_auth_context, client):
        """Test session refresh."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        from app.core.auth import AuthContext
        mock_auth_context.return_value = AuthContext(
            user_id="test-user-123",
            email="test@example.com",
            session_token="old-session-token",
            is_authenticated=True,
            preferences={"theme": "dark"}
        )
        
        mock_service.refresh_session.return_value = "new-session-token"
        
        # Make request
        response = client.post("/api/v1/auth/refresh")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["session_token"] == "new-session-token"
        assert data["user_id"] == "test-user-123"
        assert data["email"] == "test@example.com"
        
        # Verify service call
        mock_service.refresh_session.assert_called_once_with("old-session-token")
    
    @patch('app.api.auth.get_auth_context')
    async def test_get_current_user_info_authenticated(self, mock_auth_context, client):
        """Test getting current user info for authenticated user."""
        # Setup mock
        from app.core.auth import AuthContext
        mock_auth_context.return_value = AuthContext(
            user_id="test-user-123",
            email="test@example.com",
            is_authenticated=True,
            is_anonymous=False,
            preferences={"theme": "dark"}
        )
        
        # Make request
        response = client.get("/api/v1/auth/me")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-123"
        assert data["email"] == "test@example.com"
        assert data["is_authenticated"] == True
        assert data["is_anonymous"] == False
        assert data["preferences"]["theme"] == "dark"
    
    @patch('app.api.auth.get_auth_context')
    async def test_get_current_user_info_anonymous(self, mock_auth_context, client):
        """Test getting current user info for anonymous user."""
        # Setup mock
        from app.core.auth import AuthContext
        mock_auth_context.return_value = AuthContext(
            user_id=None,
            email=None,
            is_authenticated=False,
            is_anonymous=True,
            preferences={}
        )
        
        # Make request
        response = client.get("/api/v1/auth/me")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] is None
        assert data["email"] is None
        assert data["is_authenticated"] == False
        assert data["is_anonymous"] == True
    
    async def test_auth_health_check(self, client):
        """Test authentication health check endpoint."""
        response = client.get("/api/v1/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "supabase_configured" in data


class TestAuthService:
    """Test authentication service business logic."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def auth_service(self, mock_db_session):
        """Auth service with mocked database."""
        return AuthService(mock_db_session)
    
    async def test_create_anonymous_session(self, auth_service, mock_db_session):
        """Test creating anonymous session."""
        # Mock database operations
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        
        # Create session
        token = await auth_service.create_anonymous_session(
            email="test@example.com",
            preferences={"theme": "dark"}
        )
        
        # Assertions
        assert token is not None
        assert len(token) > 20  # Should be a reasonable length token
        
        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    async def test_verify_jwt_token_no_supabase(self, auth_service):
        """Test JWT token verification when Supabase is not configured."""
        # Auth service without Supabase client
        auth_service.supabase_client = None
        
        result = await auth_service.verify_jwt_token("some-token")
        
        assert result is None
    
    async def test_get_session_valid(self, auth_service, mock_db_session):
        """Test getting valid session."""
        # Mock database query
        mock_session = DBUserSession(
            session_token="test-token",
            user_id="test-user",
            email="test@example.com",
            expires_at=datetime.now() + timedelta(hours=1),
            is_active=True,
            last_accessed=datetime.now()
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()
        
        # Get session
        session = await auth_service.get_session("test-token")
        
        # Assertions
        assert session is not None
        assert session.session_token == "test-token"
        assert session.user_id == "test-user"
        
        # Verify database operations
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    async def test_get_session_expired(self, auth_service, mock_db_session):
        """Test getting expired session."""
        # Mock database query returning None (expired session filtered out)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Get session
        session = await auth_service.get_session("expired-token")
        
        # Assertions
        assert session is None
    
    async def test_revoke_session(self, auth_service, mock_db_session):
        """Test revoking a session."""
        # Mock database query
        mock_session = DBUserSession(
            session_token="test-token",
            user_id="test-user",
            is_active=True
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()
        
        # Revoke session
        result = await auth_service.revoke_session("test-token")
        
        # Assertions
        assert result == True
        assert mock_session.is_active == False
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
    
    async def test_cleanup_expired_sessions(self, auth_service, mock_db_session):
        """Test cleaning up expired sessions."""
        # Mock database update operation
        mock_result = MagicMock()
        mock_result.rowcount = 5  # 5 sessions cleaned up
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()
        
        # Cleanup sessions
        count = await auth_service.cleanup_expired_sessions()
        
        # Assertions
        assert count == 5
        
        # Verify database operations
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])