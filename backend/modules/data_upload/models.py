"""SQLAlchemy models for uploaded dataset sessions."""

from datetime import UTC, datetime
from typing import Any

import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.api.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class DatasetSession(Base):
    """Persisted dataset state for a browser data session."""

    __tablename__ = "dataset_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False)
    data_json: Mapped[str] = mapped_column(Text, nullable=False)
    original_data_json: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    user: Mapped["User"] = relationship("User")


class PreprocessingEvent(Base):
    """Persisted dataset timeline entry for a dataset session."""

    __tablename__ = "preprocessing_events"
    __table_args__ = (
        UniqueConstraint(
            "dataset_session_id",
            "event_index",
            name="uq_preprocessing_events_session_index",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_index: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False, default="preprocessing")
    step: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    undoable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    dataset_session: Mapped["DatasetSession"] = relationship("DatasetSession")
    user: Mapped["User"] = relationship("User")


class TimelineSnapshot(Base):
    """Persisted reversible snapshot linked to a timeline event."""

    __tablename__ = "timeline_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "dataset_session_id",
            "event_index",
            name="uq_timeline_snapshots_session_index",
        ),
        UniqueConstraint(
            "event_id",
            name="uq_timeline_snapshots_event_id",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_index: Mapped[int] = mapped_column(Integer, nullable=False)
    data_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    dataset_session: Mapped["DatasetSession"] = relationship("DatasetSession")
    user: Mapped["User"] = relationship("User")
