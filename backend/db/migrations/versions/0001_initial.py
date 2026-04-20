"""create all tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --- auth_sessions ---
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("ip_address", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("last_used_at", sa.DateTime, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False, index=True),
        sa.Column("revoked_at", sa.DateTime, nullable=True),
    )

    # --- dataset_sessions ---
    op.create_table(
        "dataset_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("filename", sa.String(512), nullable=True),
        sa.Column("row_count", sa.Integer, nullable=False),
        sa.Column("column_count", sa.Integer, nullable=False),
        sa.Column("data_json", sa.Text, nullable=False),
        sa.Column("original_data_json", sa.Text, nullable=False),
        sa.Column("metadata_json", sa.JSON, nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --- preprocessing_events ---
    op.create_table(
        "preprocessing_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_session_id", sa.String(36), sa.ForeignKey("dataset_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("event_index", sa.Integer, nullable=False),
        sa.Column("step", sa.String(128), nullable=True),
        sa.Column("action", sa.String(128), nullable=True),
        sa.Column("payload_json", sa.JSON, nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("dataset_session_id", "event_index", name="uq_preprocessing_events_session_index"),
    )

    # --- trained_models ---
    op.create_table(
        "trained_models",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_session_id", sa.String(36), sa.ForeignKey("dataset_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("model_id", sa.String(128), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("target_column", sa.String(255), nullable=False),
        sa.Column("problem_type", sa.String(64), nullable=False),
        sa.Column("metrics_json", sa.JSON, nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("feature_columns_json", sa.JSON, nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("training_time", sa.Float, nullable=True),
        sa.Column("model_blob", sa.LargeBinary, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("trained_models")
    op.drop_table("preprocessing_events")
    op.drop_table("dataset_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("users")
