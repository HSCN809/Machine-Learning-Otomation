"""
Timeline Router - Shared dataset timeline endpoints
"""

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_db, persist_session, require_session, session_manager
from backend.modules.data_upload.timeline_rollback import (
    apply_selective_rollback,
    build_rollback_plan,
    normalize_event_metadata,
)

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


def _summarize_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": event.get("id"),
        "category": event.get("category"),
        "action": event.get("action"),
        "title": event.get("title"),
        "description": event.get("description"),
        "step": event.get("step"),
        "scope": event.get("scope") or (event.get("metadata") or {}).get("scope") or {},
    }


def _visible_timeline_events(session_id: str) -> list[dict[str, Any]]:
    return [
        normalize_event_metadata(dict(event))
        for event in session_manager.get_timeline_events(session_id)
        if event.get("category") != "model"
    ]


@router.get("")
async def get_timeline(session_id: str = Depends(require_session)):
    events = _visible_timeline_events(session_id)
    all_events = session_manager.get_timeline_events(session_id)
    actual_last_event_id = all_events[-1]["id"] if all_events else None
    visible_last_event_id = events[-1]["id"] if events else None
    return {
        "events": events,
        "canUndoLast": bool(
            visible_last_event_id
            and actual_last_event_id == visible_last_event_id
            and session_manager.can_undo_last_timeline_event(session_id)
        ),
        "lastEventId": visible_last_event_id,
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


@router.get("/events/{event_id}/rollback-plan")
async def get_rollback_plan(
    event_id: str,
    session_id: str = Depends(require_session),
):
    events = session_manager.get_timeline_events(session_id)
    plan = build_rollback_plan(events, event_id)
    return {
        "eventId": event_id,
        "canRollback": plan["can_rollback"],
        "targetEvent": _summarize_event(plan["target_event"]),
        "dependentEvents": [_summarize_event(event) for event in plan["dependent_events"]],
        "preservedEvents": [_summarize_event(event) for event in plan["preserved_events"]],
        "invalidatedModelEvents": [],
        "unsupportedReplayEvents": [_summarize_event(event) for event in plan["unsupported_replay_events"]],
    }


@router.post("/events/{event_id}/rollback")
async def rollback_timeline_event(
    event_id: str,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    original_df = session_manager.get_original_dataframe(session_id)
    if original_df is None:
        raise HTTPException(status_code=400, detail="No original data found")

    rollback_event_id = str(uuid.uuid4())
    result = apply_selective_rollback(
        original_df=original_df,
        events=session_manager.get_timeline_events(session_id),
        event_id=event_id,
        rollback_event_id=rollback_event_id,
    )

    session["data"] = result["data"]
    session["timeline_events"] = result["events"]
    session["timeline_snapshots"] = [
        snapshot
        for snapshot in session.get("timeline_snapshots", [])
        if snapshot.get("event_id") not in set(result["plan"]["rollback_event_ids"])
    ]
    rollback_event = session_manager.add_timeline_event(
        session_id,
        {
            "id": rollback_event_id,
            "category": "system",
            "action": "selective_rollback",
            "title": "Selective rollback applied",
            "description": "A selected timeline event and dependent events were reverted.",
            "undoable": False,
            "metadata": {
                "rollback_status": "active",
                "target_event_id": event_id,
                "reverted_event_ids": result["plan"]["rollback_event_ids"],
                "dependent_count": len(result["plan"]["dependent_events"]),
                "invalidated_model_count": len(result["plan"]["invalidated_model_events"]),
            },
            "payload": {
                "target_event_id": event_id,
                "reverted_event_ids": result["plan"]["rollback_event_ids"],
            },
        },
    )

    session["history"] = session_manager._build_legacy_history(session["timeline_events"])
    session["history_snapshots"] = []
    _clear_downstream_metadata(session_id)
    persist_session(session_id, db)
    logger.info(
        "Selective timeline rollback applied for session %s: target_event_id=%s reverted_count=%s",
        session_id,
        event_id,
        len(result["plan"]["rollback_event_ids"]),
    )
    current_df = session_manager.get_dataframe(session_id)
    if current_df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    return {
        "success": True,
        "rollbackEventId": rollback_event["id"],
        "revertedEventIds": result["plan"]["rollback_event_ids"],
        "dependentCount": len(result["plan"]["dependent_events"]),
        "invalidatedModelCount": 0,
        "rows": len(current_df),
        "columns": len(current_df.columns),
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
