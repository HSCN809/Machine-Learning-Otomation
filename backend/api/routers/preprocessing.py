"""
Preprocessing Router - Data preprocessing endpoints
"""

import ast
from io import BytesIO
import logging
import os
import sys
from typing import Any, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ..dependencies import get_db, persist_session, require_session, session_manager
from backend.modules.data_preprocessing.feature_engineering.processor import (
    create_binned_feature,
    create_categorical_combination,
    create_datetime_feature,
    create_numeric_feature,
    drop_columns,
)
from backend.modules.data_preprocessing.encoding.processor import binary_encode
from backend.modules.data_preprocessing.missing_values.processor import (
    fill_missing_values_interpolation,
    fill_missing_values_knn,
    fill_missing_values_regression,
)
from backend.modules.data_preprocessing.outlier.analyzer import analyze_outliers
from backend.modules.data_preprocessing.outlier.processor import apply_outlier_method
from backend.modules.data_preprocessing.scaling.processor import apply_scaling_method

router = APIRouter()


def _raise_internal_error(log_message: str, user_message: str, exc: Exception, session_id: str) -> None:
    logger.exception("%s failed for session %s", log_message, session_id)
    raise HTTPException(status_code=500, detail=user_message) from exc


def _record_preprocessing_timeline_event(
    session_id: str,
    *,
    action: str,
    payload: dict[str, Any],
    previous_df: pd.DataFrame,
    title: str,
    description: str,
) -> None:
    event = session_manager.add_timeline_event(
        session_id,
        {
            "category": "preprocessing",
            "action": action,
            "title": title,
            "description": description,
            "undoable": True,
            "metadata": dict(payload),
            "payload": dict(payload),
            "step": payload.get("step"),
        },
    )
    session_manager.add_timeline_snapshot(session_id, event["id"], previous_df)


# Request schemas
class MissingValuesRequest(BaseModel):
    method: str  # fill_mean, fill_median, fill_mode, fill_knn, fill_interpolation, fill_regression, fill_ffill, fill_bfill, drop_columns
    columns: List[str]


class OutliersRequest(BaseModel):
    method: str  # iqr_cap, iqr_winsorize
    columns: List[str]
    threshold: Optional[float] = None
    winsorize_percent: Optional[float] = Field(default=None, ge=0.1, le=49.9)


class OutlierAnalysisRequest(BaseModel):
    method: str
    columns: Optional[List[str]] = None
    threshold: Optional[float] = None
    winsorize_percent: Optional[float] = Field(default=None, ge=0.1, le=49.9)


class EncodingRequest(BaseModel):
    method: str  # label, onehot, ordinal
    columns: List[str]
    drop_first: Optional[bool] = True
    ordinal_mapping: Optional[dict[str, int]] = None


class ScalingRequest(BaseModel):
    method: str  # standard, minmax, robust
    columns: List[str]
    feature_range: Optional[tuple[float, float]] = None


class FeatureRequest(BaseModel):
    operation: str  # create_numeric, polynomial, binning, create_datetime, create_categorical
    source_columns: List[str]
    new_column_name: Optional[str] = None
    expression: Optional[str] = None
    params: dict[str, Any] = Field(default_factory=dict)


class UndoToHistoryRequest(BaseModel):
    history_index: int = Field(ge=0)


class DropColumnsRequest(BaseModel):
    columns: List[str]
    reason: Optional[str] = None


ALLOWED_EXPRESSION_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Name,
    ast.Load,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.Constant,
)

SUPPORTED_MISSING_VALUE_METHODS = {
    "fill_mean",
    "fill_median",
    "fill_mode",
    "fill_knn",
    "fill_interpolation",
    "fill_regression",
    "fill_ffill",
    "fill_bfill",
    "drop_columns",
}


def _parse_outlier_method(method: str) -> str:
    normalized = (method or "").strip().lower()

    if normalized == "iqr":
        return "iqr_cap"
    if normalized in {"iqr_cap", "iqr_winsorize"}:
        return normalized
    raise HTTPException(status_code=400, detail=f"Unsupported outlier method: {method}")


