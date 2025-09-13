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

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio


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
    
    def test_login_success(self, client, mock_supabase_user):
        """Test successful login with JWT token."""
        with patch('app.api.auth.get_db') as mock_get_db, \
             patch('app.services.auth_service.AuthService') as mock_service_class:
            
            # Setup mocks
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
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
    
    def test_create_anonymous_session(self, client):
        """Test creating anonymous session."""
        with patch('app.api.auth.get_db') as mock_get_db, \
             patch('app.services.auth_service.AuthService') as mock_service_class:
            
            # Setup mocks
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
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
    
    @patch('app.api.auth.get_auth_context')
    @patch('app.api.auth.get_db')
    @patch('app.services.auth_service.AuthService')
    async def test_update_preferences(self, mock_service_class, mock_db, mock_auth_context, client):
        """Test updating user preferences."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        from app.core.auth import AuthContext
        mock_auth_context.return_value = AuthContext(
            user_id="test-user-123",
            session_token="session-token-123",
            is_authenticated=True
        )
        
        mock_service.update_session_preferences.return_value = True
        
        preferences = {"theme": "dark", "language": "en"}
        
        # Make request
        response = client.post("/api/v1/auth/preferences", json=preferences)
        
        # Assertions
        assert response.status_code == 200
        assert "Preferences updated successfully" in response.json()["message"]
        
        # Verify service call
        mock_service.update_session_preferences.assert_called_once_with(
            "session-token-123",
            preferences
        )
    
    @patch('app.api.auth.require_authentication')
    @patch('app.api.auth.get_db')
    @patch('app.services.auth_service.AuthService')
    async def test_get_user_sessions(self, mock_service_class, mock_db, mock_require_auth, client):
        """Test getting user sessions."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_require_auth.return_value = "test-user-123"
        
        # Mock session data
        mock_session = MagicMock()
        mock_session.session_token = "session-token-123456789"
        mock_session.created_at = datetime.now()
        mock_session.last_accessed = datetime.now()
        mock_session.expires_at = datetime.now() + timedelta(hours=1)
        
        mock_service.get_user_sessions.return_value = [mock_session]
        
        # Make request
        response = client.get("/api/v1/auth/sessions")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total_count" in data
        assert data["total_count"] == 1
        assert len(data["sessions"]) == 1
        
        # Verify service call
        mock_service.get_user_sessions.assert_called_once_with("test-user-123")
    
    @patch('app.api.auth.get_db')
    @patch('app.services.auth_service.AuthService')
    async def test_validate_session(self, mock_service_class, mock_db, client):
        """Test session validation endpoint."""
        # Setup mocks
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        mock_service.validate_session_token.return_value = True
        
        # Make request
        response = client.post("/api/v1/auth/validate", json="valid-session-token")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        
        # Verify service call
        mock_service.validate_session_token.assert_called_once_with("valid-session-token")
    
    async def test_auth_health_check(self, client):
        """Test authentication health check endpoint."""
        response = client.get("/api/v1/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "supabase_configured" in data
        assert "jwt_secret_configured" in data
        assert "environment" in data


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
    
    async def test_validate_session_token_valid(self, auth_service, mock_db_session):
        """Test validating a valid session token."""
        # Mock get_session to return a valid session
        with patch.object(auth_service, 'get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_session.is_active = True
            mock_get_session.return_value = mock_session
            
            # Validate session
            is_valid = await auth_service.validate_session_token("valid-token")
            
            # Assertions
            assert is_valid == True
            mock_get_session.assert_called_once_with("valid-token")
    
    async def test_validate_session_token_invalid(self, auth_service, mock_db_session):
        """Test validating an invalid session token."""
        # Mock get_session to return None
        with patch.object(auth_service, 'get_session') as mock_get_session:
            mock_get_session.return_value = None
            
            # Validate session
            is_valid = await auth_service.validate_session_token("invalid-token")
            
            # Assertions
            assert is_valid == False
            mock_get_session.assert_called_once_with("invalid-token")
    
    async def test_get_user_sessions(self, auth_service, mock_db_session):
        """Test getting user sessions."""
        # Mock database query
        mock_session1 = DBUserSession(
            session_token="token1",
            user_id="test-user",
            is_active=True,
            expires_at=datetime.now() + timedelta(hours=1)
        )
        mock_session2 = DBUserSession(
            session_token="token2",
            user_id="test-user",
            is_active=True,
            expires_at=datetime.now() + timedelta(hours=2)
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_session1, mock_session2]
        mock_db_session.execute.return_value = mock_result
        
        # Get sessions
        sessions = await auth_service.get_user_sessions("test-user")
        
        # Assertions
        assert len(sessions) == 2
        assert sessions[0].session_token == "token1"
        assert sessions[1].session_token == "token2"
        
        # Verify database operations
        mock_db_session.execute.assert_called_once()
    
    async def test_update_session_preferences(self, auth_service, mock_db_session):
        """Test updating session preferences."""
        # Mock get_session to return a valid session
        mock_session = DBUserSession(
            session_token="test-token",
            user_id="test-user",
            preferences={"theme": "light"}
        )
        
        with patch.object(auth_service, 'get_session') as mock_get_session:
            mock_get_session.return_value = mock_session
            mock_db_session.commit = AsyncMock()
            
            # Update preferences
            new_prefs = {"language": "en", "theme": "dark"}
            success = await auth_service.update_session_preferences("test-token", new_prefs)
            
            # Assertions
            assert success == True
            assert mock_session.preferences["theme"] == "dark"
            assert mock_session.preferences["language"] == "en"
            
            # Verify database operations
            mock_get_session.assert_called_once_with("test-token")
            mock_db_session.commit.assert_called_once()
    
    async def test_jwt_fallback_verification_with_secret(self, auth_service):
        """Test JWT fallback verification with secret key."""
        # Mock settings to have JWT secret
        with patch('app.services.auth_service.settings') as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test-secret"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.ENVIRONMENT = "production"
            
            # Create a test JWT token
            import jwt
            payload = {
                "sub": "test-user-123",
                "email": "test@example.com",
                "user_metadata": {"name": "Test User"},
                "aud": "authenticated",
                "role": "authenticated"
            }
            token = jwt.encode(payload, "test-secret", algorithm="HS256")
            
            # Verify token
            result = await auth_service._verify_jwt_fallback(token)
            
            # Assertions
            assert result is not None
            assert result["user_id"] == "test-user-123"
            assert result["email"] == "test@example.com"
            assert result["role"] == "authenticated"
    
    async def test_jwt_fallback_verification_development(self, auth_service):
        """Test JWT fallback verification in development mode."""
        # Mock settings for development
        with patch('app.services.auth_service.settings') as mock_settings:
            mock_settings.JWT_SECRET_KEY = ""
            mock_settings.ENVIRONMENT = "development"
            
            # Create a test JWT token (will be decoded without verification)
            import jwt
            payload = {
                "sub": "test-user-123",
                "email": "test@example.com",
                "user_metadata": {"name": "Test User"}
            }
            token = jwt.encode(payload, "any-secret", algorithm="HS256")
            
            # Verify token
            result = await auth_service._verify_jwt_fallback(token)
            
            # Assertions
            assert result is not None
            assert result["user_id"] == "test-user-123"
            assert result["email"] == "test@example.com"


if __name__ == "__main__":
    pytest.main([__file__])