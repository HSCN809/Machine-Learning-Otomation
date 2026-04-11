"""Outlier handling processor functions."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def cap_outliers_iqr(df: pd.DataFrame, columns: List[str], factor: float = 1.5) -> pd.DataFrame:
    """Cap outliers using IQR method."""
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    for col in numeric_cols:
        try:
            # Drop NaN values for calculation
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                continue
            
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            
            if IQR == 0 or np.isnan(IQR):
                continue
            
            lower_bound = Q1 - factor * IQR
            upper_bound = Q3 + factor * IQR
            df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        except Exception as e:
            logger.error(f"Error processing column {col} with IQR: {e}", exc_info=True)
    
    return df


def cap_outliers_zscore(
    df: pd.DataFrame,
    columns: List[str],
    threshold: float = 3.0,
    max_iterations: int = 10,
) -> pd.DataFrame:
    """Cap outliers using Z-score method.

    Notes:
        A single-pass z-score cap can leave the outlier ratio nearly unchanged because
        mean/std shift after clipping. We apply clipping iteratively until stable.
    """
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    for col in numeric_cols:
        try:
            for _ in range(max_iterations):
                # Drop NaN values for calculation
                col_data = df[col].dropna()
                if len(col_data) == 0:
                    break

                mean = col_data.mean()
                std = col_data.std()
                if std <= 0 or np.isnan(std):
                    break

                z_scores = np.abs((df[col] - mean) / std)
                outlier_mask = z_scores > threshold

                if not outlier_mask.fillna(False).any():
                    break

                lower_bound = mean - threshold * std
                upper_bound = mean + threshold * std
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        except Exception as e:
            logger.error(f"Error processing column {col} with Z-score: {e}", exc_info=True)
    
    return df


def apply_outlier_method(
    df: pd.DataFrame,
    columns: List[str],
    method: str,
    **kwargs
) -> pd.DataFrame:
    """
    Apply outlier handling method to specified columns.
    
    Args:
        df: Input DataFrame
        columns: List of column names to process
        method: Detection method ('iqr', 'zscore')
        **kwargs: Additional parameters for the method
            - factor: For IQR method (default: 1.5)
            - threshold: For Z-score method (default: 3.0)
            - max_iterations: For Z-score cap stabilization (default: 10)
    
    Returns:
        Processed DataFrame
    """
    logger.info(f"Applying outlier cap method: {method} on columns: {columns}")
    
    try:
        if method == 'iqr':
            factor = kwargs.get('factor', 1.5)
            return cap_outliers_iqr(df, columns, factor)
        
        elif method == 'zscore':
            threshold = kwargs.get('threshold', 3.0)
            max_iterations = kwargs.get('max_iterations', 10)
            return cap_outliers_zscore(df, columns, threshold, max_iterations)
        
        else:
            raise ValueError(f"Unknown method: {method}. Must be 'iqr' or 'zscore'")
    
    except Exception as e:
        logger.error(f"Error applying outlier cap method {method}: {e}", exc_info=True)
        raise

