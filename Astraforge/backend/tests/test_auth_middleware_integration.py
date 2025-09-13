"""
Integration tests for authentication middleware.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import AuthMiddleware, JWTValidationMiddleware, get_auth_context, AuthContext


def test_middleware_integration_complete():
    """Test that middleware integration is complete and working."""
    # Test that middleware classes are properly imported and available
    assert AuthMiddleware is not None
    assert JWTValidationMiddleware is not None
    assert get_auth_context is not None
    assert AuthContext is not None
    
    # Test that the app has middleware configured
    middleware_types = [type(middleware) for middleware in app.user_middleware]
    middleware_names = [middleware.__class__.__name__ for middleware in app.user_middleware]
    
    # Check that our auth middleware is present
    assert any('AuthMiddleware' in name for name in middleware_names), f"AuthMiddleware not found in {middleware_names}"
    assert any('JWTValidationMiddleware' in name for name in middleware_names), f"JWTValidationMiddleware not found in {middleware_names}"
    
    print("✅ Authentication middleware integration is complete!")


def test_auth_endpoints_available():
    """Test that authentication endpoints are available."""
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/api/v1/auth/health")
    assert response.status_code == 200
    
    # Test me endpoint (should work for anonymous users)
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert "is_authenticated" in data
    assert "is_anonymous" in data
    
    print("✅ Authentication endpoints are working!")


def test_middleware_handles_requests():
    """Test that middleware properly handles requests."""
    client = TestClient(app)
    
    # Make a request that should go through middleware
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    
    # The response should indicate anonymous access
    data = response.json()
    assert data["is_authenticated"] == False
    assert data["is_anonymous"] == True
    assert data["user_id"] is None
    
    print("✅ Middleware is handling requests correctly!")


if __name__ == "__main__":
    pytest.main([__file__])