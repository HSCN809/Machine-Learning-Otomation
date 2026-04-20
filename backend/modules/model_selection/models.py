"""SQLAlchemy models for trained ML model artifacts."""

from datetime import UTC, datetime
from typing import Any

import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.api.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TrainedModel(Base):
    """Persisted trained ML model artifact stored as a binary blob in PostgreSQL."""

    __tablename__ = "trained_models"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
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
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_column: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_type: Mapped[str] = mapped_column(String(64), nullable=False)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    feature_columns_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    training_time: Mapped[float | None] = mapped_column(nullable=True)
    model_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    dataset_session: Mapped["DatasetSession"] = relationship("DatasetSession")
    user: Mapped["User"] = relationship("User")