def _analyze_outliers_for_columns(
    df: pd.DataFrame,
    method: str,
    requested_columns: Optional[List[str]],
    threshold: Optional[float],
) -> dict[str, Any]:
    parsed_method = _parse_outlier_method(method)
    source_columns = requested_columns or df.columns.tolist()
    numeric_columns = [
        col for col in source_columns if col in df.columns and np.issubdtype(df[col].dtype, np.number)
    ]

    if not numeric_columns:
        return {
            "detection_method": "iqr",
            "outlier_method": parsed_method,
            "numeric_columns": [],
            "detected_columns": [],
            "column_stats": [],
            "total_outliers": 0,
            "total_rows": len(df),
            "outlier_row_count": 0,
            "outlier_row_percentage": 0.0,
        }

    analysis_kwargs: dict[str, Any] = {}
    resolved_threshold: Optional[float] = threshold

    if parsed_method in {"iqr_cap", "iqr_winsorize"}:
        resolved_threshold = 1.5 if resolved_threshold is None else resolved_threshold
        analysis_kwargs["factor"] = resolved_threshold

    analysis_result = analyze_outliers(
        df,
        columns=numeric_columns,
        method="iqr",
        **analysis_kwargs,
    )
    outliers_by_column = analysis_result.get("outliers_by_column", {})
    outlier_rows = analysis_result.get("outlier_rows", set())
    if isinstance(outlier_rows, set):
        outlier_row_count = len(outlier_rows)
    elif isinstance(outlier_rows, (list, tuple)):
        outlier_row_count = len(outlier_rows)
    else:
        outlier_row_count = 0
    total_rows = len(df)
    outlier_row_percentage = round((outlier_row_count / total_rows * 100), 2) if total_rows > 0 else 0.0

    column_stats: list[dict[str, Any]] = []
    detected_columns: list[str] = []
    for col in numeric_columns:
        info = outliers_by_column.get(col, {})
        outlier_count = int(info.get("count", 0))
        outlier_percentage = round(float(info.get("percentage", 0.0)), 2)
        if outlier_count <= 0:
            continue

        detected_columns.append(col)
        column_stats.append(
            {
                "column": col,
                "outlier_count": outlier_count,
                "outlier_percentage": outlier_percentage,
            }
        )

    return {
        "detection_method": "iqr",
        "outlier_method": parsed_method,
        "numeric_columns": numeric_columns,
        "detected_columns": detected_columns,
        "column_stats": column_stats,
        "total_outliers": int(analysis_result.get("total_outliers", 0)),
        "total_rows": total_rows,
        "outlier_row_count": outlier_row_count,
        "outlier_row_percentage": outlier_row_percentage,
        "resolved_threshold": resolved_threshold,
    }


def _validate_expression(expression: str, allowed_names: set[str]) -> ast.Expression:
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError as exc:
        raise HTTPException(status_code=400, detail='Invalid numeric expression') from exc

    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_EXPRESSION_NODES):
            raise HTTPException(status_code=400, detail='Only basic arithmetic expressions are allowed')
        if isinstance(node, ast.Name) and node.id not in allowed_names:
            raise HTTPException(status_code=400, detail=f'Unknown column in expression: {node.id}')

    return tree


