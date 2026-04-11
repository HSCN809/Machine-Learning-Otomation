"""Outlier analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def get_data_statistics(df: pd.DataFrame) -> Dict:
    """Get comprehensive statistics for a DataFrame."""
    stats = {
        'shape': {
            'rows': len(df),
            'columns': len(df.columns)
        },
        'data_types': {
            'numeric': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical': df.select_dtypes(include=['object', 'category']).columns.tolist(),
            'datetime': df.select_dtypes(include=['datetime']).columns.tolist()
        },
        'numeric_statistics': {}
    }
    
    # Numeric statistics
    numeric_cols = stats['data_types']['numeric']
    if numeric_cols:
        numeric_df = df[numeric_cols]
        stats['numeric_statistics'] = {
            'mean': numeric_df.mean().to_dict(),
            'median': numeric_df.median().to_dict(),
            'std': numeric_df.std().to_dict(),
            'min': numeric_df.min().to_dict(),
            'max': numeric_df.max().to_dict(),
            'skewness': numeric_df.skew().to_dict() if len(numeric_df) > 0 else {}
        }
    
    return stats


def compare_data_statistics(before_df: pd.DataFrame, after_df: pd.DataFrame) -> Dict:
    """Compare statistics between before and after preprocessing."""
    before_stats = get_data_statistics(before_df)
    after_stats = get_data_statistics(after_df)
    
    comparison = {
        'shape_change': {
            'rows_before': before_stats['shape']['rows'],
            'rows_after': after_stats['shape']['rows'],
            'rows_diff': after_stats['shape']['rows'] - before_stats['shape']['rows'],
            'columns_before': before_stats['shape']['columns'],
            'columns_after': after_stats['shape']['columns'],
            'columns_diff': after_stats['shape']['columns'] - before_stats['shape']['columns']
        },
        'data_types_change': {
            'numeric_before': len(before_stats['data_types']['numeric']),
            'numeric_after': len(after_stats['data_types']['numeric']),
            'categorical_before': len(before_stats['data_types']['categorical']),
            'categorical_after': len(after_stats['data_types']['categorical'])
        }
    }
    
    return comparison


def analyze_outliers(df: pd.DataFrame, columns: Optional[List[str]] = None, method: str = 'iqr', **kwargs) -> Dict:
    """Analyze outliers in the dataset using specified method.
    
    Args:
        df: Input DataFrame
        columns: List of column names to analyze (None for all numeric columns)
        method: Detection method ('iqr')
        **kwargs: Additional parameters for the method
            - factor: For IQR method (default: 1.5)
    
    Returns:
        Dictionary with outlier information
    """
    if df is None or df.empty:
        return {
            'method': method,
            'outliers_by_column': {},
            'total_outliers': 0,
            'total_outlier_percentage': 0.0,
            'outlier_rows': set()
        }
    
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to only columns that exist in dataframe
    columns = [col for col in columns if col in df.columns]
    
    if not columns:
        return {
            'method': method,
            'outliers_by_column': {},
            'total_outliers': 0,
            'total_outlier_percentage': 0.0,
            'outlier_rows': set()
        }
    
    if method == 'iqr':
        return _analyze_outliers_iqr(df, columns, kwargs.get('factor', 1.5))
    else:
        raise ValueError(f"Unknown method: {method}. Must be 'iqr'")


def _analyze_outliers_iqr(df: pd.DataFrame, columns: List[str], factor: float = 1.5) -> Dict:
    """Analyze outliers using IQR method."""
    outlier_info = {
        'method': 'IQR',
        'factor': factor,
        'outliers_by_column': {},
        'total_outliers': 0,
        'outlier_rows': set()
    }
    
    total_rows = len(df)
    
    for col in columns:
        try:
            if not pd.api.types.is_numeric_dtype(df[col]):
                outlier_info['outliers_by_column'][col] = {
                    'count': 0,
                    'percentage': 0.0,
                    'lower_bound': None,
                    'upper_bound': None,
                    'outlier_indices': []
                }
                continue
            
            # Drop NaN values for calculation
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                outlier_info['outliers_by_column'][col] = {
                    'count': 0,
                    'percentage': 0.0,
                    'lower_bound': None,
                    'upper_bound': None,
                    'outlier_indices': []
                }
                continue
            
            # Calculate quartiles
            Q1 = float(col_data.quantile(0.25))
            Q3 = float(col_data.quantile(0.75))
            IQR = Q3 - Q1
            
            # If IQR is 0, all values are the same, no outliers
            if IQR == 0 or np.isnan(IQR):
                outlier_info['outliers_by_column'][col] = {
                    'count': 0,
                    'percentage': 0.0,
                    'lower_bound': float(Q1) if not np.isnan(Q1) else None,
                    'upper_bound': float(Q3) if not np.isnan(Q3) else None,
                    'outlier_indices': []
                }
                continue
            
            # Calculate bounds
            lower_bound = float(Q1 - factor * IQR)
            upper_bound = float(Q3 + factor * IQR)
            
            # Find outliers in the full dataframe
            outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outliers = df[outlier_mask]
            outlier_count = len(outliers)
            outlier_indices = outliers.index.tolist()
            
            outlier_info['outliers_by_column'][col] = {
                'count': outlier_count,
                'percentage': (outlier_count / total_rows * 100) if total_rows > 0 else 0.0,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'outlier_indices': outlier_indices
            }
            outlier_info['outlier_rows'].update(outlier_indices)
            
        except Exception as e:
            outlier_info['outliers_by_column'][col] = {
                'count': 0,
                'percentage': 0.0,
                'lower_bound': None,
                'upper_bound': None,
                'outlier_indices': []
            }
    
    # Calculate total outlier cells (sum of all outlier counts across columns) for total percentage
    # Use ALL numeric columns in dataframe, not just the ones in columns parameter
    all_numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    total_cells = total_rows * len(all_numeric_cols) if all_numeric_cols else total_rows
    total_outlier_cells = sum(info['count'] for info in outlier_info['outliers_by_column'].values())
    outlier_info['total_outliers'] = total_outlier_cells
    outlier_info['total_outlier_percentage'] = (total_outlier_cells / total_cells * 100) if total_cells > 0 else 0.0
    
    return outlier_info


def analyze_outliers_iqr(df: pd.DataFrame, columns: Optional[List[str]] = None, factor: float = 1.5) -> Dict:
    """Analyze outliers using IQR method."""
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    return _analyze_outliers_iqr(df, columns, factor)


def get_all_outlier_info(df: pd.DataFrame, columns: Optional[List[str]] = None, methods: Optional[List[str]] = None) -> Dict:
    """
    Get comprehensive outlier information.
    
    Args:
        df: Input DataFrame
        columns: List of columns to analyze (None for all numeric columns)
        methods: List of methods to use ('iqr')
                 If None, uses IQR
    
    Returns:
        Dictionary with outlier information for each method
    """
    if methods is None:
        methods = ['iqr']
    
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    results = {}
    
    for method in methods:
        try:
            if method == 'iqr':
                results['iqr'] = analyze_outliers_iqr(df, columns)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error analyzing outliers with {method}: {e}", exc_info=True)
            results[method] = {
                'error': str(e),
                'total_outliers': 0,
                'total_outlier_percentage': 0
            }
    
    # Get columns with outliers (union of all methods)
    columns_with_outliers = set()
    for method_result in results.values():
        if isinstance(method_result, dict) and 'outliers_by_column' in method_result:
            columns_with_outliers.update(method_result['outliers_by_column'].keys())
    
    results['columns_with_outliers'] = list(columns_with_outliers)
    results['all_methods'] = list(results.keys())
    
    return results
