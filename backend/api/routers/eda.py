"""
EDA Router - Exploratory Data Analysis endpoints.
"""

from typing import Any, cast
import os
import sys

from fastapi import APIRouter, Depends, HTTPException, Query
import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype, is_object_dtype

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ..dependencies import session_manager, require_session

router = APIRouter()


def _safe_percentage(numerator: float, denominator: float) -> float:
    """Return percentage while avoiding division by zero."""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


def _get_dataframe(session_id: str) -> pd.DataFrame:
    """Return session dataframe or raise 400."""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    return df


def _get_series(df: pd.DataFrame, column: str) -> pd.Series:
    """Return a dataframe column as Series for type checkers and runtime safety."""
    if column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Column '{column}' not found")
    return cast(pd.Series, df[column])


def _is_numeric_series(series: pd.Series) -> bool:
    """Check whether a pandas Series is numeric."""
    return bool(is_numeric_dtype(series.dtype))


def _is_categorical_series(series: pd.Series) -> bool:
    """Check whether a pandas Series is categorical-like."""
    return bool(is_object_dtype(series.dtype) or isinstance(series.dtype, pd.CategoricalDtype))


def _is_datetime_series(series: pd.Series) -> bool:
    """Check whether a pandas Series is datetime-like."""
    return bool(is_datetime64_any_dtype(series.dtype))


@router.get("/summary")
async def get_eda_summary(session_id: str = Depends(require_session)):
    """Get EDA summary statistics"""
    df = _get_dataframe(session_id)
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    total_cells = len(df) * len(df.columns)

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "missing_count": int(df.isnull().sum().sum()),
        "missing_percentage": _safe_percentage(float(df.isnull().sum().sum()), float(total_cells)),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
    }


@router.get("/column-types")
async def get_column_types(session_id: str = Depends(require_session)):
    """Get detailed column type information"""
    df = _get_dataframe(session_id)
    
    columns: list[dict[str, Any]] = []
    for col in df.columns:
        series = _get_series(df, col)
        dtype = str(series.dtype)
        
        if _is_numeric_series(series):
            col_type = "numeric"
        elif _is_categorical_series(series):
            col_type = "categorical"
        elif _is_datetime_series(series):
            col_type = "datetime"
        else:
            col_type = "text"
        
        columns.append({
            "name": col,
            "dtype": dtype,
            "type": col_type,
            "null_count": int(series.isnull().sum()),
            "null_percentage": _safe_percentage(float(series.isnull().sum()), float(len(df))),
            "unique_count": int(series.nunique()),
        })
    
    return {"columns": columns}


@router.get("/numeric-stats")
async def get_numeric_stats(session_id: str = Depends(require_session)):
    """Get statistics for numeric columns"""
    df = _get_dataframe(session_id)
    
    numeric_df = df.select_dtypes(include=['number'])
    if numeric_df.empty:
        return {"stats": []}
    
    stats: list[dict[str, Any]] = []
    for col in numeric_df.columns:
        series = _get_series(df, col)
        col_data = cast(pd.Series, numeric_df[col].dropna())
        null_count = series.isnull().sum()
        null_percentage = _safe_percentage(float(null_count), float(len(df)))
        unique_count = int(series.nunique())
        
        if len(col_data) == 0:
            continue
        
        variance = float(col_data.var()) if len(col_data) > 1 else 0.0
        std = float(col_data.std()) if len(col_data) > 1 else 0.0
            
        stats.append({
            "column": col,
            "count": int(col_data.count()),
            "unique_count": unique_count,
            "mean": round(float(col_data.mean()), 4),
            "std": round(std, 4),
            "variance": round(variance, 6),
            "min": round(float(col_data.min()), 4),
            "q25": round(float(col_data.quantile(0.25)), 4),
            "median": round(float(col_data.median()), 4),
            "q75": round(float(col_data.quantile(0.75)), 4),
            "max": round(float(col_data.max()), 4),
            "null_count": int(null_count),
            "null_percentage": round(null_percentage, 2),
        })
    
    return {"stats": stats}


@router.get("/categorical-stats")
async def get_categorical_stats(session_id: str = Depends(require_session)):
    """Get statistics for categorical columns"""
    df = _get_dataframe(session_id)
    
    categorical_df = df.select_dtypes(include=['object', 'category'])
    if categorical_df.empty:
        return {"stats": []}
    
    stats: list[dict[str, Any]] = []
    for col in categorical_df.columns:
        series = _get_series(df, col)
        col_data = cast(pd.Series, categorical_df[col].dropna())
        null_count = series.isnull().sum()
        null_percentage = _safe_percentage(float(null_count), float(len(df)))
        unique_count = int(series.nunique())
        
        if len(col_data) == 0:
            continue
        
        value_counts = cast(pd.Series, col_data.value_counts())
        stats.append({
            "column": col,
            "count": int(len(col_data)),
            "unique": unique_count,
            "top": str(value_counts.index[0]) if len(value_counts) > 0 else None,
            "frequency": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
            "null_count": int(null_count),
            "null_percentage": round(null_percentage, 2),
        })
    
    return {"stats": stats}


