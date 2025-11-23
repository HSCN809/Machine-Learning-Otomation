"""Scaling processor functions."""

import pandas as pd
import numpy as np
from typing import List, Optional
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, Normalizer, PowerTransformer
import logging

logger = logging.getLogger(__name__)


def standard_scale(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Standard scale (Z-score normalization) specified numeric columns.
    
    Standard scaling transforms data to have mean=0 and std=1.
    Formula: (x - mean) / std
    Suitable for most machine learning algorithms, especially when data is normally distributed.
    """
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_cols:
        logger.warning("No numeric columns found for standard scaling")
        return df
    
    try:
        scaler = StandardScaler()
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        logger.info(f"✅ Standard scaled columns: {', '.join(numeric_cols)}")
    except Exception as e:
        logger.error(f"Error standard scaling columns: {e}", exc_info=True)
    
    return df


def minmax_scale(df: pd.DataFrame, columns: List[str], feature_range: tuple = (0, 1)) -> pd.DataFrame:
    """Min-Max scale specified numeric columns.
    
    Min-Max scaling transforms data to a specified range (default: 0-1).
    Formula: (x - min) / (max - min) * (max_range - min_range) + min_range
    Suitable for neural networks and algorithms that require bounded input.
    """
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_cols:
        logger.warning("No numeric columns found for min-max scaling")
        return df
    
    try:
        scaler = MinMaxScaler(feature_range=feature_range)
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        logger.info(f"✅ Min-Max scaled columns: {', '.join(numeric_cols)} (range: {feature_range})")
    except Exception as e:
        logger.error(f"Error min-max scaling columns: {e}", exc_info=True)
    
    return df


def robust_scale(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Robust scale specified numeric columns.
    
    Robust scaling uses median and IQR instead of mean and std.
    Formula: (x - median) / IQR
    Suitable for data with outliers, as it's less sensitive to extreme values.
    """
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_cols:
        logger.warning("No numeric columns found for robust scaling")
        return df
    
    try:
        scaler = RobustScaler()
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        logger.info(f"✅ Robust scaled columns: {', '.join(numeric_cols)}")
    except Exception as e:
        logger.error(f"Error robust scaling columns: {e}", exc_info=True)
    
    return df


def normalize(df: pd.DataFrame, columns: List[str], norm: str = 'l2') -> pd.DataFrame:
    """Normalize specified numeric columns.
    
    Normalization scales each sample (row) to have unit norm.
    norm: 'l1', 'l2', or 'max'
    - l2: Euclidean norm (default)
    - l1: Manhattan norm
    - max: Maximum norm
    Suitable for text classification, clustering, and when sample-wise scaling is needed.
    """
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_cols:
        logger.warning("No numeric columns found for normalization")
        return df
    
    try:
        normalizer = Normalizer(norm=norm)
        df[numeric_cols] = normalizer.fit_transform(df[numeric_cols])
        logger.info(f"✅ Normalized columns: {', '.join(numeric_cols)} (norm: {norm})")
    except Exception as e:
        logger.error(f"Error normalizing columns: {e}", exc_info=True)
    
    return df


def power_transform(df: pd.DataFrame, columns: List[str], method: str = 'yeo-johnson') -> pd.DataFrame:
    """Power transform specified numeric columns.
    
    Power transformation makes data more Gaussian-like.
    method: 'yeo-johnson' (default, works with positive and negative values) or 'box-cox' (only positive values)
    Suitable for data that is not normally distributed.
    """
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_cols:
        logger.warning("No numeric columns found for power transformation")
        return df
    
    try:
        # For box-cox, check if all values are positive
        if method == 'box-cox':
            for col in numeric_cols:
                if (df[col].dropna() <= 0).any():
                    logger.warning(f"Column {col} contains non-positive values. Using 'yeo-johnson' instead of 'box-cox'.")
                    method = 'yeo-johnson'
                    break
        
        transformer = PowerTransformer(method=method, standardize=True)
        df[numeric_cols] = transformer.fit_transform(df[numeric_cols])
        logger.info(f"✅ Power transformed columns: {', '.join(numeric_cols)} (method: {method})")
    except Exception as e:
        logger.error(f"Error power transforming columns: {e}", exc_info=True)
    
    return df


def apply_scaling_method(df: pd.DataFrame, columns: List[str], method: str, **kwargs) -> pd.DataFrame:
    """Apply scaling method to specified columns.
    
    Args:
        df: DataFrame to scale
        columns: List of column names to scale
        method: Scaling method name
            - 'standard_scaler': Standard scaling (Z-score)
            - 'minmax_scaler': Min-Max scaling
            - 'robust_scaler': Robust scaling
            - 'normalizer': Normalization
            - 'power_transform': Power transformation
        **kwargs: Additional parameters for specific methods
            - feature_range: For minmax_scaler (default: (0, 1))
            - norm: For normalizer (default: 'l2')
            - method: For power_transform (default: 'yeo-johnson')
    
    Returns:
        DataFrame with scaled columns
    """
    method_map = {
        'standard_scaler': standard_scale,
        'minmax_scaler': minmax_scale,
        'robust_scaler': robust_scale,
        'normalizer': normalize,
        'power_transform': power_transform
    }
    
    if method not in method_map:
        logger.error(f"Unknown scaling method: {method}")
        return df
    
    scaling_func = method_map[method]
    
    # Extract method-specific kwargs
    if method == 'minmax_scaler':
        feature_range = kwargs.get('feature_range', (0, 1))
        return scaling_func(df, columns, feature_range=feature_range)
    elif method == 'normalizer':
        norm = kwargs.get('norm', 'l2')
        return scaling_func(df, columns, norm=norm)
    elif method == 'power_transform':
        transform_method = kwargs.get('method', 'yeo-johnson')
        return scaling_func(df, columns, method=transform_method)
    else:
        return scaling_func(df, columns)

