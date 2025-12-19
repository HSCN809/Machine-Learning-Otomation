"""
EDA Router - Exploratory Data Analysis endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ..dependencies import session_manager, require_session

router = APIRouter()


@router.get("/summary")
async def get_eda_summary(session_id: str = Depends(require_session)):
    """Get EDA summary statistics"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "missing_count": int(df.isnull().sum().sum()),
        "missing_percentage": round(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 2),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
    }


@router.get("/column-types")
async def get_column_types(session_id: str = Depends(require_session)):
    """Get detailed column type information"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    columns = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        
        if np.issubdtype(df[col].dtype, np.number):
            col_type = "numeric"
        elif df[col].dtype == 'object' or df[col].dtype.name == 'category':
            col_type = "categorical"
        elif np.issubdtype(df[col].dtype, np.datetime64):
            col_type = "datetime"
        else:
            col_type = "text"
        
        columns.append({
            "name": col,
            "dtype": dtype,
            "type": col_type,
            "null_count": int(df[col].isnull().sum()),
            "null_percentage": round(df[col].isnull().sum() / len(df) * 100, 2),
            "unique_count": int(df[col].nunique()),
        })
    
    return {"columns": columns}


@router.get("/numeric-stats")
async def get_numeric_stats(session_id: str = Depends(require_session)):
    """Get statistics for numeric columns"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    numeric_df = df.select_dtypes(include=['number'])
    if numeric_df.empty:
        return {"stats": []}
    
    stats = []
    for col in numeric_df.columns:
        col_data = numeric_df[col].dropna()
        if len(col_data) == 0:
            continue
            
        stats.append({
            "column": col,
            "count": int(col_data.count()),
            "mean": round(float(col_data.mean()), 4),
            "std": round(float(col_data.std()), 4),
            "min": round(float(col_data.min()), 4),
            "q25": round(float(col_data.quantile(0.25)), 4),
            "median": round(float(col_data.median()), 4),
            "q75": round(float(col_data.quantile(0.75)), 4),
            "max": round(float(col_data.max()), 4),
        })
    
    return {"stats": stats}


@router.get("/categorical-stats")
async def get_categorical_stats(session_id: str = Depends(require_session)):
    """Get statistics for categorical columns"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    categorical_df = df.select_dtypes(include=['object', 'category'])
    if categorical_df.empty:
        return {"stats": []}
    
    stats = []
    for col in categorical_df.columns:
        col_data = categorical_df[col].dropna()
        if len(col_data) == 0:
            continue
        
        value_counts = col_data.value_counts()
        stats.append({
            "column": col,
            "count": int(len(col_data)),
            "unique": int(col_data.nunique()),
            "top": str(value_counts.index[0]) if len(value_counts) > 0 else None,
            "frequency": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
        })
    
    return {"stats": stats}


@router.get("/correlation")
async def get_correlation(session_id: str = Depends(require_session)):
    """Get correlation matrix for numeric columns"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    numeric_df = df.select_dtypes(include=['number'])
    if numeric_df.shape[1] < 2:
        return {"correlation": [], "columns": []}
    
    corr_matrix = numeric_df.corr()
    
    # Convert to list of dicts for frontend
    correlation_data = []
    for i, row in enumerate(corr_matrix.index):
        for j, col in enumerate(corr_matrix.columns):
            correlation_data.append({
                "x": row,
                "y": col,
                "value": round(float(corr_matrix.iloc[i, j]), 4),
            })
    
    return {
        "correlation": correlation_data,
        "columns": corr_matrix.columns.tolist(),
    }


@router.get("/histogram/{column}")
async def get_histogram(
    column: str,
    bins: int = 20,
    session_id: str = Depends(require_session)
):
    """Get histogram data for a numeric column"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    if column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Column '{column}' not found")
    
    col_data = df[column].dropna()
    
    if not np.issubdtype(col_data.dtype, np.number):
        raise HTTPException(status_code=400, detail="Column must be numeric")
    
    counts, bin_edges = np.histogram(col_data, bins=bins)
    
    histogram_data = []
    for i in range(len(counts)):
        histogram_data.append({
            "bin": f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}",
            "count": int(counts[i]),
            "percentage": round(counts[i] / len(col_data) * 100, 2),
        })
    
    return {"data": histogram_data, "column": column}


@router.get("/boxplot/{column}")
async def get_boxplot(
    column: str,
    session_id: str = Depends(require_session)
):
    """Get boxplot data for a numeric column"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    if column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Column '{column}' not found")
    
    col_data = df[column].dropna()
    
    if not np.issubdtype(col_data.dtype, np.number):
        raise HTTPException(status_code=400, detail="Column must be numeric")
    
    q1 = float(col_data.quantile(0.25))
    q3 = float(col_data.quantile(0.75))
    iqr = q3 - q1
    
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    
    outliers = col_data[(col_data < lower_fence) | (col_data > upper_fence)].tolist()
    
    return {
        "column": column,
        "min": float(col_data.min()),
        "q1": q1,
        "median": float(col_data.median()),
        "q3": q3,
        "max": float(col_data.max()),
        "outliers": outliers[:50],  # Limit outliers
    }


@router.get("/category-distribution/{column}")
async def get_category_distribution(
    column: str,
    top_n: int = 10,
    session_id: str = Depends(require_session)
):
    """Get distribution for a categorical column"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    if column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Column '{column}' not found")
    
    value_counts = df[column].value_counts().head(top_n)
    total = len(df[column].dropna())
    
    distribution = []
    for name, count in value_counts.items():
        distribution.append({
            "name": str(name),
            "value": int(count),
            "percentage": round(count / total * 100, 2),
        })
    
    return {"data": distribution, "column": column}
