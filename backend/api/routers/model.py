"""
Model Router - Model training and evaluation endpoints
"""

import asyncio
import json
import logging
import os
import pickle
import sys
import threading
import uuid
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from starlette.responses import StreamingResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from sqlalchemy.orm import Session

from ..dependencies import (
    get_current_user,
    get_db,
    persist_session,
    require_session,
    session_manager,
)
from backend.modules.model_selection.persistence import TrainedModelRepository

try:
    import xgboost as xgb
except ImportError:
    xgb = None

router = APIRouter()
logger = logging.getLogger(__name__)
TRAINING_JOBS: Dict[str, Dict[str, Any]] = {}
TRAINING_JOBS_LOCK = threading.Lock()


# Request schemas
class TrainRequest(BaseModel):
    target_column: str
    problem_type: Optional[str] = None
    models: List[str]
    test_size: float = 0.2
    params: Optional[Dict[str, Dict[str, Any]]] = None


class StopTrainingRequest(BaseModel):
    job_id: str


MODEL_PARAM_CASTERS: Dict[str, Dict[str, Any]] = {
    "logistic_regression": {"C": float, "max_iter": int},
    "random_forest_clf": {"n_estimators": int, "max_depth": int},
    "xgboost_clf": {"n_estimators": int, "learning_rate": float, "max_depth": int},
    "svc": {"C": float, "kernel": str},
    "decision_tree_clf": {"max_depth": int, "min_samples_split": int},
    "linear_regression": {},
    "ridge": {"alpha": float},
    "lasso": {"alpha": float},
    "random_forest_reg": {"n_estimators": int, "max_depth": int},
    "xgboost_reg": {"n_estimators": int, "learning_rate": float, "max_depth": int},
    "svr": {"C": float, "kernel": str},
}

CLASSIFICATION_MODEL_IDS = {
    "logistic_regression",
    "random_forest_clf",
    "xgboost_clf",
    "svc",
    "decision_tree_clf",
}

REGRESSION_MODEL_IDS = {
    "linear_regression",
    "ridge",
    "lasso",
    "random_forest_reg",
    "xgboost_reg",
    "svr",
}


def _normalize_model_params(model_id: str, raw_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not raw_params:
        return {}

    normalized: Dict[str, Any] = {}
    casters = MODEL_PARAM_CASTERS.get(model_id, {})
    for key, value in raw_params.items():
        if value is None or key not in casters:
            continue
        try:
            normalized[key] = casters[key](value)
        except (TypeError, ValueError):
            continue

    return normalized


def _build_model(model_id: str, custom_params: Optional[Dict[str, Any]]):
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.linear_model import Lasso, LinearRegression, LogisticRegression, Ridge
    from sklearn.svm import SVC, SVR
    from sklearn.tree import DecisionTreeClassifier

    normalized_params = _normalize_model_params(model_id, custom_params)

    if model_id == "logistic_regression":
        return LogisticRegression(max_iter=1000, **normalized_params)
    if model_id == "random_forest_clf":
        return RandomForestClassifier(n_estimators=100, random_state=42, **normalized_params)
    if model_id == "xgboost_clf":
        if xgb is None:
            raise HTTPException(status_code=500, detail="XGBoost is not installed")
        return xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42,
            n_jobs=-1,
            eval_metric='logloss',
            **normalized_params,
        )
    if model_id == "svc":
        return SVC(probability=True, **normalized_params)
    if model_id == "decision_tree_clf":
        return DecisionTreeClassifier(random_state=42, **normalized_params)
    if model_id == "linear_regression":
        return LinearRegression(**normalized_params)
    if model_id == "ridge":
        return Ridge(**normalized_params)
    if model_id == "lasso":
        return Lasso(max_iter=1000, **normalized_params)
    if model_id == "random_forest_reg":
        return RandomForestRegressor(n_estimators=100, random_state=42, **normalized_params)
    if model_id == "xgboost_reg":
        if xgb is None:
            raise HTTPException(status_code=500, detail="XGBoost is not installed")
        return xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42,
            n_jobs=-1,
            **normalized_params,
        )
    if model_id == "svr":
        return SVR(**normalized_params)

    return None


def _get_problem_type_label(is_classification: bool) -> str:
    return "classification" if is_classification else "regression"


def _is_integer_like_series(series: pd.Series) -> bool:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return False
    return bool(np.allclose(numeric, np.round(numeric)))


