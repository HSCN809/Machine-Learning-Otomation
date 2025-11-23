"""Outlier analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


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
        method: Detection method ('iqr', 'zscore', 'isolation_forest', 'lof')
        **kwargs: Additional parameters for the method
            - factor: For IQR method (default: 1.5)
            - threshold: For Z-score method (default: 3.0)
            - contamination: For Isolation Forest and LOF (default: 0.1)
            - n_neighbors: For LOF method (default: 20)
    
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
    elif method == 'zscore':
        return _analyze_outliers_zscore(df, columns, kwargs.get('threshold', 3.0))
    elif method == 'isolation_forest':
        return _analyze_outliers_isolation_forest(df, columns, kwargs.get('contamination', 0.1))
    elif method == 'lof':
        return _analyze_outliers_lof(df, columns, kwargs.get('contamination', 0.1), kwargs.get('n_neighbors', 20))
    else:
        raise ValueError(f"Unknown method: {method}. Must be 'iqr', 'zscore', 'isolation_forest', or 'lof'")


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


def _analyze_outliers_zscore(df: pd.DataFrame, columns: List[str], threshold: float = 3.0) -> Dict:
    """Analyze outliers using Z-score method."""
    outlier_info = {
        'method': 'Z-score',
        'threshold': threshold,
        'outliers_by_column': {},
        'total_outliers': 0,
        'outlier_rows': set()
    }
    
    total_rows = len(df)
    # Calculate total cells: rows × numeric columns
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    total_cells = total_rows * len(numeric_cols) if numeric_cols else total_rows
    
    for col in columns:
        try:
            if not pd.api.types.is_numeric_dtype(df[col]):
                outlier_info['outliers_by_column'][col] = {
                    'count': 0,
                    'percentage': 0.0,
                    'threshold': threshold,
                    'outlier_indices': []
                }
                continue
            
            # Drop NaN values for calculation
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                outlier_info['outliers_by_column'][col] = {
                    'count': 0,
                    'percentage': 0.0,
                    'threshold': threshold,
                    'outlier_indices': []
                }
                continue
            
            mean = col_data.mean()
            std = col_data.std()
            
            if std > 0:
                z_scores = np.abs((df[col] - mean) / std)
                outliers = df[z_scores > threshold]
                outlier_count = len(outliers)
                outlier_indices = outliers.index.tolist()
                
                outlier_info['outliers_by_column'][col] = {
                    'count': outlier_count,
                    'percentage': (outlier_count / total_rows * 100) if total_rows > 0 else 0.0,
                    'threshold': threshold,
                    'outlier_indices': outlier_indices
                }
                outlier_info['outlier_rows'].update(outlier_indices)
            else:
                outlier_info['outliers_by_column'][col] = {
                    'count': 0,
                    'percentage': 0.0,
                    'threshold': threshold,
                    'outlier_indices': []
                }
        except Exception as e:
            outlier_info['outliers_by_column'][col] = {
                'count': 0,
                'percentage': 0.0,
                'threshold': threshold,
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


def _analyze_outliers_isolation_forest(df: pd.DataFrame, columns: List[str], contamination: float = 0.1) -> Dict:
    """Analyze outliers using Isolation Forest method."""
    from sklearn.ensemble import IsolationForest
    
    outlier_info = {
        'method': 'Isolation Forest',
        'contamination': contamination,
        'outliers_by_column': {},
        'total_outliers': 0,
        'outlier_rows': set()
    }
    
    total_rows = len(df)
    
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_cols:
        outlier_info['total_outlier_percentage'] = 0.0
        return outlier_info
    
    try:
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        outliers = iso_forest.fit_predict(df[numeric_cols])
        outlier_indices = df[outliers == -1].index.tolist()
        
        outlier_info['outlier_rows'] = set(outlier_indices)
        
        # Calculate per-column statistics (percentage based on rows, not cells)
        for col in numeric_cols:
            col_outliers = df.loc[outlier_indices, col] if outlier_indices else pd.Series()
            outlier_count = len(col_outliers)
            outlier_info['outliers_by_column'][col] = {
                'count': outlier_count,
                'percentage': (outlier_count / total_rows * 100) if total_rows > 0 else 0.0,
                'outlier_indices': outlier_indices
            }
        
        # Calculate total outlier cells (sum of all outlier counts across columns) for total percentage
        # Use ALL numeric columns in dataframe, not just the ones in columns parameter
        all_numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        total_cells = total_rows * len(all_numeric_cols) if all_numeric_cols else total_rows
        total_outlier_cells = sum(info['count'] for info in outlier_info['outliers_by_column'].values())
        outlier_info['total_outliers'] = total_outlier_cells
        outlier_info['total_outlier_percentage'] = (total_outlier_cells / total_cells * 100) if total_cells > 0 else 0.0
    except Exception as e:
        outlier_info['total_outlier_percentage'] = 0.0
    
    return outlier_info


def _analyze_outliers_lof(df: pd.DataFrame, columns: List[str], contamination: float = 0.1, n_neighbors: int = 20) -> Dict:
    """Analyze outliers using Local Outlier Factor method."""
    from sklearn.neighbors import LocalOutlierFactor
    
    outlier_info = {
        'method': 'LOF',
        'contamination': contamination,
        'n_neighbors': n_neighbors,
        'outliers_by_column': {},
        'total_outliers': 0,
        'outlier_rows': set()
    }
    
    total_rows = len(df)
    
    numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_cols:
        outlier_info['total_outlier_percentage'] = 0.0
        return outlier_info
    
    try:
        lof = LocalOutlierFactor(contamination=contamination, n_neighbors=n_neighbors)
        outliers = lof.fit_predict(df[numeric_cols])
        outlier_indices = df[outliers == -1].index.tolist()
        
        outlier_info['outlier_rows'] = set(outlier_indices)
        
        # Calculate per-column statistics (percentage based on rows, not cells)
        for col in numeric_cols:
            col_outliers = df.loc[outlier_indices, col] if outlier_indices else pd.Series()
            outlier_count = len(col_outliers)
            outlier_info['outliers_by_column'][col] = {
                'count': outlier_count,
                'percentage': (outlier_count / total_rows * 100) if total_rows > 0 else 0.0,
                'outlier_indices': outlier_indices
            }
        
        # Calculate total outlier cells (sum of all outlier counts across columns) for total percentage
        # Use ALL numeric columns in dataframe, not just the ones in columns parameter
        all_numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        total_cells = total_rows * len(all_numeric_cols) if all_numeric_cols else total_rows
        total_outlier_cells = sum(info['count'] for info in outlier_info['outliers_by_column'].values())
        outlier_info['total_outliers'] = total_outlier_cells
        outlier_info['total_outlier_percentage'] = (total_outlier_cells / total_cells * 100) if total_cells > 0 else 0.0
    except Exception as e:
        outlier_info['total_outlier_percentage'] = 0.0
    
    return outlier_info


def analyze_outliers_iqr(df: pd.DataFrame, columns: Optional[List[str]] = None, factor: float = 1.5) -> Dict:
    """Analyze outliers using IQR method."""
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    return _analyze_outliers_iqr(df, columns, factor)


def analyze_outliers_zscore(df: pd.DataFrame, columns: Optional[List[str]] = None, threshold: float = 3.0) -> Dict:
    """Analyze outliers using Z-score method."""
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    return _analyze_outliers_zscore(df, columns, threshold)


def analyze_outliers_isolation_forest(df: pd.DataFrame, columns: Optional[List[str]] = None, contamination: float = 0.1) -> Dict:
    """Analyze outliers using Isolation Forest method."""
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    return _analyze_outliers_isolation_forest(df, columns, contamination)


def analyze_outliers_lof(df: pd.DataFrame, columns: Optional[List[str]] = None, contamination: float = 0.1, n_neighbors: int = 20) -> Dict:
    """Analyze outliers using Local Outlier Factor method."""
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    return _analyze_outliers_lof(df, columns, contamination, n_neighbors)


def get_all_outlier_info(df: pd.DataFrame, columns: Optional[List[str]] = None, methods: Optional[List[str]] = None) -> Dict:
    """
    Get comprehensive outlier information using multiple methods.
    
    Args:
        df: Input DataFrame
        columns: List of columns to analyze (None for all numeric columns)
        methods: List of methods to use ('iqr', 'zscore', 'isolation_forest', 'lof')
                 If None, uses all methods
    
    Returns:
        Dictionary with outlier information for each method
    """
    if methods is None:
        methods = ['iqr', 'zscore', 'isolation_forest', 'lof']
    
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    results = {}
    
    for method in methods:
        try:
            if method == 'iqr':
                results['iqr'] = analyze_outliers_iqr(df, columns)
            elif method == 'zscore':
                results['zscore'] = analyze_outliers_zscore(df, columns)
            elif method == 'isolation_forest':
                results['isolation_forest'] = analyze_outliers_isolation_forest(df, columns)
            elif method == 'lof':
                results['lof'] = analyze_outliers_lof(df, columns)
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

