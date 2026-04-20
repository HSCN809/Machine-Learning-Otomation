"""SQLAlchemy models for uploaded dataset sessions."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
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