def _infer_problem_type(target: pd.Series) -> str:
    non_null_target = target.dropna()
    if non_null_target.empty:
        return "regression"

    if (
        non_null_target.dtype == "object"
        or non_null_target.dtype.name == "category"
        or non_null_target.dtype == "bool"
    ):
        return "classification"

    unique_count = non_null_target.nunique()
    unique_ratio = unique_count / len(non_null_target) if len(non_null_target) > 0 else 0

    if _is_integer_like_series(non_null_target) and unique_count <= 20 and unique_ratio <= 0.2:
        return "classification"

    return "regression"


def _resolve_problem_type(requested_problem_type: Optional[str], target: pd.Series) -> str:
    if requested_problem_type in {"classification", "regression"}:
        return requested_problem_type
    return _infer_problem_type(target)


def _validate_target_for_problem_type(target: pd.Series, problem_type: str):
    non_null_target = target.dropna()
    if non_null_target.empty:
        raise HTTPException(status_code=400, detail="Hedef kolonda gecerli veri bulunamadi")

    if problem_type == "regression":
        numeric_target = pd.to_numeric(non_null_target, errors="coerce")
        if numeric_target.isna().any():
            raise HTTPException(
                status_code=400,
                detail="Regresyon icin hedef kolon sayisal olmalidir",
            )
        return

    if (
        non_null_target.dtype == "object"
        or non_null_target.dtype.name == "category"
        or non_null_target.dtype == "bool"
    ):
        return

    if not _is_integer_like_series(non_null_target):
        raise HTTPException(
            status_code=400,
            detail="Siniflandirma icin hedef kolon ayrik siniflardan olusmalidir",
        )


def _validate_models_for_problem_type(model_ids: List[str], problem_type: str):
    allowed_models = CLASSIFICATION_MODEL_IDS if problem_type == "classification" else REGRESSION_MODEL_IDS
    invalid_models = [model_id for model_id in model_ids if model_id not in allowed_models]
    if invalid_models:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Secilen modeller hedef kolon icin uygun degil: {', '.join(invalid_models)}. "
                f"Beklenen problem tipi: {problem_type}."
            ),
        )


def _sort_training_results(results: List[Dict[str, Any]], problem_type: str) -> List[Dict[str, Any]]:
    primary_metric = "accuracy" if problem_type == "classification" else "r2"
    return sorted(results, key=lambda item: item["metrics"].get(primary_metric, 0), reverse=True)


def _store_trained_model_artifact(
    session_id: str,
    db: Session,
    *,
    model_id: str,
    model_name: str,
    model: Any,
    target_column: str,
    problem_type: str,
    feature_columns: List[str],
    metrics: Optional[Dict[str, Any]] = None,
    training_time: Optional[float] = None,
):
    """Eğitilmiş modeli PostgreSQL'e BYTEA olarak kaydet."""
    session = session_manager.get_session(session_id)
    user_id = session.get("owner_user_id") if session else None
    if not user_id:
        return

    repo = TrainedModelRepository(db)
    repo.save_model(
        dataset_session_id=session_id,
        user_id=user_id,
        model_id=model_id,
        model_name=model_name,
        target_column=target_column,
        problem_type=problem_type,
        metrics=metrics or {},
        feature_columns=feature_columns,
        training_time=training_time,
        model_object=model,
    )


def _store_training_metadata(
    session_id: str,
    *,
    target_column: Optional[str] = None,
    problem_type: Optional[str] = None,
    results: Optional[List[Dict[str, Any]]] = None,
    active_job_id: Optional[str] = None,
    db: Optional[Session] = None,
):
    if target_column is not None:
        session_manager.set_metadata(session_id, "training_target_column", target_column)
    if problem_type is not None:
        session_manager.set_metadata(session_id, "problem_type", problem_type)
    if results is not None:
        session_manager.set_metadata(session_id, "training_results", results)
    session_manager.set_metadata(session_id, "active_training_job_id", active_job_id)
    if db is not None:
        persist_session(session_id, db)


def _append_model_timeline_event(
    session_id: str,
    *,
    action: str,
    title: str,
    description: str,
    db: Session,
    metadata: Optional[Dict[str, Any]] = None,
):
    logger.info("Model event skipped for timeline: session=%s action=%s", session_id, action)
    persist_session(session_id, db)


