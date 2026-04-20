"""reconcile trained_models schema with SQLAlchemy model

Revision ID: 0002_trained_models_fix
Revises: 0001_initial
Create Date: 2026-04-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_trained_models_fix"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LEGACY_COLUMNS = (
    "confusion_matrix_json",
    "feature_importance_json",
    "file_path",
)


def _get_column_names(bind: sa.Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    columns = _get_column_names(bind, "trained_models")
    if not columns:
        return

    if "training_time" not in columns:
        op.add_column(
            "trained_models",
            sa.Column("training_time", sa.Float(), nullable=True),
        )
        columns.add("training_time")

    if "model_blob" not in columns:
        op.add_column(
            "trained_models",
            sa.Column("model_blob", sa.LargeBinary(), nullable=True),
        )
        columns.add("model_blob")

    total_rows = bind.execute(sa.text("SELECT COUNT(*) FROM trained_models")).scalar_one()
    null_blob_rows = bind.execute(
        sa.text("SELECT COUNT(*) FROM trained_models WHERE model_blob IS NULL")
    ).scalar_one()

    if null_blob_rows:
        raise RuntimeError(
            "trained_models contains legacy rows without model_blob. "
            "Manual data migration or cleanup is required before applying this migration."
        )

    op.alter_column(
        "trained_models",
        "model_blob",
        existing_type=sa.LargeBinary(),
        nullable=False,
    )

    if total_rows == 0:
        for column_name in LEGACY_COLUMNS:
            if column_name in columns:
                op.drop_column("trained_models", column_name)
    else:
        remaining_legacy = [name for name in LEGACY_COLUMNS if name in columns]
        if remaining_legacy:
            raise RuntimeError(
                "trained_models still contains legacy columns on a non-empty table: "
                + ", ".join(remaining_legacy)
                + ". Migrate the data before removing the old schema."
            )


def downgrade() -> None:
    bind = op.get_bind()
    columns = _get_column_names(bind, "trained_models")
    if not columns:
        return

    if "confusion_matrix_json" not in columns:
        op.add_column(
            "trained_models",
            sa.Column("confusion_matrix_json", sa.JSON(), nullable=True),
        )

    if "feature_importance_json" not in columns:
        op.add_column(
            "trained_models",
            sa.Column(
                "feature_importance_json",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'::json"),
            ),
        )
        op.alter_column(
            "trained_models",
            "feature_importance_json",
            existing_type=sa.JSON(),
            server_default=None,
        )

    if "file_path" not in columns:
        op.add_column(
            "trained_models",
            sa.Column("file_path", sa.String(), nullable=True),
        )

    columns = _get_column_names(bind, "trained_models")
    if "model_blob" in columns:
        op.drop_column("trained_models", "model_blob")
    if "training_time" in columns:
        op.drop_column("trained_models", "training_time")