@router.post("/missing-values")
async def handle_missing_values(
    request: MissingValuesRequest,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Handle missing values"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        previous_df = df.copy(deep=True)
        affected_rows = 0

        if request.method not in SUPPORTED_MISSING_VALUE_METHODS:
            raise HTTPException(status_code=400, detail=f"Unsupported missing values method: {request.method}")
        
        valid_columns = [col for col in request.columns if col in df.columns]
        skipped_columns = [col for col in request.columns if col not in df.columns]
        if skipped_columns:
            logger.warning("Missing value preprocessing skipped unknown columns for session %s: %s", session_id, skipped_columns)
        if not valid_columns:
            raise HTTPException(status_code=400, detail="İşlem için geçerli sütun bulunamadı")

        for col in valid_columns:
            if col not in df.columns:
                continue
            
            initial_nulls = df[col].isnull().sum()
            
            if request.method == "fill_mean":
                if np.issubdtype(df[col].dtype, np.number):
                    df[col] = df[col].fillna(df[col].mean())
            elif request.method == "fill_median":
                if np.issubdtype(df[col].dtype, np.number):
                    df[col] = df[col].fillna(df[col].median())
            elif request.method == "fill_mode":
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val.iloc[0])
            elif request.method == "fill_knn":
                df = fill_missing_values_knn(df, [col])
            elif request.method == "fill_interpolation":
                df = fill_missing_values_interpolation(df, [col], method="linear")
            elif request.method == "fill_regression":
                df = fill_missing_values_regression(df, [col])
            elif request.method == "fill_ffill":
                df[col] = df[col].ffill()
            elif request.method == "fill_bfill":
                df[col] = df[col].bfill()
            elif request.method == "drop_columns":
                if df[col].isnull().sum() > 0:
                    df = df.drop(columns=[col])
            
            affected_rows += int(initial_nulls)
        
        history_payload = {
            "step": "missing_values",
            "action": request.method,
            "columns": valid_columns,
            "params": {
                "skipped_columns": skipped_columns,
            },
            "affected_rows": affected_rows,
        }
        session_manager.set_dataframe(session_id, df)
        session_manager.add_history_snapshot(session_id, previous_df)
        session_manager.add_history(session_id, dict(history_payload))
        _record_preprocessing_timeline_event(
            session_id,
            action=request.method,
            payload=history_payload,
            previous_df=previous_df,
            title="Eksik değer işlemi uygulandı",
            description=f"{len(valid_columns)} sütunda {request.method} işlemi uygulandı.",
        )
        persist_session(session_id, db)
        
        return {
            "success": True,
            "method": request.method,
            "columns": valid_columns,
            "skipped_columns": skipped_columns,
            "affected_rows": affected_rows,
            "remaining_nulls": int(df.isnull().sum().sum()),
        }

    except HTTPException:
        raise
    except Exception as e:
        _raise_internal_error("Missing value preprocessing", "Eksik değer işlemi sırasında hata oluştu", e, session_id)