def _build_result_payload(
    *,
    model_id: str,
    model_name: str,
    metrics: Optional[Dict[str, Any]] = None,
    training_time: Optional[float] = None,
    confusion_matrix: Optional[List[List[int]]] = None,
    confusion_labels: Optional[List[str]] = None,
    feature_importance: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "model_id": model_id,
        "model_name": model_name,
        "metrics": metrics or {},
        "confusion_matrix": confusion_matrix,
        "confusion_labels": confusion_labels,
        "feature_importance": feature_importance or [],
        "training_time": training_time,
    }


def _load_persisted_training_results(
    session_id: str,
    db: Session,
) -> tuple[list[dict[str, Any]], Optional[str], Optional[str]]:
    session = session_manager.get_session(session_id)
    user_id = session.get("owner_user_id") if session else None
    if not user_id:
        return [], None, None

    repo = TrainedModelRepository(db)
    records = repo.list_models(dataset_session_id=session_id, user_id=user_id)
    if not records:
        return [], None, None

    problem_type = records[0].problem_type
    target_column = records[0].target_column
    results = [
        _build_result_payload(
            model_id=record.model_id,
            model_name=record.model_name,
            metrics=record.metrics_json,
            training_time=record.training_time,
        )
        for record in records
    ]
    return _sort_training_results(results, problem_type), problem_type, target_column


def _create_job(session_id: str, request: TrainRequest) -> str:
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "session_id": session_id,
        "target_column": request.target_column,
        "problem_type": request.problem_type,
        "models": request.models,
        "test_size": request.test_size,
        "params": request.params or {},
        "status": "queued",
        "current_model": None,
        "total_models": len(request.models),
        "completed_models": 0,
        "results": [],
        "error": None,
        "stop_requested": False,
        "revision": 0,
        "started_at": datetime.now().isoformat(),
        "finished_at": None,
    }
    with TRAINING_JOBS_LOCK:
        TRAINING_JOBS[job_id] = job

    _store_training_metadata(
        session_id,
        target_column=request.target_column,
        results=[],
        active_job_id=job_id,
    )
    # trained_model_artifacts artik DB'de tutuluyor
    return job_id


def _get_job_snapshot(job_id: str) -> Optional[Dict[str, Any]]:
    with TRAINING_JOBS_LOCK:
        job = TRAINING_JOBS.get(job_id)
        if job is None:
            return None
        return {
            "job_id": job["job_id"],
            "session_id": job["session_id"],
            "target_column": job["target_column"],
            "problem_type": job["problem_type"],
            "models": list(job["models"]),
            "test_size": job["test_size"],
            "params": dict(job["params"]),
            "status": job["status"],
            "current_model": job["current_model"],
            "total_models": job["total_models"],
            "completed_models": job["completed_models"],
            "results": list(job["results"]),
            "error": job["error"],
            "stop_requested": job["stop_requested"],
            "revision": job["revision"],
            "started_at": job["started_at"],
            "finished_at": job["finished_at"],
        }


def _update_job(job_id: str, **changes: Any) -> Optional[Dict[str, Any]]:
    with TRAINING_JOBS_LOCK:
        job = TRAINING_JOBS.get(job_id)
        if job is None:
            return None
        job.update(changes)
        job["revision"] += 1
        return dict(job)


def _find_active_job_for_session(session_id: str) -> Optional[Dict[str, Any]]:
    active_job_id = session_manager.get_metadata(session_id, "active_training_job_id")
    if not active_job_id:
        return None
    return _get_job_snapshot(active_job_id)


def _prepare_training_bundle(
    df: pd.DataFrame,
    target_column: str,
    test_size: float,
    problem_type: str,
) -> Dict[str, Any]:
    from sklearn.model_selection import train_test_split

    if target_column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Target column '{target_column}' not found")

    X = df.drop(columns=[target_column])
    y = df[target_column]
    original_target = y.copy()
    class_label_lookup: Optional[List[str]] = None

    X = pd.get_dummies(X, drop_first=True)

    _validate_target_for_problem_type(original_target, problem_type)

    if problem_type == "classification" and (y.dtype == 'object' or y.dtype.name == 'category'):
        categorical_target = y.astype('category')
        class_label_lookup = [str(label) for label in categorical_target.cat.categories.tolist()]
        y = categorical_target.cat.codes
    elif problem_type == "regression":
        y = pd.to_numeric(y, errors="coerce")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    is_classification = problem_type == "classification"

    return {
        "X": X,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "is_classification": is_classification,
        "problem_type": problem_type,
        "class_label_lookup": class_label_lookup,
    }


