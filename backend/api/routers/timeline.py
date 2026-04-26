"""
Timeline Router - Shared dataset timeline endpoints
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_db, persist_session, require_session, session_manager

router = APIRouter()
logger = logging.getLogger(__name__)


class TimelineEventCreateRequest(BaseModel):
    category: str = Field(min_length=1, max_length=128)
    action: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    undoable: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    step: Optional[str] = None


def _clear_downstream_metadata(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        return

    for key in (
        "training_target_column",
        "problem_type",
        "training_results",
        "active_training_job_id",
        "trained_model_artifacts",
    ):
        session["metadata"].pop(key, None)


@router.get("")
async def get_timeline(session_id: str = Depends(require_session)):
    events = session_manager.get_timeline_events(session_id)
    return {
        "events": events,
        "canUndoLast": session_manager.can_undo_last_timeline_event(session_id),
        "lastEventId": events[-1]["id"] if events else None,
    }


@router.post("/events")
async def append_timeline_event(
    request: TimelineEventCreateRequest,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    event = session_manager.add_timeline_event(
        session_id,
        {
            "category": request.category,
            "action": request.action,
            "title": request.title,
            "description": request.description,
            "undoable": request.undoable,
            "metadata": request.metadata,
            "payload": request.payload,
            "step": request.step,
        },
    )
    persist_session(session_id, db)
    return {
        "success": True,
        "event": event,
    }


@router.post("/undo-last")
async def undo_last_timeline_event(
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    result = session_manager.undo_last_timeline_event(session_id)
    removed_event = result["removed_event"]
    current_df = session_manager.get_dataframe(session_id)
    if current_df is None:
        raise HTTPException(status_code=400, detail="No data loaded")

    if removed_event.get("category") == "editor":
        session = session_manager.get_session(session_id)
        if session:
            session["original_data"] = current_df.copy(deep=True)

    _clear_downstream_metadata(session_id)
    persist_session(session_id, db)
    logger.info(
        "Timeline undo applied for session %s: event_id=%s action=%s",
        session_id,
        removed_event.get("id"),
        removed_event.get("action"),
    )
    return {
        "success": True,
        "removedEventId": removed_event.get("id"),
        "rows": len(current_df),
        "columns": len(current_df.columns),
    }