@router.post("/outliers")
async def handle_outliers(
    request: OutliersRequest,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Handle outliers"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        previous_df = df.copy(deep=True)
        analysis = _analyze_outliers_for_columns(
            df=df,
            method=request.method,
            requested_columns=request.columns,
            threshold=request.threshold,
        )
        outlier_method = _parse_outlier_method(request.method)
        detected_columns = analysis["detected_columns"]

        if not detected_columns:
            return {
                "success": True,
                "method": request.method,
                "columns": [],
                "requested_columns": request.columns,
                "affected_rows": 0,
                "remaining_rows": len(df),
            }

        process_kwargs: dict[str, Any] = {}
        resolved_threshold = analysis.get("resolved_threshold")
        if outlier_method in {"iqr_cap", "iqr_winsorize"} and resolved_threshold is not None:
            process_kwargs["factor"] = resolved_threshold
        if outlier_method == "iqr_winsorize":
            process_kwargs["tail_percent"] = (
                request.winsorize_percent if request.winsorize_percent is not None else 5.0
            )

        processed_df = apply_outlier_method(
            df,
            detected_columns,
            method=outlier_method,
            **process_kwargs,
        )

        affected_rows = int(analysis.get("total_outliers", 0))

        history_payload = {
            "step": "outliers",
            "action": request.method,
            "columns": detected_columns,
            "requested_columns": request.columns,
            "threshold": resolved_threshold,
            "winsorize_percent": request.winsorize_percent if outlier_method == "iqr_winsorize" else None,
            "affected_rows": affected_rows,
        }
        session_manager.set_dataframe(session_id, processed_df)
        session_manager.add_history_snapshot(session_id, previous_df)
        session_manager.add_history(session_id, dict(history_payload))
        _record_preprocessing_timeline_event(
            session_id,
            action=request.method,
            payload=history_payload,
            previous_df=previous_df,
            title="Aykırı değer işlemi uygulandı",
            description=f"{len(detected_columns)} sütunda aykırı değer işlemi uygulandı.",
        )
        persist_session(session_id, db)
        
        return {
            "success": True,
            "method": request.method,
            "columns": detected_columns,
            "requested_columns": request.columns,
            "affected_rows": affected_rows,
            "remaining_rows": len(processed_df),
            "winsorize_percent": request.winsorize_percent if outlier_method == "iqr_winsorize" else None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        _raise_internal_error("Outlier preprocessing", "Aykırı değer işlemi sırasında hata oluştu", e, session_id)


@router.post("/outliers/analyze")
async def analyze_outlier_columns(
    request: OutlierAnalysisRequest,
    session_id: str = Depends(require_session)
):
    """Analyze outliers for requested method and return only columns with outliers."""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")

    try:
        analysis = _analyze_outliers_for_columns(
            df=df,
            method=request.method,
            requested_columns=request.columns,
            threshold=request.threshold,
        )

        return {
            "success": True,
            "method": request.method,
            "detection_method": analysis["detection_method"],
            "outlier_method": analysis["outlier_method"],
            "threshold": analysis.get("resolved_threshold"),
            "detected_columns": analysis["detected_columns"],
            "columns": analysis["column_stats"],
            "total_outliers": analysis["total_outliers"],
            "total_rows": analysis["total_rows"],
            "outlier_row_count": analysis["outlier_row_count"],
            "outlier_row_percentage": analysis["outlier_row_percentage"],
        }
    except HTTPException:
        raise
    except Exception as e:
        _raise_internal_error("Outlier analysis", "Aykırı değer analizi sırasında hata oluştu", e, session_id)


@router.post("/encoding")
async def handle_encoding(
    request: EncodingRequest,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Handle categorical encoding"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        previous_df = df.copy(deep=True)
        new_columns = []
        
        valid_columns = [col for col in request.columns if col in df.columns]
        skipped_columns = [col for col in request.columns if col not in df.columns]
        if skipped_columns:
            logger.warning("Encoding skipped unknown columns for session %s: %s", session_id, skipped_columns)
        if not valid_columns:
            raise HTTPException(status_code=400, detail="İşlem için geçerli sütun bulunamadı")

        for col in valid_columns:
            if col not in df.columns:
                continue
            
            if request.method == "label":
                df[col] = df[col].astype('category').cat.codes
            elif request.method == "onehot":
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=request.drop_first)
                df = df.drop(columns=[col])
                df = pd.concat([df, dummies], axis=1)
                new_columns.extend(dummies.columns.tolist())
            elif request.method == "ordinal":
                if request.ordinal_mapping:
                    df[col] = df[col].map(request.ordinal_mapping)
                else:
                    df[col] = df[col].astype('category').cat.codes
            elif request.method == "binary":
                previous_columns = set(df.columns.tolist())
                df = binary_encode(df, [col])
                new_columns.extend(
                    [column_name for column_name in df.columns if column_name not in previous_columns]
                )
            elif request.method == "frequency":
                freq_map = df[col].value_counts(normalize=True).to_dict()
                df[col] = df[col].map(freq_map)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported encoding method: {request.method}")
        
        history_payload = {
            "step": "encoding",
            "action": request.method,
            "columns": valid_columns,
            "new_columns": new_columns,
            "params": {
                "drop_first": request.drop_first if request.method == "onehot" else None,
                "ordinal_mapping": request.ordinal_mapping if request.method == "ordinal" else None,
                "skipped_columns": skipped_columns,
            },
        }
        session_manager.set_dataframe(session_id, df)
        session_manager.add_history_snapshot(session_id, previous_df)
        session_manager.add_history(session_id, dict(history_payload))
        _record_preprocessing_timeline_event(
            session_id,
            action=request.method,
            payload=history_payload,
            previous_df=previous_df,
            title="Kodlama işlemi uygulandı",
            description=f"{len(valid_columns)} sütunda {request.method} kodlama işlemi uygulandı.",
        )
        persist_session(session_id, db)
        
        return {
            "success": True,
            "method": request.method,
            "columns": valid_columns,
            "skipped_columns": skipped_columns,
            "new_columns": new_columns,
            "total_columns": len(df.columns),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        _raise_internal_error("Encoding preprocessing", "Kodlama işlemi sırasında hata oluştu", e, session_id)


@router.post("/scaling")
async def handle_scaling(
    request: ScalingRequest,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Handle feature scaling"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        previous_df = df.copy(deep=True)
        valid_columns = [
            col for col in request.columns if col in df.columns and np.issubdtype(df[col].dtype, np.number)
        ]
        skipped_columns = [col for col in request.columns if col not in valid_columns]
        if skipped_columns:
            logger.warning("Scaling skipped invalid columns for session %s: %s", session_id, skipped_columns)
        if not valid_columns:
            raise HTTPException(status_code=400, detail="Ölçeklendirme için geçerli sayısal sütun bulunamadı")

        if request.method == "standard":
            df = apply_scaling_method(df, valid_columns, "standard_scaler")
        elif request.method == "minmax":
            scaling_kwargs: dict[str, Any] = {}
            if request.feature_range is not None:
                scaling_kwargs["feature_range"] = tuple(request.feature_range)
            df = apply_scaling_method(df, valid_columns, "minmax_scaler", **scaling_kwargs)
        elif request.method == "robust":
            df = apply_scaling_method(df, valid_columns, "robust_scaler")
        elif request.method == "maxabs":
            df = apply_scaling_method(df, valid_columns, "maxabs_scaler")
        elif request.method == "normalizer":
            df = apply_scaling_method(df, valid_columns, "normalizer")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported scaling method: {request.method}")
        
        history_payload = {
            "step": "scaling",
            "action": request.method,
            "columns": valid_columns,
            "params": {
                "feature_range": list(request.feature_range) if request.feature_range is not None else None,
                "skipped_columns": skipped_columns,
            },
        }
        session_manager.set_dataframe(session_id, df)
        session_manager.add_history_snapshot(session_id, previous_df)
        session_manager.add_history(session_id, dict(history_payload))
        _record_preprocessing_timeline_event(
            session_id,
            action=request.method,
            payload=history_payload,
            previous_df=previous_df,
            title="Ölçeklendirme işlemi uygulandı",
            description=f"{len(valid_columns)} sayısal sütunda {request.method} ölçeklendirme uygulandı.",
        )
        persist_session(session_id, db)
        
        return {
            "success": True,
            "method": request.method,
            "columns": valid_columns,
            "skipped_columns": skipped_columns,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        _raise_internal_error("Scaling preprocessing", "Ölçeklendirme işlemi sırasında hata oluştu", e, session_id)


@router.post("/feature-engineering")
async def handle_feature_engineering(
    request: FeatureRequest,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Create new features"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        previous_df = df.copy(deep=True)
        params = request.params or {}
        new_columns: List[str] = []
        history_payload: dict[str, Any] = {
            "step": "feature_engineering",
            "action": request.operation,
            "source_columns": request.source_columns,
            "params": params,
        }

        if request.operation == "polynomial":
            for col in request.source_columns:
                if col in df.columns and np.issubdtype(df[col].dtype, np.number):
                    generated_column = f"{col}_squared"
                    df[generated_column] = df[col] ** 2
                    new_columns.append(generated_column)
        elif request.operation == "create_numeric":
            new_column_name = (request.new_column_name or "").strip()
            if not new_column_name:
                raise HTTPException(status_code=400, detail="New column name is required")

            numeric_operation = params.get("numericOperation")
            if numeric_operation == "custom":
                expression = (request.expression or "").strip()
                if not expression:
                    raise HTTPException(status_code=400, detail="Expression is required for custom numeric operation")

                _validate_expression(expression, set(request.source_columns))
                safe_scope = {col: df[col] for col in request.source_columns if col in df.columns}
                df[new_column_name] = eval(expression, {"__builtins__": {}}, safe_scope)
            else:
                if numeric_operation not in {"add", "subtract", "multiply", "divide"}:
                    raise HTTPException(status_code=400, detail="Invalid numeric operation")
                df = create_numeric_feature(df, numeric_operation, request.source_columns, new_column_name)

            new_columns.append(new_column_name)
        elif request.operation == "binning":
            new_column_name = (request.new_column_name or "").strip()
            if not new_column_name:
                raise HTTPException(status_code=400, detail="New column name is required")
            if len(request.source_columns) != 1:
                raise HTTPException(status_code=400, detail="Binning requires exactly one source column")

            df = create_binned_feature(
                df,
                request.source_columns[0],
                new_column_name,
                str(params.get("strategy", "equal_width")),
                int(params.get("binCount", 5)),
            )
            new_columns.append(new_column_name)
        elif request.operation == "create_datetime":
            new_column_name = (request.new_column_name or "").strip()
            if not new_column_name:
                raise HTTPException(status_code=400, detail="New column name is required")
            if len(request.source_columns) != 1:
                raise HTTPException(status_code=400, detail="Datetime feature requires exactly one source column")

            df = create_datetime_feature(
                df,
                request.source_columns[0],
                str(params.get("datetimePart", "year")),
                new_column_name,
            )
            new_columns.append(new_column_name)
        elif request.operation == "create_categorical":
            new_column_name = (request.new_column_name or "").strip()
            if not new_column_name:
                raise HTTPException(status_code=400, detail="New column name is required")

            df = create_categorical_combination(
                df,
                request.source_columns,
                new_column_name,
                str(params.get("separator", "_")),
            )
            new_columns.append(new_column_name)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported feature engineering operation: {request.operation}")

        session_manager.set_dataframe(session_id, df)
        session_manager.add_history_snapshot(session_id, previous_df)
        history_payload["new_columns"] = new_columns
        session_manager.add_history(session_id, dict(history_payload))
        _record_preprocessing_timeline_event(
            session_id,
            action=request.operation,
            payload=history_payload,
            previous_df=previous_df,
            title="Özellik mühendisliği işlemi uygulandı",
            description=f"{request.operation} işlemi ile {len(new_columns)} yeni sütun oluşturuldu.",
        )
        persist_session(session_id, db)

        return {
            "success": True,
            "operation": request.operation,
            "new_columns": new_columns,
            "total_columns": len(df.columns),
        }

    except HTTPException:
        raise
    except Exception as e:
        _raise_internal_error("Feature engineering preprocessing", "Özellik mühendisliği işlemi sırasında hata oluştu", e, session_id)


@router.get("/history")
async def get_history(session_id: str = Depends(require_session)):
    """Get preprocessing history"""
    history = session_manager.get_history(session_id)
    return {"history": history}


@router.post("/drop-columns")
async def handle_drop_columns(
    request: DropColumnsRequest,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Drop specified columns from the dataframe"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        previous_df = df.copy(deep=True)
        
        existing_columns = [col for col in request.columns if col in df.columns]
        missing_columns = [col for col in request.columns if col not in df.columns]
        
        if missing_columns:
            logger.warning(f"⚠️ Columns not found: {missing_columns}")
        
        if not existing_columns:
            raise HTTPException(status_code=400, detail="No valid columns to drop")
        
        df = drop_columns(df, existing_columns)
        
        history_payload = {
            "step": "feature_engineering",
            "action": "drop_columns",
            "columns": existing_columns,
            "reason": request.reason,
        }
        session_manager.set_dataframe(session_id, df)
        session_manager.add_history_snapshot(session_id, previous_df)
        session_manager.add_history(session_id, dict(history_payload))
        _record_preprocessing_timeline_event(
            session_id,
            action="drop_columns",
            payload=history_payload,
            previous_df=previous_df,
            title="Sütunlar silindi",
            description=f"{len(existing_columns)} sütun veri setinden kaldırıldı.",
        )
        persist_session(session_id, db)
        
        return {
            "success": True,
            "dropped_columns": existing_columns,
            "missing_columns": missing_columns,
            "total_columns": len(df.columns),
            "remaining_rows": len(df),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        _raise_internal_error("Drop columns preprocessing", "Sütun silme işlemi sırasında hata oluştu", e, session_id)


@router.get("/drop-columns/analyze")
async def analyze_droppable_columns(
    cardinality_threshold: float = 0.9,
    session_id: str = Depends(require_session)
):
    """Analyze columns for potential removal recommendations"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        total_rows = len(df)
        recommendations = []
        
        for col in df.columns:
            unique_count = df[col].nunique()
            unique_ratio = unique_count / total_rows if total_rows > 0 else 0
            
            recommendation = {
                "column": col,
                "unique_count": int(unique_count),
                "unique_ratio": round(unique_ratio, 4),
                "missing_count": int(df[col].isnull().sum()),
                "missing_percentage": round(df[col].isnull().sum() / total_rows * 100, 2) if total_rows > 0 else 0,
                "reasons": [],
            }
            
            missing_pct = round(df[col].isnull().sum() / total_rows * 100, 2) if total_rows > 0 else 0
            
            if unique_count == 1:
                recommendation["reasons"].append("Sabit değer")
            
            if missing_pct > 50:
                recommendation["reasons"].append(f"Yüksek eksik değer ({missing_pct}%)")
            
            if pd.api.types.is_numeric_dtype(df[col]):
                variance = df[col].var()
                if variance == 0:
                    recommendation["reasons"].append("Düşük varyans")
            
            if unique_ratio > cardinality_threshold:
                recommendation["reasons"].append(f"Yüksek kardinalite ({int(unique_ratio * 100)}%)")
            
            if recommendation["reasons"]:
                recommendations.append(recommendation)
        
        recommended_columns = [r["column"] for r in recommendations]
        
        return {
            "success": True,
            "recommendations": recommendations,
            "recommended_columns": recommended_columns,
            "all_columns": list(df.columns),
            "cardinality_threshold": cardinality_threshold,
        }
        
    except Exception as e:
        _raise_internal_error("Droppable columns analysis", "Silinebilir sütun analizi sırasında hata oluştu", e, session_id)


@router.post("/undo")
async def undo_last_preprocessing(
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Undo the last preprocessing action"""
    undone_action = session_manager.undo_last_history_action(session_id)
    current_df = session_manager.get_dataframe(session_id)
    if current_df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    persist_session(session_id, db)
    logger.info("Preprocessing undo applied for session %s: action=%s", session_id, undone_action.get("action"))

    return {
        "success": True,
        "message": "Last preprocessing action was undone",
        "undone_action": undone_action,
        "rows": len(current_df),
        "columns": len(current_df.columns),
    }


@router.post("/undo-to")
async def undo_to_history_item(
    request: UndoToHistoryRequest,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Undo the selected preprocessing action and all newer actions"""
    undo_result = session_manager.undo_to_history_index(session_id, request.history_index)
    current_df = session_manager.get_dataframe(session_id)
    if current_df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    persist_session(session_id, db)
    logger.info(
        "Preprocessing undo-to applied for session %s: history_index=%s undone_count=%s",
        session_id,
        request.history_index,
        len(undo_result["undone_actions"]),
    )

    return {
        "success": True,
        "message": "Selected preprocessing history was undone",
        "undone_count": len(undo_result["undone_actions"]),
        "remaining_history_count": undo_result["remaining_history_count"],
        "rows": len(current_df),
        "columns": len(current_df.columns),
    }


@router.post("/reset")
async def reset_data(
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Reset to original data"""
    original_df = session_manager.get_original_dataframe(session_id)
    if original_df is None:
        raise HTTPException(status_code=400, detail="No original data found")
    
    session_manager.set_dataframe(session_id, original_df.copy())
    session = session_manager.get_session(session_id)
    if session:
        remaining_events = [
            event
            for event in session.get("timeline_events", [])
            if event.get("category") != "preprocessing"
        ]
        remaining_event_ids = {event.get("id") for event in remaining_events}
        session["timeline_events"] = remaining_events
        session["timeline_snapshots"] = [
            snapshot
            for snapshot in session.get("timeline_snapshots", [])
            if snapshot.get("event_id") in remaining_event_ids
        ]
        session["history"] = []
        session["history_snapshots"] = []
    persist_session(session_id, db)
    logger.info("Preprocessing reset applied for session %s", session_id)
    
    return {
        "success": True,
        "message": "Data reset to original",
        "rows": len(original_df),
        "columns": len(original_df.columns),
    }


@router.get("/export")
async def export_processed_data(session_id: str = Depends(require_session)):
    """Export the current processed dataframe as an Excel file."""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="processed_data")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="processed_data.xlsx"',
        },
    )
