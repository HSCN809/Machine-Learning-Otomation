"""
Preprocessing Router - Data preprocessing endpoints
"""

import ast
import os
import sys
from typing import Any, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ..dependencies import session_manager, require_session
from backend.modules.data_preprocessing.feature_engineering.processor import (
    create_binned_feature,
    create_categorical_combination,
    create_datetime_feature,
    create_numeric_feature,
)
from backend.modules.data_preprocessing.missing_values.processor import (
    fill_missing_values_interpolation,
    fill_missing_values_knn,
    fill_missing_values_regression,
)
from backend.modules.data_preprocessing.outlier.analyzer import analyze_outliers
from backend.modules.data_preprocessing.outlier.processor import apply_outlier_method

router = APIRouter()


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


class ScalingRequest(BaseModel):
    method: str  # standard, minmax, robust
    columns: List[str]


class FeatureRequest(BaseModel):
    operation: str  # create_numeric, polynomial, binning, create_datetime, create_categorical
    source_columns: List[str]
    new_column_name: Optional[str] = None
    expression: Optional[str] = None
    params: dict[str, Any] = Field(default_factory=dict)


class UndoToHistoryRequest(BaseModel):
    history_index: int = Field(ge=0)


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
    session_id: str = Depends(require_session)
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
        
        for col in request.columns:
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
        
        session_manager.set_dataframe(session_id, df)
        session_manager.add_history_snapshot(session_id, previous_df)
        session_manager.add_history(session_id, {
            "step": "missing_values",
            "action": request.method,
            "columns": request.columns,
            "affected_rows": affected_rows,
        })
        
        return {
            "success": True,
            "method": request.method,
            "columns": request.columns,
            "affected_rows": affected_rows,
            "remaining_nulls": int(df.isnull().sum().sum()),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outliers")
async def handle_outliers(
    request: OutliersRequest,
    session_id: str = Depends(require_session)
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

        session_manager.set_dataframe(session_id, processed_df)
        session_manager.add_history_snapshot(session_id, previous_df)
        session_manager.add_history(session_id, {
            "step": "outliers",
            "action": request.method,
            "columns": detected_columns,
            "requested_columns": request.columns,
            "threshold": resolved_threshold,
            "winsorize_percent": request.winsorize_percent if outlier_method == "iqr_winsorize" else None,
            "affected_rows": affected_rows,
        })
        
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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/encoding")
async def handle_encoding(
    request: EncodingRequest,
    session_id: str = Depends(require_session)
):
    """Handle categorical encoding"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        previous_df = df.copy(deep=True)
        new_columns = []
        
        for col in request.columns:
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
                df[col] = df[col].astype('category').cat.codes
            elif request.method == "frequency":
                freq_map = df[col].value_counts(normalize=True).to_dict()
                df[col] = df[col].map(freq_map)
        
        session_manager.set_dataframe(session_id, df)
        session_manager.add_history_snapshot(session_id, previous_df)
        session_manager.add_history(session_id, {
            "step": "encoding",
            "action": request.method,
            "columns": request.columns,
            "new_columns": new_columns,
        })
        
        return {
            "success": True,
            "method": request.method,
            "columns": request.columns,
            "new_columns": new_columns,
            "total_columns": len(df.columns),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scaling")
async def handle_scaling(
    request: ScalingRequest,
    session_id: str = Depends(require_session)
):
    """Handle feature scaling"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        previous_df = df.copy(deep=True)
        for col in request.columns:
            if col not in df.columns or not np.issubdtype(df[col].dtype, np.number):
                continue
            
            if request.method == "standard":
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    df[col] = (df[col] - mean) / std
            elif request.method == "minmax":
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val > min_val:
                    df[col] = (df[col] - min_val) / (max_val - min_val)
            elif request.method == "robust":
                median = df[col].median()
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    df[col] = (df[col] - median) / iqr
        
        session_manager.set_dataframe(session_id, df)
        session_manager.add_history_snapshot(session_id, previous_df)
        session_manager.add_history(session_id, {
            "step": "scaling",
            "action": request.method,
            "columns": request.columns,
        })
        
        return {
            "success": True,
            "method": request.method,
            "columns": request.columns,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feature-engineering")
async def handle_feature_engineering(
    request: FeatureRequest,
    session_id: str = Depends(require_session)
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
        session_manager.add_history(session_id, history_payload)

        return {
            "success": True,
            "operation": request.operation,
            "new_columns": new_columns,
            "total_columns": len(df.columns),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(session_id: str = Depends(require_session)):
    """Get preprocessing history"""
    history = session_manager.get_history(session_id)
    return {"history": history}


@router.post("/undo")
async def undo_last_preprocessing(session_id: str = Depends(require_session)):
    """Undo the last preprocessing action"""
    undone_action = session_manager.undo_last_history_action(session_id)
    current_df = session_manager.get_dataframe(session_id)
    if current_df is None:
        raise HTTPException(status_code=400, detail="No data loaded")

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
    session_id: str = Depends(require_session)
):
    """Undo the selected preprocessing action and all newer actions"""
    undo_result = session_manager.undo_to_history_index(session_id, request.history_index)
    current_df = session_manager.get_dataframe(session_id)
    if current_df is None:
        raise HTTPException(status_code=400, detail="No data loaded")

    return {
        "success": True,
        "message": "Selected preprocessing history was undone",
        "undone_count": len(undo_result["undone_actions"]),
        "remaining_history_count": undo_result["remaining_history_count"],
        "rows": len(current_df),
        "columns": len(current_df.columns),
    }


@router.post("/reset")
async def reset_data(session_id: str = Depends(require_session)):
    """Reset to original data"""
    original_df = session_manager.get_original_dataframe(session_id)
    if original_df is None:
        raise HTTPException(status_code=400, detail="No original data found")
    
    session_manager.set_dataframe(session_id, original_df.copy())
    session = session_manager.get_session(session_id)
    if session:
        session["history"] = []
        session["history_snapshots"] = []
    
    return {
        "success": True,
        "message": "Data reset to original",
        "rows": len(original_df),
        "columns": len(original_df.columns),
    }
