"""add generic timeline metadata and snapshots

Revision ID: 0003_generic_timeline
Revises: 0002_trained_models_fix
Create Date: 2026-04-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_generic_timeline"
down_revision: Union[str, None] = "0002_trained_models_fix"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "preprocessing_events",
        sa.Column("category", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "preprocessing_events",
        sa.Column("title", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "preprocessing_events",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "preprocessing_events",
        sa.Column("undoable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "preprocessing_events",
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )

    op.execute(
        """
        UPDATE preprocessing_events
        SET category = 'preprocessing',
            undoable = true
        WHERE category IS NULL
        """
    )
    op.alter_column("preprocessing_events", "category", nullable=False)
    op.alter_column("preprocessing_events", "undoable", server_default=None)
    op.alter_column("preprocessing_events", "metadata_json", server_default=None)

    op.create_table(
        "timeline_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_session_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("event_index", sa.Integer(), nullable=False),
        sa.Column("data_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_session_id"], ["dataset_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_session_id", "event_index", name="uq_timeline_snapshots_session_index"),
        sa.UniqueConstraint("event_id", name="uq_timeline_snapshots_event_id"),
    )
    op.create_index(
        op.f("ix_timeline_snapshots_dataset_session_id"),
        "timeline_snapshots",
        ["dataset_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_timeline_snapshots_user_id"),
        "timeline_snapshots",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_timeline_snapshots_user_id"), table_name="timeline_snapshots")
    op.drop_index(op.f("ix_timeline_snapshots_dataset_session_id"), table_name="timeline_snapshots")
    op.drop_table("timeline_snapshots")

    op.drop_column("preprocessing_events", "metadata_json")
    op.drop_column("preprocessing_events", "undoable")
    op.drop_column("preprocessing_events", "description")
    op.drop_column("preprocessing_events", "title")
    op.drop_column("preprocessing_events", "category")