def _train_single_model(
    model_id: str,
    model: Any,
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        mean_absolute_error,
        mean_squared_error,
        precision_score,
        r2_score,
        recall_score,
        roc_auc_score,
    )

    model_names = {
        "logistic_regression": "Logistic Regression",
        "random_forest_clf": "Random Forest",
        "xgboost_clf": "XGBoost",
        "decision_tree_clf": "Decision Tree",
        "svc": "SVC",
        "linear_regression": "Linear Regression",
        "ridge": "Ridge",
        "lasso": "Lasso",
        "random_forest_reg": "Random Forest Regressor",
        "xgboost_reg": "XGBoost Regressor",
        "svr": "SVR",
    }

    start_time = datetime.now()
    model.fit(bundle["X_train"], bundle["y_train"])
    y_pred = model.predict(bundle["X_test"])
    training_time = (datetime.now() - start_time).total_seconds()

    if bundle["is_classification"]:
        metrics = {
            "accuracy": round(accuracy_score(bundle["y_test"], y_pred), 4),
            "precision": round(precision_score(bundle["y_test"], y_pred, average='weighted', zero_division=0), 4),
            "recall": round(recall_score(bundle["y_test"], y_pred, average='weighted', zero_division=0), 4),
            "f1_score": round(f1_score(bundle["y_test"], y_pred, average='weighted', zero_division=0), 4),
        }

        try:
            if hasattr(model, 'predict_proba'):
                y_prob = model.predict_proba(bundle["X_test"])
                if y_prob.shape[1] == 2:
                    metrics["auc"] = round(roc_auc_score(bundle["y_test"], y_prob[:, 1]), 4)
        except Exception as exc:
            logger.warning("AUC calculation failed for model %s: %s", model_id, exc)

        class_labels = np.unique(np.concatenate([np.asarray(bundle["y_test"]), np.asarray(y_pred)]))
        confusion = confusion_matrix(bundle["y_test"], y_pred, labels=class_labels).tolist()
        if bundle["class_label_lookup"] is not None:
            confusion_labels = [
                bundle["class_label_lookup"][int(label)]
                if int(label) < len(bundle["class_label_lookup"])
                else str(label)
                for label in class_labels.tolist()
            ]
        else:
            confusion_labels = [str(label) for label in class_labels.tolist()]
    else:
        metrics = {
            "mse": round(mean_squared_error(bundle["y_test"], y_pred), 4),
            "rmse": round(np.sqrt(mean_squared_error(bundle["y_test"], y_pred)), 4),
            "mae": round(mean_absolute_error(bundle["y_test"], y_pred), 4),
            "r2": round(r2_score(bundle["y_test"], y_pred), 4),
        }
        confusion = None
        confusion_labels = None

    feature_importance: List[Dict[str, Any]] = []
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        for i, col in enumerate(bundle["X"].columns):
            feature_importance.append({
                "feature": col,
                "importance": round(float(importances[i]), 4),
            })
        feature_importance.sort(key=lambda x: x["importance"], reverse=True)
    elif hasattr(model, 'coef_'):
        coefs = np.abs(model.coef_).flatten() if model.coef_.ndim > 1 else np.abs(model.coef_)
        for i, col in enumerate(bundle["X"].columns[:len(coefs)]):
            feature_importance.append({
                "feature": col,
                "importance": round(float(coefs[i]), 4),
            })
        feature_importance.sort(key=lambda x: x["importance"], reverse=True)

    return {
        "model_id": model_id,
        "model_name": model_names.get(model_id, model_id),
        "metrics": metrics,
        "confusion_matrix": confusion,
        "confusion_labels": confusion_labels,
        "feature_importance": feature_importance[:10],
        "training_time": round(training_time, 2),
    }


