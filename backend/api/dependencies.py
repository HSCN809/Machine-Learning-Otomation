"""
Dependencies and session management for FastAPI
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import pandas as pd
from fastapi import Cookie, Depends, HTTPException, Header, status
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.database import SessionLocal
from backend.modules.auth.models import AuthSession, User
from backend.modules.auth.security import hash_session_token
from backend.modules.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """In-memory session manager for storing DataFrames"""
    
    def __init__(self, timeout_minutes: int = 60):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.timeout = timedelta(minutes=timeout_minutes)
    
    def create_session(self) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "data": None,
            "original_data": None,
            "history": [],
            "history_snapshots": [],
            "metadata": {},
        }
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        session = self._sessions.get(session_id)
        if session:
            session["last_accessed"] = datetime.now()
        return session
    
    def set_dataframe(self, session_id: str, df: pd.DataFrame, is_original: bool = False):
        """Store DataFrame in session"""
        session = self.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session["data"] = df
        if is_original:
            session["original_data"] = df.copy()
            session["history"] = []
            session["history_snapshots"] = []
        
        logger.info(f"Session {session_id}: DataFrame set with shape {df.shape}")
    
    def get_dataframe(self, session_id: str) -> Optional[pd.DataFrame]:
        """Get DataFrame from session"""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.get("data")
    
    def get_original_dataframe(self, session_id: str) -> Optional[pd.DataFrame]:
        """Get original DataFrame from session"""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.get("original_data")
    
    def add_history(self, session_id: str, action: Dict[str, Any]):
        """Add action to session history"""
        session = self.get_session(session_id)
        if session:
            action["timestamp"] = datetime.now().isoformat()
            session["history"].append(action)

    def add_history_snapshot(self, session_id: str, df: pd.DataFrame):
        """Store pre-action snapshot for undo operations"""
        session = self.get_session(session_id)
        if session:
            session["history_snapshots"].append(df.copy(deep=True))
    
    def get_history(self, session_id: str) -> list:
        """Get session history"""
        session = self.get_session(session_id)
        return session.get("history", []) if session else []

    def undo_last_history_action(self, session_id: str) -> Dict[str, Any]:
        """Restore the dataframe snapshot before the last preprocessing action"""
        session = self.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        history = session.get("history", [])
        snapshots = session.get("history_snapshots", [])
        if not history or not snapshots:
            raise HTTPException(status_code=400, detail="No preprocessing action to undo")

        restored_df = snapshots.pop()
        undone_action = history.pop()
        session["data"] = restored_df.copy(deep=True)
        return undone_action

    def undo_to_history_index(self, session_id: str, history_index: int) -> Dict[str, Any]:
        """Restore the dataframe snapshot before the selected history item and trim newer actions"""
        session = self.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        history = session.get("history", [])
        snapshots = session.get("history_snapshots", [])
        if not history or not snapshots:
            raise HTTPException(status_code=400, detail="No preprocessing action to undo")
        if history_index < 0 or history_index >= len(history):
            raise HTTPException(status_code=400, detail="Invalid history index")

        restored_df = snapshots[history_index].copy(deep=True)
        undone_actions = history[history_index:]
        session["data"] = restored_df
        del history[history_index:]
        del snapshots[history_index:]
        return {
            "undone_actions": undone_actions,
            "remaining_history_count": len(history),
        }
    
    def set_metadata(self, session_id: str, key: str, value: Any):
        """Set metadata in session"""
        session = self.get_session(session_id)
        if session:
            session["metadata"][key] = value
    
    def get_metadata(self, session_id: str, key: str) -> Any:
        """Get metadata from session"""
        session = self.get_session(session_id)
        return session.get("metadata", {}).get(key) if session else None
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
    
    def cleanup_expired(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            sid for sid, session in self._sessions.items()
            if now - session["last_accessed"] > self.timeout
        ]
        for sid in expired:
            self.delete_session(sid)
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")


# Global session manager instance
session_manager = SessionManager()


async def get_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    """Dependency to get or create session ID"""
    if x_session_id and session_manager.get_session(x_session_id):
        return x_session_id
    return session_manager.create_session()


async def require_session(x_session_id: str = Header(...)) -> str:
    """Dependency that requires a valid session"""
    if not x_session_id or not session_manager.get_session(x_session_id):
        raise HTTPException(
            status_code=400,
            detail="Valid session ID required. Upload data first."
        )
    return x_session_id


async def require_data(x_session_id: str = Header(...)) -> pd.DataFrame:
    """Dependency that requires session with loaded data"""
    session_id = await require_session(x_session_id)
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(
            status_code=400,
            detail="No data loaded. Please upload data first."
        )
    return df


def get_db():
    """Yield SQLAlchemy DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    auth_cookie: Optional[str] = Cookie(default=None, alias=settings.AUTH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    """Resolve authenticated user from httpOnly cookie."""
    if not auth_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    session = db.scalar(
        select(AuthSession)
        .join(User)
        .where(
            AuthSession.token_hash == hash_session_token(auth_cookie),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.utcnow(),
            User.is_active.is_(True),
        )
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    session.last_used_at = datetime.utcnow()
    db.commit()
    return session.user


def require_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Alias dependency for protected routers."""
    return current_user
