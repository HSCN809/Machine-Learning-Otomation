"""Persistence helpers for trained ML model artifacts."""

from __future__ import annotations

import pickle
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.modules.model_selection.models import TrainedModel


class TrainedModelRepository:
    """Database access for trained ML model artifacts."""

    def __init__(self, db: Session):
        self.db = db

    def save_model(
        self,
        *,
        dataset_session_id: str,
        user_id: str,
        model_id: str,
        model_name: str,
        target_column: str,
        problem_type: str,
        metrics: dict[str, Any],
        feature_columns: list[str],
        training_time: float | None,
        model_object: Any,
    ) -> TrainedModel:
        """Serialize and persist a trained model to PostgreSQL."""
        model_blob = pickle.dumps(model_object)

        # Aynı oturum+kullanıcı+model_id için varsa güncelle, yoksa ekle.
        existing = self.db.scalar(
            select(TrainedModel).where(
                TrainedModel.dataset_session_id == dataset_session_id,
                TrainedModel.user_id == user_id,
                TrainedModel.model_id == model_id,
            )
        )

        if existing is not None:
            existing.model_name = model_name
            existing.target_column = target_column
            existing.problem_type = problem_type
            existing.metrics_json = metrics
            existing.feature_columns_json = feature_columns
            existing.training_time = training_time
            existing.model_blob = model_blob
            return existing

        record = TrainedModel(
            dataset_session_id=dataset_session_id,
            user_id=user_id,
            model_id=model_id,
            model_name=model_name,
            target_column=target_column,
            problem_type=problem_type,
            metrics_json=metrics,
            feature_columns_json=feature_columns,
            training_time=training_time,
            model_blob=model_blob,
        )
        self.db.add(record)
        return record

    def get_model(
        self,
        *,
        model_record_id: str,
        dataset_session_id: str,
        user_id: str,
    ) -> TrainedModel | None:
        """Get a specific trained model by its primary key, scoped by session and user."""
        return self.db.scalar(
            select(TrainedModel).where(
                TrainedModel.id == model_record_id,
                TrainedModel.dataset_session_id == dataset_session_id,
                TrainedModel.user_id == user_id,
            )
        )

    def get_model_by_model_id(
        self,
        *,
        model_id: str,
        dataset_session_id: str,
        user_id: str,
    ) -> TrainedModel | None:
        """Get a trained model by its logical model_id (e.g. 'random_forest_clf')."""
        return self.db.scalar(
            select(TrainedModel).where(
                TrainedModel.model_id == model_id,
                TrainedModel.dataset_session_id == dataset_session_id,
                TrainedModel.user_id == user_id,
            )
        )

    def list_models(
        self,
        *,
        dataset_session_id: str,
        user_id: str,
    ) -> list[TrainedModel]:
        """List all trained models for a dataset session."""
        return list(
            self.db.scalars(
                select(TrainedModel)
                .where(
                    TrainedModel.dataset_session_id == dataset_session_id,
                    TrainedModel.user_id == user_id,
                )
                .order_by(TrainedModel.created_at.desc())
            ).all()
        )

    def rename_model(
        self,
        *,
        model_record_id: str,
        dataset_session_id: str,
        user_id: str,
        model_name: str,
    ) -> TrainedModel | None:
        record = self.get_model(
            model_record_id=model_record_id,
            dataset_session_id=dataset_session_id,
            user_id=user_id,
        )
        if record is None:
            return None

        record.model_name = model_name
        return record

    def delete_model(
        self,
        *,
        model_record_id: str,
        dataset_session_id: str,
        user_id: str,
    ) -> bool:
        record = self.get_model(
            model_record_id=model_record_id,
            dataset_session_id=dataset_session_id,
            user_id=user_id,
        )
        if record is None:
            return False

        self.db.delete(record)
        return True

    def delete_models_for_session(
        self,
        *,
        dataset_session_id: str,
        user_id: str,
    ) -> None:
        """Delete all trained models for a dataset session."""
        models = self.list_models(
            dataset_session_id=dataset_session_id, user_id=user_id
        )
        for model in models:
            self.db.delete(model)