def _run_training_job(job_id: str):
    from backend.api.database import SessionLocal

    snapshot = _get_job_snapshot(job_id)
    if snapshot is None:
        return

    session_id = snapshot["session_id"]
    db = SessionLocal()

    try:
        df = session_manager.get_dataframe(session_id)
        if df is None:
            raise HTTPException(status_code=400, detail="No data loaded")

        target = df[snapshot["target_column"]]
        problem_type = _resolve_problem_type(snapshot.get("problem_type"), target)
        bundle = _prepare_training_bundle(
            df,
            snapshot["target_column"],
            float(snapshot["test_size"]) if "test_size" in snapshot else 0.2,
            problem_type,
        )
        _validate_models_for_problem_type(model_ids=snapshot.get("models", []), problem_type=problem_type)
        _update_job(job_id, status="running", problem_type=problem_type)
        _store_training_metadata(
            session_id,
            target_column=snapshot["target_column"],
            problem_type=problem_type,
            results=[],
            active_job_id=job_id,
            db=db,
        )

        results: List[Dict[str, Any]] = []
        raw_params = snapshot.get("params", {})
        model_ids = snapshot.get("models", [])

        for model_id in model_ids:
            current_snapshot = _get_job_snapshot(job_id)
            if current_snapshot is None:
                return
            if current_snapshot["stop_requested"]:
                _update_job(
                    job_id,
                    status="stopped",
                    current_model=None,
                    finished_at=datetime.now().isoformat(),
                )
                _store_training_metadata(
                    session_id,
                    problem_type=problem_type,
                    results=_sort_training_results(results, problem_type),
                    active_job_id=None,
                    db=db,
                )
                _append_model_timeline_event(
                    session_id,
                    action="training_stopped",
                    title="Model eğitimi durduruldu",
                    description="Çalışan model eğitimi isteği kullanıcı talebiyle durduruldu.",
                    db=db,
                    metadata={
                        "job_id": job_id,
                        "target_column": snapshot["target_column"],
                        "problem_type": problem_type,
                        "completed_models": len(results),
                    },
                )
                return

            model = _build_model(model_id, raw_params.get(model_id))
            if model is None:
                continue

            _update_job(job_id, current_model=model_id)
            result = _train_single_model(model_id, model, bundle)
            _store_trained_model_artifact(
                session_id,
                db,
                model_id=model_id,
                model_name=result["model_name"],
                model=model,
                target_column=snapshot["target_column"],
                problem_type=problem_type,
                feature_columns=bundle["X"].columns.tolist(),
                metrics=result.get("metrics"),
                training_time=result.get("training_time"),
            )
            db.commit()
            results.append(result)
            sorted_results = _sort_training_results(results, problem_type)
            _update_job(
                job_id,
                completed_models=len(results),
                results=sorted_results,
            )
            _store_training_metadata(
                session_id,
                problem_type=problem_type,
                results=sorted_results,
                active_job_id=job_id,
                db=db,
            )

        if not results:
            raise HTTPException(status_code=400, detail="No supported models were trained")

        final_results = _sort_training_results(results, problem_type)
        _update_job(
            job_id,
            status="completed",
            current_model=None,
            completed_models=len(final_results),
            results=final_results,
            finished_at=datetime.now().isoformat(),
        )
        _store_training_metadata(
            session_id,
            problem_type=problem_type,
            results=final_results,
            active_job_id=None,
            db=db,
        )
        _append_model_timeline_event(
            session_id,
            action="training_completed",
            title="Model eğitimi tamamlandı",
            description=f"{len(final_results)} model eğitimi tamamlandı ve sonuçlar kaydedildi.",
            db=db,
            metadata={
                "job_id": job_id,
                "target_column": snapshot["target_column"],
                "problem_type": problem_type,
                "completed_models": len(final_results),
                "model_ids": [result["model_id"] for result in final_results],
            },
        )
    except HTTPException as exc:
        logger.warning(
            "Training job failed for job %s session %s: %s",
            job_id,
            session_id,
            exc.detail,
        )
        _update_job(
            job_id,
            status="failed",
            current_model=None,
            error=exc.detail,
            finished_at=datetime.now().isoformat(),
        )
        _store_training_metadata(session_id, active_job_id=None, db=db)
        _append_model_timeline_event(
            session_id,
            action="training_failed",
            title="Model eğitimi başarısız oldu",
            description="Model eğitimi sırasında hata oluştu.",
            db=db,
            metadata={
                "job_id": job_id,
                "target_column": snapshot["target_column"],
                "error": exc.detail,
            },
        )
    except Exception as exc:
        logger.exception("Training job crashed for job %s session %s", job_id, session_id)
        _update_job(
            job_id,
            status="failed",
            current_model=None,
            error=str(exc),
            finished_at=datetime.now().isoformat(),
        )
        _store_training_metadata(session_id, active_job_id=None, db=db)
        _append_model_timeline_event(
            session_id,
            action="training_failed",
            title="Model eğitimi başarısız oldu",
            description="Model eğitimi sırasında beklenmeyen hata oluştu.",
            db=db,
            metadata={
                "job_id": job_id,
                "target_column": snapshot["target_column"],
                "error": str(exc),
            },
        )
    finally:
        db.close()


