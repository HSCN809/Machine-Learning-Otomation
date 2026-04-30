"""Persistence helpers for uploaded dataset sessions."""

from __future__ import annotations

from datetime import datetime
from io import StringIO
from typing import Any

import pandas as pd
from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.modules.data_upload.models import (
    DatasetSession,
    PreprocessingEvent,
    TimelineSnapshot,
    utc_now,
)
from backend.modules.data_upload.timeline_rollback import normalize_event_metadata


def dataframe_to_json(df: pd.DataFrame) -> str:
    """Serialize a DataFrame with schema information for DB storage."""
    return df.to_json(orient="table", date_format="iso")


def dataframe_from_json(payload: str) -> pd.DataFrame:
    """Restore a DataFrame serialized by dataframe_to_json."""
    return pd.read_json(StringIO(payload), orient="table")


class DataSessionRepository:
    """Database access for uploaded dataset session state."""

    def __init__(self, db: Session):
        self.db = db

    def get_session(self, session_id: str, user_id: str) -> DatasetSession | None:
        return self.db.scalar(
            select(DatasetSession).where(
                DatasetSession.id == session_id,
                DatasetSession.user_id == user_id,
            )
        )

    def list_sessions(self, user_id: str) -> list[DatasetSession]:
        return list(
            self.db.scalars(
                select(DatasetSession)
                .where(DatasetSession.user_id == user_id)
                .order_by(DatasetSession.updated_at.desc(), DatasetSession.created_at.desc())
            ).all()
        )

    def upsert_session(
        self,
        *,
        session_id: str,
        user_id: str,
        data: pd.DataFrame,
        original_data: pd.DataFrame,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> DatasetSession:
        metadata_payload = jsonable_encoder(metadata or {})
        existing_record = self.db.get(DatasetSession, session_id)
        if existing_record is not None and existing_record.user_id != user_id:
            raise ValueError("Dataset session belongs to a different user")

        record = existing_record
        if record is None:
            record = DatasetSession(
                id=session_id,
                user_id=user_id,
                row_count=len(data),
                column_count=len(data.columns),
                data_json=dataframe_to_json(data),
                original_data_json=dataframe_to_json(original_data),
                metadata_json=metadata_payload,
                created_at=created_at or utc_now(),
            )
            self.db.add(record)
        else:
            record.row_count = len(data)
            record.column_count = len(data.columns)
            record.data_json = dataframe_to_json(data)
            record.original_data_json = dataframe_to_json(original_data)
            record.metadata_json = metadata_payload

        filename = metadata_payload.get("filename")
        record.filename = str(filename) if filename is not None else None
        return record

    def delete_session(self, session_id: str, user_id: str) -> None:
        record = self.get_session(session_id, user_id)
        if record is not None:
            self.db.delete(record)

    def rename_session(
        self,
        session_id: str,
        user_id: str,
        filename: str,
    ) -> DatasetSession | None:
        record = self.get_session(session_id, user_id)
        if record is None:
            return None

        metadata_payload = dict(record.metadata_json or {})
        metadata_payload["filename"] = filename

        record.filename = filename
        record.metadata_json = metadata_payload
        return record

    def list_timeline_events(self, session_id: str, user_id: str) -> list[dict[str, Any]]:
        events = self.db.scalars(
            select(PreprocessingEvent)
            .where(
                PreprocessingEvent.dataset_session_id == session_id,
                PreprocessingEvent.user_id == user_id,
            )
            .order_by(PreprocessingEvent.event_index)
        ).all()
        timeline_events: list[dict[str, Any]] = []

        for event in events:
            payload = dict(event.payload_json or {})
            metadata_payload = dict(event.metadata_json or {})

            timeline_events.append(
                normalize_event_metadata({
                    "id": event.id,
                    "category": event.category or "preprocessing",
                    "action": event.action,
                    "title": event.title,
                    "description": event.description,
                    "created_at": event.created_at.isoformat(),
                    "undoable": bool(event.undoable),
                    "metadata": metadata_payload,
                    "payload": payload,
                    "step": event.step,
                })
            )

        return timeline_events

    def list_preprocessing_history(self, session_id: str, user_id: str) -> list[dict[str, Any]]:
        return [
            dict(event.get("payload") or {})
            for event in self.list_timeline_events(session_id, user_id)
            if event.get("category") == "preprocessing"
            and (event.get("metadata") or {}).get("rollback_status", event.get("rollback_status", "active")) == "active"
        ]

    def sync_timeline_events(
        self,
        *,
        session_id: str,
        user_id: str,
        events: list[dict[str, Any]],
    ) -> None:
        self.db.execute(
            delete(PreprocessingEvent).where(
                PreprocessingEvent.dataset_session_id == session_id,
                PreprocessingEvent.user_id == user_id,
            )
        )

        for event_index, entry in enumerate(events):
            event_payload = normalize_event_metadata(dict(entry or {}))
            payload = jsonable_encoder(event_payload.get("payload") or {})
            metadata = dict(event_payload.get("metadata") or {})
            for key in (
                "rollback_status",
                "scope",
                "replayable",
                "reverted_by_event_id",
                "rollback_reason",
            ):
                if event_payload.get(key) is not None:
                    metadata[key] = event_payload.get(key)
            metadata_payload = jsonable_encoder(metadata)
            event_kwargs: dict[str, Any] = {
                "dataset_session_id": session_id,
                "user_id": user_id,
                "event_index": event_index,
                "category": str(event_payload.get("category") or "preprocessing"),
                "step": str(event_payload.get("step") or payload.get("step")) if (event_payload.get("step") or payload.get("step")) is not None else None,
                "action": str(event_payload.get("action") or payload.get("action")) if (event_payload.get("action") or payload.get("action")) is not None else None,
                "title": str(event_payload.get("title")) if event_payload.get("title") is not None else None,
                "description": str(event_payload.get("description")) if event_payload.get("description") is not None else None,
                "undoable": bool(event_payload.get("undoable")),
                "metadata_json": metadata_payload,
                "payload_json": payload,
                "created_at": utc_now() if not event_payload.get("created_at") else datetime.fromisoformat(str(event_payload["created_at"])),
            }
            if event_payload.get("id"):
                event_kwargs["id"] = str(event_payload["id"])

            event = PreprocessingEvent(**event_kwargs)
            self.db.add(event)

    def sync_preprocessing_history(
        self,
        *,
        session_id: str,
        user_id: str,
        history: list[dict[str, Any]],
    ) -> None:
        events = [
            {
                "category": "preprocessing",
                "action": entry.get("action"),
                "title": None,
                "description": None,
                "undoable": True,
                "metadata": {},
                "payload": entry,
                "step": entry.get("step"),
            }
            for entry in history
        ]
        self.sync_timeline_events(session_id=session_id, user_id=user_id, events=events)

    def list_timeline_snapshots(self, session_id: str, user_id: str) -> list[dict[str, Any]]:
        snapshots = self.db.scalars(
            select(TimelineSnapshot)
            .where(
                TimelineSnapshot.dataset_session_id == session_id,
                TimelineSnapshot.user_id == user_id,
            )
            .order_by(TimelineSnapshot.event_index)
        ).all()

        return [
            {
                "event_id": snapshot.event_id,
                "event_index": snapshot.event_index,
                "data": dataframe_from_json(snapshot.data_json),
                "created_at": snapshot.created_at.isoformat(),
            }
            for snapshot in snapshots
        ]

    def sync_timeline_snapshots(
        self,
        *,
        session_id: str,
        user_id: str,
        snapshots: list[dict[str, Any]],
    ) -> None:
        self.db.execute(
            delete(TimelineSnapshot).where(
                TimelineSnapshot.dataset_session_id == session_id,
                TimelineSnapshot.user_id == user_id,
            )
        )

        for index, snapshot in enumerate(snapshots):
            dataframe = snapshot.get("data")
            if dataframe is None:
                continue

            self.db.add(
                TimelineSnapshot(
                    dataset_session_id=session_id,
                    user_id=user_id,
                    event_id=str(snapshot["event_id"]),
                    event_index=int(snapshot.get("event_index", index)),
                    data_json=dataframe_to_json(dataframe),
                    created_at=utc_now() if not snapshot.get("created_at") else datetime.fromisoformat(str(snapshot["created_at"])),
                )
            )
