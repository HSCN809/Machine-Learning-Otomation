"""
Model Router - Model training and evaluation endpoints
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ..dependencies import session_manager, require_session

try:
    import xgboost as xgb
except ImportError:
    xgb = None

router = APIRouter()


# Request schemas
class TrainRequest(BaseModel):
    target_column: str
    models: List[str]
    test_size: float = 0.2
    params: Optional[Dict[str, Dict[str, Any]]] = None


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
    
    # Determine problem type
    if target.dtype == 'object' or target.dtype.name == 'category':
        problem_type = "classification"
    elif unique_count <= 10:
        problem_type = "classification"
    else:
        problem_type = "regression"
    
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


@router.post("/train")
async def train_models(
    request: TrainRequest,
    session_id: str = Depends(require_session)
):
    """Train selected models"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    if request.target_column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Target column '{request.target_column}' not found")
    
    try:
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
            mean_squared_error, mean_absolute_error, r2_score
        )
        
        # Prepare data
        X = df.drop(columns=[request.target_column])
        y = df[request.target_column]
        original_target = y.copy()
        class_label_lookup: Optional[List[str]] = None
        
        # Handle categorical features
        X = pd.get_dummies(X, drop_first=True)
        
        # Handle categorical target for classification
        if y.dtype == 'object' or y.dtype.name == 'category':
            categorical_target = y.astype('category')
            class_label_lookup = [str(label) for label in categorical_target.cat.categories.tolist()]
            y = categorical_target.cat.codes
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=request.test_size, random_state=42
        )
        
        # Detect problem type
        unique_count = y.nunique()
        is_classification = unique_count <= 10 or original_target.dtype == 'object' or original_target.dtype.name == 'category'
        
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
                except:
                    pass
                
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
            
            results.append({
                "model_id": model_id,
                "model_name": model_names.get(model_id, model_id),
                "metrics": metrics,
                "confusion_matrix": confusion,
                "confusion_labels": confusion_labels,
                "feature_importance": feature_importance[:10],  # Top 10
                "training_time": round(training_time, 2),
            })

        if not results:
            raise HTTPException(status_code=400, detail="No supported models were trained")

        primary_metric = "accuracy" if is_classification else "r2"
        results = sorted(results, key=lambda item: item["metrics"].get(primary_metric, 0), reverse=True)
        
        # Store results in session
        session_manager.set_metadata(session_id, "training_results", results)
        session_manager.set_metadata(session_id, "problem_type", "classification" if is_classification else "regression")
        
        return {
            "success": True,
            "problem_type": "classification" if is_classification else "regression",
            "results": results,
        }
        
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Missing sklearn: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results")
async def get_results(session_id: str = Depends(require_session)):
    """Get training results"""
    results = session_manager.get_metadata(session_id, "training_results")
    problem_type = session_manager.get_metadata(session_id, "problem_type")
    
    if not results:
        return {"results": [], "problem_type": None}
    
    return {"results": results, "problem_type": problem_type}


@router.get("/comparison")
async def get_comparison(session_id: str = Depends(require_session)):
    """Get model comparison"""
    results = session_manager.get_metadata(session_id, "training_results")
    problem_type = session_manager.get_metadata(session_id, "problem_type")
    
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
