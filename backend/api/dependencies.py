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
from backend.modules.data_upload.persistence import DataSessionRepository, dataframe_from_json

logger = logging.getLogger(__name__)


class SessionManager:
    """In-memory session manager for storing DataFrames"""
    
    def __init__(self, timeout_minutes: int = 60):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.timeout = timedelta(minutes=timeout_minutes)

    @staticmethod
    def _build_legacy_history(timeline_events: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        return [
            dict(event.get("payload") or {})
            for event in timeline_events
            if event.get("category") == "preprocessing"
        ]
    
    def create_session(self, owner_user_id: Optional[str] = None) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "owner_user_id": owner_user_id,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "data": None,
            "original_data": None,
            "timeline_events": [],
            "timeline_snapshots": [],
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

    def restore_session(
        self,
        session_id: str,
        df: pd.DataFrame,
        original_df: pd.DataFrame,
        metadata: Dict[str, Any],
        owner_user_id: str,
        timeline_events: Optional[list[Dict[str, Any]]] = None,
        timeline_snapshots: Optional[list[Dict[str, Any]]] = None,
        created_at: Optional[datetime] = None,
    ):
        """Restore a persisted session into memory."""
        restored_timeline = timeline_events or []
        self._sessions[session_id] = {
            "owner_user_id": owner_user_id,
            "created_at": created_at or datetime.now(),
            "last_accessed": datetime.now(),
            "data": df,
            "original_data": original_df,
            "timeline_events": restored_timeline,
            "timeline_snapshots": timeline_snapshots or [],
            "history": self._build_legacy_history(restored_timeline),
            "history_snapshots": [],
            "metadata": metadata,
        }
        logger.info(f"Restored persisted session: {session_id}")

    def owns_session(self, session_id: str, user_id: str) -> bool:
        """Return whether an in-memory session belongs to the given user."""
        session = self._sessions.get(session_id)
        if not session or session.get("owner_user_id") != user_id:
            return False
        session["last_accessed"] = datetime.now()
        return True
    
    def set_dataframe(self, session_id: str, df: pd.DataFrame, is_original: bool = False):
        """Store DataFrame in session"""
        session = self.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session["data"] = df
        if is_original:
            session["original_data"] = df.copy()
            session["timeline_events"] = []
            session["timeline_snapshots"] = []
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
        if not session:
            return []
        session["history"] = self._build_legacy_history(session.get("timeline_events", []))
        return session.get("history", [])

    def add_timeline_event(self, session_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """Append a generic timeline event to the session."""
        session = self.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        normalized_event = {
            "id": str(event.get("id") or uuid.uuid4()),
            "category": str(event.get("category") or "general"),
            "action": event.get("action"),
            "title": event.get("title"),
            "description": event.get("description"),
            "created_at": str(event.get("created_at") or datetime.now().isoformat()),
            "undoable": bool(event.get("undoable")),
            "metadata": dict(event.get("metadata") or {}),
            "payload": dict(event.get("payload") or {}),
            "step": event.get("step"),
        }
        session["timeline_events"].append(normalized_event)
        session["history"] = self._build_legacy_history(session["timeline_events"])
        return normalized_event

    def add_timeline_snapshot(self, session_id: str, event_id: str, df: pd.DataFrame):
        """Store a reversible dataframe snapshot linked to a timeline event."""
        session = self.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        session["timeline_snapshots"].append(
            {
                "event_id": event_id,
                "event_index": len(session.get("timeline_events", [])),
                "data": df.copy(deep=True),
                "created_at": datetime.now().isoformat(),
            }
        )

    def get_timeline_events(self, session_id: str) -> list[Dict[str, Any]]:
        session = self.get_session(session_id)
        return session.get("timeline_events", []) if session else []

    def get_timeline_snapshots(self, session_id: str) -> list[Dict[str, Any]]:
        session = self.get_session(session_id)
        return session.get("timeline_snapshots", []) if session else []

    def can_undo_last_timeline_event(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False

        timeline_events = session.get("timeline_events", [])
        if not timeline_events:
            return False

        last_event = timeline_events[-1]
        if not last_event.get("undoable"):
            return False

        snapshots = session.get("timeline_snapshots", [])
        return bool(snapshots and snapshots[-1].get("event_id") == last_event.get("id"))

    def undo_last_timeline_event(self, session_id: str) -> Dict[str, Any]:
        """Undo the last reversible timeline event."""
        session = self.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        timeline_events = session.get("timeline_events", [])
        if not timeline_events:
            raise HTTPException(status_code=400, detail="No timeline event to undo")

        last_event = timeline_events[-1]
        if not last_event.get("undoable"):
            raise HTTPException(status_code=409, detail="Last timeline event is not undoable")

        snapshots = session.get("timeline_snapshots", [])
        if not snapshots or snapshots[-1].get("event_id") != last_event.get("id"):
            raise HTTPException(status_code=409, detail="Timeline snapshot mismatch for undo")

        restored_snapshot = snapshots.pop()
        session["data"] = restored_snapshot["data"].copy(deep=True)
        removed_event = timeline_events.pop()

        if removed_event.get("category") == "preprocessing":
            history = session.get("history", [])
            if history:
                history.pop()
            history_snapshots = session.get("history_snapshots", [])
            if history_snapshots:
                history_snapshots.pop()

        session["history"] = self._build_legacy_history(timeline_events)
        return {
            "removed_event": removed_event,
            "remaining_count": len(timeline_events),
        }

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


def restore_persisted_session(session_id: str, user_id: str, db: Session) -> bool:
    """Load a persisted dataset session into the in-memory manager."""
    repository = DataSessionRepository(db)
    record = repository.get_session(session_id, user_id)
    if record is None:
        return False

    session_manager.restore_session(
        session_id=session_id,
        df=dataframe_from_json(record.data_json),
        original_df=dataframe_from_json(record.original_data_json),
        metadata=record.metadata_json or {},
        owner_user_id=user_id,
        timeline_events=repository.list_timeline_events(session_id, user_id),
        timeline_snapshots=repository.list_timeline_snapshots(session_id, user_id),
        created_at=record.created_at,
    )
    return True


def persist_session(session_id: str, db: Session):
    """Persist the current in-memory dataset session to PostgreSQL."""
    session = session_manager.get_session(session_id)
    if not session or session.get("data") is None:
        raise HTTPException(status_code=400, detail="No data loaded")

    user_id = session.get("owner_user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Valid session ID required. Upload data first.")

    original_df = session.get("original_data")
    if original_df is None:
        original_df = session["data"].copy(deep=True)

    repository = DataSessionRepository(db)
    repository.upsert_session(
        session_id=session_id,
        user_id=user_id,
        data=session["data"],
        original_data=original_df,
        metadata=session.get("metadata", {}),
        created_at=session.get("created_at"),
    )
    repository.sync_timeline_events(
        session_id=session_id,
        user_id=user_id,
        events=session.get("timeline_events", []),
    )
    repository.sync_timeline_snapshots(
        session_id=session_id,
        user_id=user_id,
        snapshots=session.get("timeline_snapshots", []),
    )
    db.commit()


def delete_persisted_session(session_id: str, user_id: str, db: Session):
    """Delete a persisted dataset session from PostgreSQL."""
    DataSessionRepository(db).delete_session(session_id, user_id)
    db.commit()


async def get_session_id(
    x_session_id: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> str:
    """Dependency to get or create session ID"""
    if x_session_id and session_manager.owns_session(x_session_id, current_user.id):
        return x_session_id
    if x_session_id and restore_persisted_session(x_session_id, current_user.id, db):
        return x_session_id
    return session_manager.create_session(owner_user_id=current_user.id)


async def require_session(
    x_session_id: str = Header(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> str:
    """Dependency that requires a valid session"""
    has_session = bool(x_session_id and session_manager.owns_session(x_session_id, current_user.id))
    if not has_session and x_session_id:
        has_session = restore_persisted_session(x_session_id, current_user.id, db)

    if not has_session:
        raise HTTPException(
            status_code=400,
            detail="Valid session ID required. Upload data first."
        )
    return x_session_id


async def require_data(
    x_session_id: str = Header(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> pd.DataFrame:
    """Dependency that requires session with loaded data"""
    session_id = await require_session(x_session_id, current_user, db)
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(
            status_code=400,
            detail="No data loaded. Please upload data first."
        )
    return df
