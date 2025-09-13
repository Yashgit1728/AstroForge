"""
Authentication middleware and dependencies for FastAPI.
"""
import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from ..services.auth_service import AuthService, AuthenticationError
from ..models.database import UserSession

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class AuthContext:
    """Authentication context for the current request."""
    
    def __init__(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        session_token: Optional[str] = None,
        is_authenticated: bool = False,
        is_anonymous: bool = False,
        preferences: Optional[Dict[str, Any]] = None
    ):
        self.user_id = user_id
        self.email = email
        self.session_token = session_token
        self.is_authenticated = is_authenticated
        self.is_anonymous = is_anonymous
        self.preferences = preferences or {}


async def get_auth_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> AuthContext:
    """
    Get authentication context for the current request.
    
    This dependency checks for authentication in the following order:
    1. JWT token in Authorization header (Supabase auth)
    2. Session token in Authorization header (our session system)
    3. Session token in cookies
    4. Anonymous access (no authentication)
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        AuthContext with user information
    """
    auth_service = AuthService(db)
    
    # Try JWT token authentication (Supabase)
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
        
        # First try as JWT token
        jwt_payload = await auth_service.verify_jwt_token(token)
        if jwt_payload:
            return AuthContext(
                user_id=jwt_payload["user_id"],
                email=jwt_payload.get("email"),
                session_token=None,
                is_authenticated=True,
                is_anonymous=False,
                preferences=jwt_payload.get("metadata", {})
            )
        
        # Then try as session token
        session = await auth_service.get_session(token)
        if session:
            return AuthContext(
                user_id=session.user_id,
                email=session.email,
                session_token=session.session_token,
                is_authenticated=session.user_id is not None,
                is_anonymous=session.user_id is None,
                preferences=session.preferences
            )
    
    # Try session token in cookies
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await auth_service.get_session(session_token)
        if session:
            return AuthContext(
                user_id=session.user_id,
                email=session.email,
                session_token=session.session_token,
                is_authenticated=session.user_id is not None,
                is_anonymous=session.user_id is None,
                preferences=session.preferences
            )
    
    # No authentication - anonymous access
    return AuthContext(
        user_id=None,
        email=None,
        session_token=None,
        is_authenticated=False,
        is_anonymous=True,
        preferences={}
    )


async def get_current_user(
    auth_context: AuthContext = Depends(get_auth_context)
) -> Optional[str]:
    """
    Get current user ID from authentication context.
    
    Args:
        auth_context: Authentication context
        
    Returns:
        User ID if authenticated, None otherwise
    """
    return auth_context.user_id


async def require_authentication(
    auth_context: AuthContext = Depends(get_auth_context)
) -> str:
    """
    Require authentication for the current request.
    
    Args:
        auth_context: Authentication context
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not auth_context.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return auth_context.user_id


async def get_optional_user(
    auth_context: AuthContext = Depends(get_auth_context)
) -> Optional[str]:
    """
    Get current user ID, allowing anonymous access.
    
    Args:
        auth_context: Authentication context
        
    Returns:
        User ID if authenticated, None for anonymous users
    """
    return auth_context.user_id if auth_context.is_authenticated else None


class AuthMiddleware:
    """Authentication middleware for session cleanup and management."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation."""
        # For now, just pass through to the app
        # In the future, we could add session cleanup logic here
        await self.app(scope, receive, send)


# Export dependencies and classes
__all__ = [
    'AuthContext',
    'get_auth_context',
    'get_current_user',
    'require_authentication',
    'get_optional_user',
    'AuthMiddleware'
]