@router.get("/detect-problem")
async def detect_problem_type(
    target_column: str,
    session_id: str = Depends(require_session)
):
    """Detect problem type based on target column"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    if target_column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Column '{target_column}' not found")
    
    target = df[target_column]
    unique_count = target.nunique()
    problem_type = _infer_problem_type(target)
    
    return {
        "target_column": target_column,
        "problem_type": problem_type,
        "unique_values": unique_count,
        "dtype": str(target.dtype),
    }


@router.get("/available-models")
async def get_available_models(
    problem_type: str,
):
    """Get available models for problem type"""
    classification_models = [
        {"id": "logistic_regression", "name": "Logistic Regression", "category": "linear"},
        {"id": "random_forest_clf", "name": "Random Forest", "category": "tree"},
        {"id": "xgboost_clf", "name": "XGBoost", "category": "tree"},
        {"id": "svc", "name": "Support Vector Classifier", "category": "svm"},
        {"id": "decision_tree_clf", "name": "Decision Tree", "category": "tree"},
    ]
    
    regression_models = [
        {"id": "linear_regression", "name": "Linear Regression", "category": "linear"},
        {"id": "ridge", "name": "Ridge Regression", "category": "linear"},
        {"id": "lasso", "name": "Lasso Regression", "category": "linear"},
        {"id": "random_forest_reg", "name": "Random Forest Regressor", "category": "tree"},
        {"id": "xgboost_reg", "name": "XGBoost Regressor", "category": "tree"},
        {"id": "svr", "name": "Support Vector Regressor", "category": "svm"},
    ]
    
    if problem_type == "classification":
        return {"models": classification_models}
    elif problem_type == "regression":
        return {"models": regression_models}
    else:
        raise HTTPException(status_code=400, detail="Invalid problem type")


@router.post("/train/start")
async def start_training(
    request: TrainRequest,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Start model training in background and return a job id."""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    if request.target_column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Target column '{request.target_column}' not found")

    active_job = _find_active_job_for_session(session_id)
    if active_job and active_job["status"] in {"queued", "running", "stopping"}:
        raise HTTPException(status_code=409, detail="A training job is already running for this session")

    job_id = _create_job(session_id, request)
    _append_model_timeline_event(
        session_id,
        action="training_started",
        title="Model eğitimi başlatıldı",
        description=f"{len(request.models)} model için eğitim kuyruğa alındı.",
        db=db,
        metadata={
            "job_id": job_id,
            "target_column": request.target_column,
            "problem_type": request.problem_type,
            "models": request.models,
        },
    )
    worker = threading.Thread(target=_run_training_job, args=(job_id,), daemon=True)
    worker.start()

    return {"success": True, "job_id": job_id}


@router.get("/train/stream")
async def stream_training(
    request: Request,
    job_id: str,
    session_id: str = Query(...),
    current_user=Depends(get_current_user),
):
    """Stream training progress for a job via SSE."""
    if not session_manager.owns_session(session_id, current_user.id):
        raise HTTPException(status_code=400, detail="Valid session ID required. Upload data first.")

    snapshot = _get_job_snapshot(job_id)
    if snapshot is None or snapshot["session_id"] != session_id:
        raise HTTPException(status_code=404, detail="Training job not found")

    async def event_generator():
        last_revision = -1
        while True:
            if await request.is_disconnected():
                break

            current = _get_job_snapshot(job_id)
            if current is None:
                break

            if current["revision"] != last_revision:
                payload = {
                    "job_id": current["job_id"],
                    "target_column": current["target_column"],
                    "status": current["status"],
                    "current_model": current["current_model"],
                    "total_models": current["total_models"],
                    "completed_models": current["completed_models"],
                    "results": current["results"],
                    "problem_type": current["problem_type"],
                    "error": current["error"],
                    "stop_requested": current["stop_requested"],
                }
                yield f"data: {json.dumps(payload)}\n\n"
                last_revision = current["revision"]

            if current["status"] in {"completed", "failed", "stopped"}:
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/train/stop")
async def stop_training(
    request: StopTrainingRequest,
    session_id: str = Depends(require_session)
):
    """Request background training to stop after the current checkpoint."""
    snapshot = _get_job_snapshot(request.job_id)
    if snapshot is None or snapshot["session_id"] != session_id:
        raise HTTPException(status_code=404, detail="Training job not found")
    if snapshot["status"] not in {"queued", "running"}:
        raise HTTPException(status_code=400, detail="Training job is not running")

    _update_job(request.job_id, stop_requested=True, status="stopping")
    return {"success": True, "job_id": request.job_id}


