"""Outlier handling processor functions."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from sklearn.neighbors import LocalOutlierFactor
import logging

logger = logging.getLogger(__name__)


def remove_outliers_iqr(df: pd.DataFrame, columns: List[str], factor: float = 1.5) -> pd.DataFrame:
    """Remove outliers using IQR method."""
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_cols:
        return df
    
    mask = pd.Series([True] * len(df), index=df.index)
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
            mask &= (df[col] >= lower_bound) & (df[col] <= upper_bound)
        except Exception as e:
            logger.error(f"Error processing column {col} with IQR: {e}", exc_info=True)
    
    return df[mask].reset_index(drop=True)


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


def remove_outliers_zscore(df: pd.DataFrame, columns: List[str], threshold: float = 3.0) -> pd.DataFrame:
    """Remove outliers using Z-score method."""
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_cols:
        return df
    
    mask = pd.Series([True] * len(df), index=df.index)
    for col in numeric_cols:
        try:
            # Drop NaN values for calculation
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                continue
            
            mean = col_data.mean()
            std = col_data.std()
            
            if std > 0:
                z_scores = np.abs((df[col] - mean) / std)
                mask &= z_scores <= threshold
        except Exception as e:
            logger.error(f"Error processing column {col} with Z-score: {e}", exc_info=True)
    
    return df[mask].reset_index(drop=True)


def cap_outliers_zscore(df: pd.DataFrame, columns: List[str], threshold: float = 3.0) -> pd.DataFrame:
    """Cap outliers using Z-score method."""
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    for col in numeric_cols:
        try:
            # Drop NaN values for calculation
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                continue
            
            mean = col_data.mean()
            std = col_data.std()
            
            if std > 0:
                lower_bound = mean - threshold * std
                upper_bound = mean + threshold * std
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        except Exception as e:
            logger.error(f"Error processing column {col} with Z-score: {e}", exc_info=True)
    
    return df


def remove_outliers_lof(df: pd.DataFrame, columns: List[str], contamination: float = 0.1, n_neighbors: int = 20) -> pd.DataFrame:
    """Remove outliers using Local Outlier Factor."""
    df = df.copy()
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_cols:
        return df
    
    try:
        lof = LocalOutlierFactor(contamination=contamination, n_neighbors=n_neighbors)
        outliers = lof.fit_predict(df[numeric_cols])
        mask = outliers == 1
        
        return df[mask].reset_index(drop=True)
    except Exception as e:
        logger.error(f"Error removing outliers with LOF: {e}", exc_info=True)
        return df


def apply_outlier_method(
    df: pd.DataFrame,
    columns: List[str],
    method: str,
    action: str,
    **kwargs
) -> pd.DataFrame:
    """
    Apply outlier handling method to specified columns.
    
    Args:
        df: Input DataFrame
        columns: List of column names to process
        method: Detection method ('iqr', 'zscore', 'lof')
        action: Action to take ('remove' or 'cap')
        **kwargs: Additional parameters for the method
            - factor: For IQR method (default: 1.5)
            - threshold: For Z-score method (default: 3.0)
            - contamination: For LOF (default: 0.1)
            - n_neighbors: For LOF method (default: 20)
    
    Returns:
        Processed DataFrame
    """
    logger.info(f"🔍 Applying outlier method: {method} with action: {action} on columns: {columns}")
    
    try:
        if method == 'iqr':
            factor = kwargs.get('factor', 1.5)
            if action == 'remove':
                return remove_outliers_iqr(df, columns, factor)
            elif action == 'cap':
                return cap_outliers_iqr(df, columns, factor)
            else:
                raise ValueError(f"Unknown action: {action}. Must be 'remove' or 'cap'")
        
        elif method == 'zscore':
            threshold = kwargs.get('threshold', 3.0)
            if action == 'remove':
                return remove_outliers_zscore(df, columns, threshold)
            elif action == 'cap':
                return cap_outliers_zscore(df, columns, threshold)
            else:
                raise ValueError(f"Unknown action: {action}. Must be 'remove' or 'cap'")
        
        elif method == 'lof':
            contamination = kwargs.get('contamination', 0.1)
            n_neighbors = kwargs.get('n_neighbors', 20)
            if action == 'remove':
                return remove_outliers_lof(df, columns, contamination, n_neighbors)
            else:
                raise ValueError(f"Action 'cap' is not supported for lof method. Use 'remove'.")
        
        else:
            raise ValueError(f"Unknown method: {method}. Must be 'iqr', 'zscore', or 'lof'")
    
    except Exception as e:
        logger.error(f"❌ Error applying outlier method {method} with action {action}: {e}", exc_info=True)
        raise

