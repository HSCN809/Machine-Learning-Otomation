"""Outlier handling processor functions."""

import pandas as pd
import numpy as np
from typing import List
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


def winsorize_outliers_iqr(
    df: pd.DataFrame,
    columns: List[str],
    factor: float = 1.5,
    tail_percent: float = 5.0,
) -> pd.DataFrame:
    """
    Winsorize outliers detected by IQR bounds.

    Values outside IQR bounds are replaced with percentile-based limits.
    `tail_percent` is applied symmetrically to both tails (e.g. 5 -> p5/p95).
    """
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    clipped_tail = min(max(float(tail_percent), 0.1), 49.9)
    lower_q = clipped_tail / 100.0
    upper_q = 1.0 - lower_q

    for col in numeric_cols:
        try:
            col_data = df[col].dropna()

            if len(col_data) == 0:
                continue

            q1 = col_data.quantile(0.25)
            q3 = col_data.quantile(0.75)
            iqr = q3 - q1

            if iqr == 0 or np.isnan(iqr):
                continue

            lower_bound = q1 - factor * iqr
            upper_bound = q3 + factor * iqr
            lower_winsor = col_data.quantile(lower_q)
            upper_winsor = col_data.quantile(upper_q)

            lower_mask = df[col] < lower_bound
            upper_mask = df[col] > upper_bound

            df.loc[lower_mask, col] = lower_winsor
            df.loc[upper_mask, col] = upper_winsor
        except Exception as e:
            logger.error(f"Error processing column {col} with IQR winsorize: {e}", exc_info=True)

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
        method: Outlier handling method ('iqr_cap', 'iqr_winsorize')
        **kwargs: Additional parameters for the method
            - factor: For IQR method (default: 1.5)
            - tail_percent: For IQR winsorize (default: 5.0)
    
    Returns:
        Processed DataFrame
    """
    logger.info(f"Applying outlier cap method: {method} on columns: {columns}")
    
    try:
        normalized_method = (method or '').strip().lower()

        if normalized_method in {'iqr', 'iqr_cap'}:
            factor = kwargs.get('factor', 1.5)
            return cap_outliers_iqr(df, columns, factor)
        if normalized_method == 'iqr_winsorize':
            factor = kwargs.get('factor', 1.5)
            tail_percent = kwargs.get('tail_percent', 5.0)
            return winsorize_outliers_iqr(df, columns, factor, tail_percent)

        else:
            raise ValueError(f"Unknown method: {method}. Must be 'iqr_cap' or 'iqr_winsorize'")
    
    except Exception as e:
        logger.error(f"Error applying outlier cap method {method}: {e}", exc_info=True)
        raise

