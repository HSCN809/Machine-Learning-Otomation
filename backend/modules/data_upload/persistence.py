"""Persistence helpers for uploaded dataset sessions."""

from __future__ import annotations

from datetime import datetime
from io import StringIO
from typing import Any

import pandas as pd
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.modules.data_upload.models import DatasetSession, utc_now


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
