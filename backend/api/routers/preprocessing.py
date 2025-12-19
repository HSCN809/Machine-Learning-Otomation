"""
Preprocessing Router - Data preprocessing endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ..dependencies import session_manager, require_session

router = APIRouter()


# Request schemas
class MissingValuesRequest(BaseModel):
    method: str  # fill_mean, fill_median, fill_mode, fill_constant, drop_rows, drop_columns
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
    operation: str  # create_numeric, polynomial
    source_columns: List[str]
    new_column_name: str
    expression: Optional[str] = None


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
        if request.operation == "polynomial":
            for col in request.source_columns:
                if col in df.columns and np.issubdtype(df[col].dtype, np.number):
                    df[f"{col}_squared"] = df[col] ** 2
        elif request.operation == "create_numeric" and request.expression:
            # Simple expression evaluation (be careful with security)
            # Only allow basic math operations
            df[request.new_column_name] = eval(request.expression, {"__builtins__": {}}, df.to_dict('series'))
        
        session_manager.set_dataframe(session_id, df)
        session_manager.add_history(session_id, {
            "step": "feature_engineering",
            "action": request.operation,
            "source_columns": request.source_columns,
            "new_column": request.new_column_name,
        })
        
        return {
            "success": True,
            "operation": request.operation,
            "new_column": request.new_column_name,
            "total_columns": len(df.columns),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(session_id: str = Depends(require_session)):
    """Get preprocessing history"""
    history = session_manager.get_history(session_id)
    return {"history": history}


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
    
    return {
        "success": True,
        "message": "Data reset to original",
        "rows": len(original_df),
        "columns": len(original_df.columns),
    }
