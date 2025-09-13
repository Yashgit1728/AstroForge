"""
Authentication API endpoints for login, logout, and session management.
"""
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..core.auth import get_auth_context, AuthContext, require_authentication
from ..services.auth_service import AuthService, AuthenticationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)


# Request/Response schemas
class LoginRequest(BaseModel):
    """Request schema for login with JWT token."""
    jwt_token: str = Field(..., description="JWT token from Supabase")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AnonymousSessionRequest(BaseModel):
    """Request schema for creating anonymous session."""
    email: Optional[str] = Field(None, description="Optional email for session recovery")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """Response schema for session information."""
    session_token: str
    user_id: Optional[str]
    email: Optional[str]
    is_authenticated: bool
    expires_at: Optional[datetime]
    preferences: Dict[str, Any]


class UserInfoResponse(BaseModel):
    """Response schema for user information."""
    user_id: Optional[str]
    email: Optional[str]
    is_authenticated: bool
    is_anonymous: bool
    preferences: Dict[str, Any]


@router.post("/login", response_model=SessionResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """
    Login with Supabase JWT token and create session.
    
    This endpoint accepts a JWT token from Supabase authentication
    and creates a local session for the user.
    """
    try:
        auth_service = AuthService(db)
        
        # Verify JWT token
        jwt_payload = await auth_service.verify_jwt_token(request.jwt_token)
        if not jwt_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT token"
            )
        
        # Create authenticated session
        session_token = await auth_service.create_authenticated_session(
            user_id=jwt_payload["user_id"],
            email=jwt_payload.get("email"),
            jwt_token=request.jwt_token,
            preferences=request.preferences
        )
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=30 * 24 * 60 * 60  # 30 days
        )
        
        logger.info(f"User {jwt_payload['user_id']} logged in successfully")
        
        return SessionResponse(
            session_token=session_token,
            user_id=jwt_payload["user_id"],
            email=jwt_payload.get("email"),
            is_authenticated=True,
            expires_at=None,  # Will be set by the service
            preferences=request.preferences
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/anonymous", response_model=SessionResponse)
async def create_anonymous_session(
    request: AnonymousSessionRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """
    Create an anonymous session for users who don't want to authenticate.
    
    Anonymous sessions allow users to save missions temporarily and
    optionally provide an email for session recovery.
    """
    try:
        auth_service = AuthService(db)
        
        # Create anonymous session
        session_token = await auth_service.create_anonymous_session(
            email=request.email,
            preferences=request.preferences
        )
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=30 * 24 * 60 * 60  # 30 days
        )
        
        logger.info("Anonymous session created successfully")
        
        return SessionResponse(
            session_token=session_token,
            user_id=None,
            email=request.email,
            is_authenticated=False,
            expires_at=None,  # Will be set by the service
            preferences=request.preferences
        )
        
    except AuthenticationError as e:
        logger.error(f"Error creating anonymous session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating anonymous session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/logout")
async def logout(
    response: Response,
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Logout and revoke current session.
    
    This endpoint revokes the current session and clears the session cookie.
    """
    try:
        if auth_context.session_token:
            auth_service = AuthService(db)
            await auth_service.revoke_session(auth_context.session_token)
        
        # Clear session cookie
        response.delete_cookie(
            key="session_token",
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        logger.info(f"User {auth_context.user_id or 'anonymous'} logged out")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/refresh", response_model=SessionResponse)
async def refresh_session(
    response: Response,
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """
    Refresh current session to extend expiration.
    
    This endpoint creates a new session token with extended expiration
    for the current user.
    """
    try:
        if not auth_context.session_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No active session to refresh"
            )
        
        auth_service = AuthService(db)
        new_token = await auth_service.refresh_session(auth_context.session_token)
        
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh session"
            )
        
        # Set new session cookie
        response.set_cookie(
            key="session_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=30 * 24 * 60 * 60  # 30 days
        )
        
        logger.info(f"Session refreshed for user {auth_context.user_id or 'anonymous'}")
        
        return SessionResponse(
            session_token=new_token,
            user_id=auth_context.user_id,
            email=auth_context.email,
            is_authenticated=auth_context.is_authenticated,
            expires_at=None,  # Will be updated by the service
            preferences=auth_context.preferences
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    auth_context: AuthContext = Depends(get_auth_context)
) -> UserInfoResponse:
    """
    Get current user information.
    
    Returns information about the currently authenticated user or
    anonymous session.
    """
    return UserInfoResponse(
        user_id=auth_context.user_id,
        email=auth_context.email,
        is_authenticated=auth_context.is_authenticated,
        is_anonymous=auth_context.is_anonymous,
        preferences=auth_context.preferences
    )


@router.post("/logout-all")
async def logout_all_sessions(
    user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Logout from all sessions for the current user.
    
    This endpoint revokes all active sessions for the authenticated user.
    Requires authentication.
    """
    try:
        auth_service = AuthService(db)
        count = await auth_service.revoke_all_user_sessions(user_id)
        
        logger.info(f"Revoked {count} sessions for user {user_id}")
        
        return {"message": f"Logged out from {count} sessions"}
        
    except Exception as e:
        logger.error(f"Error logging out all sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/preferences")
async def update_preferences(
    preferences: Dict[str, Any],
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Update user preferences for the current session.
    
    This endpoint allows users to update their preferences which are
    stored with their session.
    """
    try:
        if not auth_context.session_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No active session"
            )
        
        auth_service = AuthService(db)
        success = await auth_service.update_session_preferences(
            auth_context.session_token,
            preferences
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update preferences"
            )
        
        logger.info(f"Updated preferences for user {auth_context.user_id or 'anonymous'}")
        
        return {"message": "Preferences updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/sessions")
async def get_user_sessions(
    user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all active sessions for the current user.
    
    This endpoint returns information about all active sessions
    for the authenticated user.
    """
    try:
        auth_service = AuthService(db)
        sessions = await auth_service.get_user_sessions(user_id)
        
        session_info = []
        for session in sessions:
            session_info.append({
                "session_token": session.session_token[:8] + "...",  # Partial token for security
                "created_at": session.created_at,
                "last_accessed": session.last_accessed,
                "expires_at": session.expires_at,
                "is_current": session.session_token == getattr(
                    # Get current session token from context if available
                    # This is a simplified check - in practice you'd compare with request context
                    None, "session_token", None
                )
            })
        
        return {
            "sessions": session_info,
            "total_count": len(session_info)
        }
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


class SessionValidationRequest(BaseModel):
    """Request schema for session validation."""
    session_token: str = Field(..., description="Session token to validate")


@router.post("/validate")
async def validate_session(
    request: SessionValidationRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, bool]:
    """
    Validate a session token.
    
    This endpoint checks if a session token is valid and active.
    Useful for client-side session validation.
    """
    try:
        auth_service = AuthService(db)
        is_valid = await auth_service.validate_session_token(request.session_token)
        
        return {"valid": is_valid}
        
    except Exception as e:
        logger.error(f"Error validating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/health")
async def auth_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for authentication service.
    
    Returns the status of authentication-related services.
    """
    from ..core.config import settings
    
    status_info = {
        "status": "healthy",
        "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY),
        "jwt_secret_configured": bool(settings.JWT_SECRET_KEY),
        "environment": settings.ENVIRONMENT
    }
    
    return status_info


# Export router
__all__ = ['router']