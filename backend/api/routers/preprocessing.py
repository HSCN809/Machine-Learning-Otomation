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

router = APIRouter()


# Request schemas
class MissingValuesRequest(BaseModel):
    method: str  # fill_mean, fill_median, fill_mode, fill_knn, fill_interpolation, fill_regression, fill_constant, drop_rows, drop_columns
    columns: List[str]
    fill_value: Optional[str] = None


class OutliersRequest(BaseModel):
    method: str  # iqr_remove, iqr_cap, zscore_remove, zscore_cap
    columns: List[str]
    threshold: Optional[float] = 1.5


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
            elif request.method == "fill_constant":
                df[col] = df[col].fillna(request.fill_value)
            elif request.method == "fill_ffill":
                df[col] = df[col].ffill()
            elif request.method == "fill_bfill":
                df[col] = df[col].bfill()
            elif request.method == "drop_rows":
                df = df.dropna(subset=[col])
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
        affected_rows = 0
        
        for col in request.columns:
            if col not in df.columns or not np.issubdtype(df[col].dtype, np.number):
                continue
            
            if "iqr" in request.method:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - request.threshold * iqr
                upper = q3 + request.threshold * iqr
            elif "zscore" in request.method:
                mean = df[col].mean()
                std = df[col].std()
                lower = mean - request.threshold * std
                upper = mean + request.threshold * std
            else:
                continue
            
            outlier_mask = (df[col] < lower) | (df[col] > upper)
            affected_rows += int(outlier_mask.sum())
            
            if "remove" in request.method:
                df = df[~outlier_mask]
            elif "cap" in request.method:
                df.loc[df[col] < lower, col] = lower
                df.loc[df[col] > upper, col] = upper
        
        session_manager.set_dataframe(session_id, df)
        session_manager.add_history_snapshot(session_id, previous_df)
        session_manager.add_history(session_id, {
            "step": "outliers",
            "action": request.method,
            "columns": request.columns,
            "threshold": request.threshold,
            "affected_rows": affected_rows,
        })
        
        return {
            "success": True,
            "method": request.method,
            "columns": request.columns,
            "affected_rows": affected_rows,
            "remaining_rows": len(df),
        }
        
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