@router.post("/train")
async def train_models(
    request: TrainRequest,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db)
):
    """Train selected models"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    if request.target_column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Target column '{request.target_column}' not found")
    
    try:
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
            mean_squared_error, mean_absolute_error, r2_score
        )
        # trained_model_artifacts artik DB'de tutuluyor
        target = df[request.target_column]
        problem_type = _resolve_problem_type(request.problem_type, target)
        bundle = _prepare_training_bundle(df, request.target_column, request.test_size, problem_type)
        X = bundle["X"]
        X_train = bundle["X_train"]
        X_test = bundle["X_test"]
        y_train = bundle["y_train"]
        y_test = bundle["y_test"]
        class_label_lookup = bundle["class_label_lookup"]
        is_classification = bundle["is_classification"]
        _validate_models_for_problem_type(request.models, problem_type)
        
        model_names = {
            "logistic_regression": "Logistic Regression",
            "random_forest_clf": "Random Forest",
            "xgboost_clf": "XGBoost",
            "decision_tree_clf": "Decision Tree",
            "svc": "SVC",
            "linear_regression": "Linear Regression",
            "ridge": "Ridge",
            "lasso": "Lasso",
            "random_forest_reg": "Random Forest Regressor",
            "xgboost_reg": "XGBoost Regressor",
            "svr": "SVR",
        }
        
        results = []
        
        for model_id in request.models:
            model = _build_model(model_id, (request.params or {}).get(model_id))
            if model is None:
                continue
            
            start_time = datetime.now()
            
            # Train
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate metrics
            if is_classification:
                metrics = {
                    "accuracy": round(accuracy_score(y_test, y_pred), 4),
                    "precision": round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                    "recall": round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                    "f1_score": round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                }
                
                # Try to calculate AUC
                try:
                    if hasattr(model, 'predict_proba'):
                        y_prob = model.predict_proba(X_test)
                        if y_prob.shape[1] == 2:
                            metrics["auc"] = round(roc_auc_score(y_test, y_prob[:, 1]), 4)
                except Exception as exc:
                    logger.warning("AUC calculation failed for model %s: %s", model_id, exc)
                
                # Confusion matrix
                from sklearn.metrics import confusion_matrix
                class_labels = np.unique(np.concatenate([np.asarray(y_test), np.asarray(y_pred)]))
                cm = confusion_matrix(y_test, y_pred, labels=class_labels)
                confusion = cm.tolist()
                if class_label_lookup is not None:
                    confusion_labels = [
                        class_label_lookup[int(label)] if int(label) < len(class_label_lookup) else str(label)
                        for label in class_labels.tolist()
                    ]
                else:
                    confusion_labels = [str(label) for label in class_labels.tolist()]
            else:
                metrics = {
                    "mse": round(mean_squared_error(y_test, y_pred), 4),
                    "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 4),
                    "mae": round(mean_absolute_error(y_test, y_pred), 4),
                    "r2": round(r2_score(y_test, y_pred), 4),
                }
                confusion = None
                confusion_labels = None
            
            # Feature importance
            feature_importance = []
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                for i, col in enumerate(X.columns):
                    feature_importance.append({
                        "feature": col,
                        "importance": round(float(importances[i]), 4),
                    })
                feature_importance.sort(key=lambda x: x["importance"], reverse=True)
            elif hasattr(model, 'coef_'):
                coefs = np.abs(model.coef_).flatten() if model.coef_.ndim > 1 else np.abs(model.coef_)
                for i, col in enumerate(X.columns[:len(coefs)]):
                    feature_importance.append({
                        "feature": col,
                        "importance": round(float(coefs[i]), 4),
                    })
                feature_importance.sort(key=lambda x: x["importance"], reverse=True)
            
            results.append(
                _build_result_payload(
                    model_id=model_id,
                    model_name=model_names.get(model_id, model_id),
                    metrics=metrics,
                    confusion_matrix=confusion,
                    confusion_labels=confusion_labels,
                    feature_importance=feature_importance[:10],
                    training_time=round(training_time, 2),
                )
            )
            _store_trained_model_artifact(
                session_id,
                db,
                model_id=model_id,
                model_name=model_names.get(model_id, model_id),
                model=model,
                target_column=request.target_column,
                problem_type=problem_type,
                feature_columns=X.columns.tolist(),
                metrics=metrics,
                training_time=round(training_time, 2),
            )
            db.commit()

        if not results:
            raise HTTPException(status_code=400, detail="No supported models were trained")

        primary_metric = "accuracy" if is_classification else "r2"
        results = sorted(results, key=lambda item: item["metrics"].get(primary_metric, 0), reverse=True)
        
        _store_training_metadata(
            session_id,
            target_column=request.target_column,
            problem_type=problem_type,
            results=results,
            active_job_id=None,
            db=db,
        )
        
        return {
            "success": True,
            "problem_type": problem_type,
            "results": results,
        }
        
    except HTTPException:
        raise
    except ImportError as e:
        logger.exception("Model training dependency missing for session %s", session_id)
        raise HTTPException(status_code=500, detail="Model eğitimi için gerekli bağımlılık eksik") from e
    except Exception as e:
        logger.exception("Model training failed for session %s", session_id)
        raise HTTPException(status_code=500, detail="Model eğitimi sırasında hata oluştu") from e


@router.get("/results")
async def get_results(
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Get training results"""
    results = session_manager.get_metadata(session_id, "training_results")
    problem_type = session_manager.get_metadata(session_id, "problem_type")
    target_column = session_manager.get_metadata(session_id, "training_target_column")
    active_job = _find_active_job_for_session(session_id)

    if not results:
        persisted_results, persisted_problem_type, persisted_target_column = _load_persisted_training_results(
            session_id,
            db,
        )
        if persisted_results:
            results = persisted_results
            problem_type = persisted_problem_type
            target_column = target_column or persisted_target_column
            _store_training_metadata(
                session_id,
                target_column=target_column,
                problem_type=problem_type,
                results=results,
                active_job_id=session_manager.get_metadata(session_id, "active_training_job_id"),
                db=db,
            )

    if not results and not active_job:
        return {"results": [], "problem_type": None, "target_column": target_column, "job": None}

    return {
        "results": results or (active_job["results"] if active_job else []),
        "problem_type": problem_type or (active_job["problem_type"] if active_job else None),
        "target_column": target_column,
        "job": active_job,
    }