@router.get("/correlation")
async def get_correlation(session_id: str = Depends(require_session)):
    """Get correlation matrix for numeric columns"""
    df = _get_dataframe(session_id)
    
    numeric_df = df.select_dtypes(include=['number'])
    if numeric_df.shape[1] < 2:
        return {"correlation": [], "columns": []}
    
    corr_matrix = numeric_df.corr()
    
    # Convert to list of dicts for frontend
    correlation_data: list[dict[str, Any]] = []
    for i, row in enumerate(corr_matrix.index):
        for j, col in enumerate(corr_matrix.columns):
            corr_value = corr_matrix.iloc[i, j]
            correlation_data.append({
                "x": row,
                "y": col,
                "value": round(float(corr_value), 4) if pd.notna(corr_value) else 0.0,
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
    df = _get_dataframe(session_id)
    series = _get_series(df, column)
    col_data = cast(pd.Series, series.dropna())
    
    if not _is_numeric_series(series):
        raise HTTPException(status_code=400, detail="Column must be numeric")
    if col_data.empty:
        return {"data": [], "column": column}
    
    counts, bin_edges = np.histogram(col_data, bins=bins)
    
    histogram_data: list[dict[str, Any]] = []
    for i in range(len(counts)):
        histogram_data.append({
            "bin": f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}",
            "count": int(counts[i]),
            "percentage": _safe_percentage(float(counts[i]), float(len(col_data))),
        })
    
    return {"data": histogram_data, "column": column}


@router.get("/boxplot/{column}")
async def get_boxplot(
    column: str,
    session_id: str = Depends(require_session)
):
    """Get boxplot data for a numeric column"""
    df = _get_dataframe(session_id)
    series = _get_series(df, column)
    col_data = cast(pd.Series, series.dropna())
    
    if not _is_numeric_series(series):
        raise HTTPException(status_code=400, detail="Column must be numeric")
    if col_data.empty:
        raise HTTPException(status_code=400, detail="Column has no non-null numeric values")
    
    q1 = float(col_data.quantile(0.25))
    q3 = float(col_data.quantile(0.75))
    iqr = q3 - q1
    
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    
    outliers = [float(value) for value in col_data[(col_data < lower_fence) | (col_data > upper_fence)].tolist()]
    
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
    df = _get_dataframe(session_id)
    series = _get_series(df, column)
    
    value_counts = cast(pd.Series, series.value_counts().head(top_n))
    total = len(series.dropna())
    if total == 0:
        return {"data": [], "column": column}
    
    distribution: list[dict[str, Any]] = []
    for name, count in value_counts.items():
        distribution.append({
            "name": str(name),
            "value": int(count),
            "percentage": round(count / total * 100, 2),
        })
    
    return {"data": distribution, "column": column}


@router.get("/scatter")
async def get_scatter_data(
    x_column: str = Query(..., description="X axis column name"),
    y_column: str = Query(..., description="Y axis column name"),
    sample_size: int = Query(500, description="Max number of points to return"),
    session_id: str = Depends(require_session)
):
    """Get scatter plot data for two numeric columns"""
    df = _get_dataframe(session_id)
    x_series = _get_series(df, x_column)
    y_series = _get_series(df, y_column)

    if not _is_numeric_series(x_series):
        raise HTTPException(status_code=400, detail=f"Column '{x_column}' must be numeric")
    if not _is_numeric_series(y_series):
        raise HTTPException(status_code=400, detail=f"Column '{y_column}' must be numeric")

    # Build a normalized scatter dataframe so duplicate column names do not break
    scatter_df = pd.DataFrame({
        "x": x_series,
        "y": y_series,
    }).dropna()
    if scatter_df.empty:
        return {
            "data": [],
            "x_column": x_column,
            "y_column": y_column,
            "total_points": 0,
        }
    
    # Sample if too many points
    if len(scatter_df) > sample_size:
        scatter_df = scatter_df.sample(n=sample_size, random_state=42)
    
    # Convert to list of dicts
    data: list[dict[str, float]] = []
    for _, row in scatter_df.iterrows():
        data.append({
            "x": round(float(row["x"]), 4),
            "y": round(float(row["y"]), 4),
        })
    
    return {
        "data": data,
        "x_column": x_column,
        "y_column": y_column,
        "total_points": len(data),
    }

