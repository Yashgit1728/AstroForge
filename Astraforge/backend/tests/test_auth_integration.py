"""
Integration tests for authentication system.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import jwt

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.database import UserSession as DBUserSession
from app.services.auth_service import AuthService
from app.core.auth import get_auth_context, AuthContext

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session fixture."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    return mock_session


@pytest.fixture
def mock_supabase_jwt():
    """Mock Supabase JWT token."""
    payload = {
        "sub": "test-user-123",
        "email": "test@example.com",
        "user_metadata": {"name": "Test User"},
        "aud": "authenticated",
        "role": "authenticated",
        "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.now().timestamp())
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


class TestAuthenticationIntegration:
    """Integration tests for authentication system."""
    
    async def test_jwt_authentication_flow(self, client, mock_supabase_jwt, mock_db_session):
        """Test JWT authentication flow."""
        from app.core.database import get_db
        
        # Mock the database dependency
        async def mock_get_db():
            yield mock_db_session
        
        # Override the dependency
        app.dependency_overrides[get_db] = mock_get_db
        
        try:
            with patch('app.services.auth_service.AuthService') as mock_service_class:
                # Setup service mock
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                # Mock JWT verification
                jwt_payload = {
                    "user_id": "test-user-123",
                    "email": "test@example.com",
                    "metadata": {"name": "Test User"}
                }
                mock_service.verify_jwt_token.return_value = jwt_payload
                mock_service.create_authenticated_session.return_value = "session-token-123"
                
                # Test login with JWT token
                login_request = {
                    "jwt_token": mock_supabase_jwt,
                    "preferences": {"theme": "dark"}
                }
                
                login_response = client.post("/api/v1/auth/login", json=login_request)
                assert login_response.status_code == 200
                
                login_data = login_response.json()
                assert login_data["user_id"] == "test-user-123"
                assert login_data["is_authenticated"] == True
                assert "session_token" in login_data
                assert len(login_data["session_token"]) > 20  # Verify it's a proper token
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    async def test_user_info_endpoint(self, client):
        """Test user info endpoint with mocked auth context."""
        from app.core.auth import get_auth_context
        
        def mock_auth_context():
            return AuthContext(
                user_id="test-user-123",
                email="test@example.com",
                session_token="session-token-123",
                is_authenticated=True,
                preferences={"theme": "dark"}
            )
        
        app.dependency_overrides[get_auth_context] = mock_auth_context
        
        try:
            me_response = client.get("/api/v1/auth/me")
            assert me_response.status_code == 200
            
            me_data = me_response.json()
            assert me_data["user_id"] == "test-user-123"
            assert me_data["email"] == "test@example.com"
            assert me_data["is_authenticated"] == True
        finally:
            app.dependency_overrides.clear()

    
    async def test_anonymous_session_flow(self, client, mock_db_session):
        """Test anonymous session creation and usage."""
        from app.core.database import get_db
        
        # Mock the database dependency
        async def mock_get_db():
            yield mock_db_session
        
        # Override the dependency
        app.dependency_overrides[get_db] = mock_get_db
        
        try:
            with patch('app.services.auth_service.AuthService') as mock_service_class:
                # Setup service mock
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.create_anonymous_session.return_value = "anon-session-123"
                
                # Step 1: Create anonymous session
                anon_request = {
                    "email": "temp@example.com",
                    "preferences": {"theme": "light"}
                }
                
                anon_response = client.post("/api/v1/auth/anonymous", json=anon_request)
                assert anon_response.status_code == 200
                
                anon_data = anon_response.json()
                assert anon_data["user_id"] is None
                assert anon_data["email"] == "temp@example.com"
                assert anon_data["is_authenticated"] == False
                
                # Step 2: Use anonymous session
                from app.core.auth import get_auth_context
                
                def mock_auth_context():
                    return AuthContext(
                        user_id=None,
                        email="temp@example.com",
                        session_token="anon-session-123",
                        is_authenticated=False,
                        is_anonymous=True,
                        preferences={"theme": "light"}
                    )
                
                app.dependency_overrides[get_auth_context] = mock_auth_context
                
                me_response = client.get("/api/v1/auth/me")
                assert me_response.status_code == 200
                
                me_data = me_response.json()
                assert me_data["user_id"] is None
                assert me_data["email"] == "temp@example.com"
                assert me_data["is_authenticated"] == False
                assert me_data["is_anonymous"] == True
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    
    async def test_session_refresh_flow(self, client, mock_db_session):
        """Test session refresh functionality."""
        from app.core.database import get_db
        from app.core.auth import get_auth_context
        
        # Mock the database dependency
        async def mock_get_db():
            yield mock_db_session
        
        # Mock auth context dependency
        def mock_auth_context():
            return AuthContext(
                user_id="test-user-123",
                email="test@example.com",
                session_token="old-session-token",
                is_authenticated=True,
                preferences={"theme": "dark"}
            )
        
        # Override the dependencies
        app.dependency_overrides[get_db] = mock_get_db
        app.dependency_overrides[get_auth_context] = mock_auth_context
        
        try:
            with patch('app.services.auth_service.AuthService') as mock_service_class:
                
                # Setup service mock
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.refresh_session.return_value = "new-session-token"
                
                refresh_response = client.post("/api/v1/auth/refresh")
                assert refresh_response.status_code == 200
                
                refresh_data = refresh_response.json()
                assert refresh_data["session_token"] == "new-session-token"
                assert refresh_data["user_id"] == "test-user-123"
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    async def test_authentication_middleware_integration(self, client):
        """Test that authentication middleware is properly integrated."""
        # Test that the middleware doesn't break normal requests
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test auth health check
        auth_health_response = client.get("/api/v1/auth/health")
        assert auth_health_response.status_code == 200
        
        health_data = auth_health_response.json()
        assert "status" in health_data
        assert "supabase_configured" in health_data
        assert "jwt_secret_configured" in health_data
    
    async def test_invalid_jwt_token_handling(self, client, mock_db_session):
        """Test handling of invalid JWT tokens."""
        from app.core.database import get_db
        
        # Mock the database dependency
        async def mock_get_db():
            yield mock_db_session
        
        # Override the dependency
        app.dependency_overrides[get_db] = mock_get_db
        
        try:
            with patch('app.services.auth_service.AuthService') as mock_service_class:
                # Setup service mock
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.verify_jwt_token.return_value = None  # Invalid token
                
                # Try to login with invalid token
                login_request = {
                    "jwt_token": "invalid-jwt-token",
                    "preferences": {}
                }
                
                login_response = client.post("/api/v1/auth/login", json=login_request)
                assert login_response.status_code == 401
                assert "Invalid JWT token" in login_response.json()["detail"]
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    async def test_session_validation_endpoint(self, client, mock_db_session):
        """Test session validation endpoint."""
        from app.core.database import get_db
        
        # Mock the database dependency
        async def mock_get_db():
            yield mock_db_session
        
        # Override the dependency
        app.dependency_overrides[get_db] = mock_get_db
        
        try:
            with patch('app.services.auth_service.AuthService') as mock_service_class:
                # Setup service mock
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                # Test valid session - mock the get_session method properly
                mock_session = MagicMock()
                mock_session.session_token = "valid-session-token"
                mock_session.is_active = True
                mock_session.expires_at = datetime.now() + timedelta(hours=1)
                mock_session.last_accessed = datetime.now()
                mock_service.get_session.return_value = mock_session
                mock_service.validate_session_token.return_value = True
                
                valid_response = client.post("/api/v1/auth/validate", json={"session_token": "valid-session-token"})
                assert valid_response.status_code == 200
                assert valid_response.json()["valid"] == True
                
                # Test invalid session
                mock_service.get_session.return_value = None
                mock_service.validate_session_token.return_value = False
                
                invalid_response = client.post("/api/v1/auth/validate", json={"session_token": "invalid-session-token"})
                assert invalid_response.status_code == 200
                assert invalid_response.json()["valid"] == False
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    async def test_protected_endpoint_access(self, client, mock_db_session):
        """Test access to protected endpoints."""
        from app.core.database import get_db
        from app.core.auth import require_authentication
        
        # Mock the database dependency
        async def mock_get_db():
            yield mock_db_session
        
        # Mock authentication requirement
        async def mock_require_auth():
            return "test-user-123"
        
        # Override the dependencies
        app.dependency_overrides[get_db] = mock_get_db
        app.dependency_overrides[require_authentication] = mock_require_auth
        
        try:
            with patch('app.services.auth_service.AuthService') as mock_service_class:
                
                # Setup service mock
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                # Mock user sessions
                mock_session = MagicMock()
                mock_session.session_token = "session-token-123456789"
                mock_session.created_at = datetime.now()
                mock_session.last_accessed = datetime.now()
                mock_session.expires_at = datetime.now() + timedelta(hours=1)
                
                mock_service.get_user_sessions.return_value = [mock_session]
                
                # Access protected endpoint
                sessions_response = client.get("/api/v1/auth/sessions")
                assert sessions_response.status_code == 200
                
                sessions_data = sessions_response.json()
                assert "sessions" in sessions_data
                assert "total_count" in sessions_data
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()


class TestAuthServiceIntegration:
    """Integration tests for AuthService."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def auth_service(self, mock_db_session):
        """Auth service with mocked database."""
        return AuthService(mock_db_session)
    
    async def test_session_lifecycle(self, auth_service, mock_db_session):
        """Test complete session lifecycle."""
        # Mock database operations
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        
        # Create anonymous session
        anon_token = await auth_service.create_anonymous_session(
            email="test@example.com",
            preferences={"theme": "dark"}
        )
        
        assert anon_token is not None
        assert len(anon_token) > 20
        
        # Mock session retrieval
        mock_session = DBUserSession(
            session_token=anon_token,
            user_id=None,
            email="test@example.com",
            expires_at=datetime.now() + timedelta(hours=1),
            is_active=True,
            preferences={"theme": "dark"}
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db_session.execute.return_value = mock_result
        
        # Get session
        retrieved_session = await auth_service.get_session(anon_token)
        assert retrieved_session is not None
        assert retrieved_session.email == "test@example.com"
        
        # Update preferences
        success = await auth_service.update_session_preferences(
            anon_token,
            {"language": "en"}
        )
        assert success == True
        
        # Revoke session
        revoked = await auth_service.revoke_session(anon_token)
        assert revoked == True
    
    async def test_jwt_verification_integration(self, auth_service):
        """Test JWT verification with different scenarios."""
        # Test with no Supabase client
        auth_service.supabase_client = None
        
        # Create a test JWT token
        payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "user_metadata": {"name": "Test User"},
            "aud": "authenticated",
            "role": "authenticated"
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        # Test fallback verification
        with patch('app.services.auth_service.settings') as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test-secret"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.ENVIRONMENT = "production"
            
            result = await auth_service.verify_jwt_token(token)
            
            assert result is not None
            assert result["user_id"] == "test-user-123"
            assert result["email"] == "test@example.com"


if __name__ == "__main__":
    pytest.main([__file__])