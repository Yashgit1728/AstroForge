"""
Authentication service for Supabase integration and session management.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from uuid import UUID, uuid4
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import jwt
try:
    from supabase import create_client, Client
    from gotrue.errors import AuthError
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    AuthError = Exception  # Fallback for type hints

from ..core.config import settings
from ..models.database import UserSession as DBUserSession

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Authentication related errors."""
    pass


class AuthService:
    """Service for handling authentication and session management."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize auth service with database session."""
        self.db = db_session
        self.supabase_client = None
        
        # Initialize Supabase client if credentials are available
        if SUPABASE_AVAILABLE and settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
            try:
                self.supabase_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_ANON_KEY
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {e}")
        elif not SUPABASE_AVAILABLE:
            logger.warning("Supabase client not available - install supabase-py for full authentication support")
    
    async def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token from Supabase.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            if not self.supabase_client:
                logger.warning("Supabase client not initialized")
                return None
            
            # Verify token with Supabase
            user = self.supabase_client.auth.get_user(token)
            
            if user and user.user:
                return {
                    "user_id": user.user.id,
                    "email": user.user.email,
                    "metadata": user.user.user_metadata
                }
            
            return None
            
        except AuthError as e:
            logger.warning(f"JWT token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying JWT token: {e}")
            return None
    
    async def create_anonymous_session(
        self,
        email: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an anonymous session for users who don't want to authenticate.
        
        Args:
            email: Optional email for session recovery
            preferences: Optional user preferences
            
        Returns:
            Session token
        """
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=30)  # 30-day anonymous sessions
            
            db_session = DBUserSession(
                session_token=session_token,
                user_id=None,  # Anonymous
                email=email,
                expires_at=expires_at,
                is_active=True,
                preferences=preferences or {}
            )
            
            self.db.add(db_session)
            await self.db.commit()
            
            logger.info(f"Created anonymous session with token {session_token[:8]}...")
            
            return session_token
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create anonymous session: {e}")
            raise AuthenticationError(f"Failed to create session: {str(e)}")
    
    async def create_authenticated_session(
        self,
        user_id: str,
        email: str,
        jwt_token: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an authenticated session for logged-in users.
        
        Args:
            user_id: Supabase user ID
            email: User email
            jwt_token: JWT token from Supabase
            preferences: Optional user preferences
            
        Returns:
            Session token
        """
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
            # Deactivate any existing sessions for this user
            await self._deactivate_user_sessions(user_id)
            
            db_session = DBUserSession(
                session_token=session_token,
                user_id=user_id,
                email=email,
                expires_at=expires_at,
                is_active=True,
                preferences=preferences or {}
            )
            
            self.db.add(db_session)
            await self.db.commit()
            
            logger.info(f"Created authenticated session for user {user_id}")
            
            return session_token
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create authenticated session: {e}")
            raise AuthenticationError(f"Failed to create session: {str(e)}")
    
    async def get_session(self, session_token: str) -> Optional[DBUserSession]:
        """
        Get session by token.
        
        Args:
            session_token: Session token
            
        Returns:
            Session object if valid and active, None otherwise
        """
        try:
            query = select(DBUserSession).where(
                and_(
                    DBUserSession.session_token == session_token,
                    DBUserSession.is_active == True,
                    DBUserSession.expires_at > datetime.now()
                )
            )
            
            result = await self.db.execute(query)
            session = result.scalar_one_or_none()
            
            if session:
                # Update last accessed time
                session.last_accessed = datetime.now()
                await self.db.commit()
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    async def refresh_session(self, session_token: str) -> Optional[str]:
        """
        Refresh an existing session.
        
        Args:
            session_token: Current session token
            
        Returns:
            New session token if successful, None otherwise
        """
        try:
            session = await self.get_session(session_token)
            
            if not session:
                return None
            
            # Create new session token
            new_token = secrets.token_urlsafe(32)
            new_expires_at = datetime.now() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
            # Update session
            session.session_token = new_token
            session.expires_at = new_expires_at
            session.last_accessed = datetime.now()
            
            await self.db.commit()
            
            logger.info(f"Refreshed session for user {session.user_id or 'anonymous'}")
            
            return new_token
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to refresh session: {e}")
            return None
    
    async def revoke_session(self, session_token: str) -> bool:
        """
        Revoke a session (logout).
        
        Args:
            session_token: Session token to revoke
            
        Returns:
            True if revoked successfully, False otherwise
        """
        try:
            query = select(DBUserSession).where(
                DBUserSession.session_token == session_token
            )
            
            result = await self.db.execute(query)
            session = result.scalar_one_or_none()
            
            if session:
                session.is_active = False
                await self.db.commit()
                
                logger.info(f"Revoked session for user {session.user_id or 'anonymous'}")
                return True
            
            return False
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to revoke session: {e}")
            return False
    
    async def revoke_all_user_sessions(self, user_id: str) -> int:
        """
        Revoke all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions revoked
        """
        try:
            return await self._deactivate_user_sessions(user_id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to revoke user sessions: {e}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            from sqlalchemy import update
            
            # Deactivate expired sessions
            stmt = update(DBUserSession).where(
                and_(
                    DBUserSession.expires_at < datetime.now(),
                    DBUserSession.is_active == True
                )
            ).values(is_active=False)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            count = result.rowcount
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            
            return count
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    async def _deactivate_user_sessions(self, user_id: str) -> int:
        """
        Deactivate all active sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions deactivated
        """
        from sqlalchemy import update
        
        stmt = update(DBUserSession).where(
            and_(
                DBUserSession.user_id == user_id,
                DBUserSession.is_active == True
            )
        ).values(is_active=False)
        
        result = await self.db.execute(stmt)
        return result.rowcount


# Export service
__all__ = ['AuthService', 'AuthenticationError']