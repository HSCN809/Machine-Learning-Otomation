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
        method: Detection method ('iqr')
        **kwargs: Additional parameters for the method
            - factor: For IQR method (default: 1.5)
    
    Returns:
        Processed DataFrame
    """
    logger.info(f"Applying outlier cap method: {method} on columns: {columns}")
    
    try:
        if method == 'iqr':
            factor = kwargs.get('factor', 1.5)
            return cap_outliers_iqr(df, columns, factor)

        else:
            raise ValueError(f"Unknown method: {method}. Must be 'iqr'")
    
    except Exception as e:
        logger.error(f"Error applying outlier cap method {method}: {e}", exc_info=True)
        raise