@router.get("/comparison")
async def get_comparison(
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Get model comparison"""
    results = session_manager.get_metadata(session_id, "training_results")
    problem_type = session_manager.get_metadata(session_id, "problem_type")

    if not results:
        results, problem_type, _ = _load_persisted_training_results(session_id, db)

    if not results:
        return {"comparison": [], "best_model": None}

    # Sort by primary metric
    if problem_type == "classification":
        sorted_results = sorted(results, key=lambda x: x["metrics"].get("accuracy", 0), reverse=True)
        primary_metric = "accuracy"
    else:
        sorted_results = sorted(results, key=lambda x: x["metrics"].get("r2", 0), reverse=True)
        primary_metric = "r2"
    
    return {
        "comparison": sorted_results,
        "best_model": sorted_results[0] if sorted_results else None,
        "primary_metric": primary_metric,
    }


@router.get("/download-model")
async def download_trained_model(
    model_id: str,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Download a trained model artifact as a pickle file from PostgreSQL."""
    session = session_manager.get_session(session_id)
    user_id = session.get("owner_user_id") if session else None
    if not user_id:
        raise HTTPException(status_code=400, detail="Valid session ID required.")

    repo = TrainedModelRepository(db)
    record = repo.get_model_by_model_id(
        model_id=model_id,
        dataset_session_id=session_id,
        user_id=user_id,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Requested trained model was not found")

    return StreamingResponse(
        BytesIO(record.model_blob),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{record.model_id}_model.pkl"',
        },
    )
