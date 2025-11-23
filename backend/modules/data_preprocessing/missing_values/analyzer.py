"""Missing values analysis functions."""

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
        'missing_values': {
            'total_missing': df.isnull().sum().sum(),
            'missing_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100 if len(df) > 0 else 0,
            'columns_with_missing': df.columns[df.isnull().any()].tolist(),
            'missing_by_column': df.isnull().sum().to_dict()
        },
        'data_types': {
            'numeric': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical': df.select_dtypes(include=['object', 'category']).columns.tolist(),
            'datetime': df.select_dtypes(include=['datetime']).columns.tolist()
        },
        'numeric_statistics': {},
        'categorical_statistics': {}
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
    
    # Categorical statistics
    categorical_cols = stats['data_types']['categorical']
    if categorical_cols:
        stats['categorical_statistics'] = {
            col: {
                'unique_count': df[col].nunique(),
                'most_frequent': df[col].mode().iloc[0] if len(df[col].mode()) > 0 else None,
                'most_frequent_count': df[col].value_counts().iloc[0] if len(df[col].value_counts()) > 0 else 0
            }
            for col in categorical_cols
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
        'missing_values_change': {
            'before_total': before_stats['missing_values']['total_missing'],
            'after_total': after_stats['missing_values']['total_missing'],
            'total_diff': after_stats['missing_values']['total_missing'] - before_stats['missing_values']['total_missing'],
            'before_percentage': before_stats['missing_values']['missing_percentage'],
            'after_percentage': after_stats['missing_values']['missing_percentage'],
            'percentage_diff': after_stats['missing_values']['missing_percentage'] - before_stats['missing_values']['missing_percentage']
        },
        'data_types_change': {
            'numeric_before': len(before_stats['data_types']['numeric']),
            'numeric_after': len(after_stats['data_types']['numeric']),
            'categorical_before': len(before_stats['data_types']['categorical']),
            'categorical_after': len(after_stats['data_types']['categorical'])
        }
    }
    
    return comparison


def analyze_missing_values(df: pd.DataFrame) -> Dict:
    """Analyze missing values in the dataset."""
    missing_info = {
        'total_missing': df.isnull().sum().sum(),
        'missing_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100 if len(df) > 0 else 0,
        'columns_with_missing': df.columns[df.isnull().any()].tolist(),
        'missing_by_column': df.isnull().sum().to_dict(),
        'missing_percentage_by_column': {}
    }
    
    for col, count in missing_info['missing_by_column'].items():
        if count > 0:
            missing_info['missing_percentage_by_column'][col] = (count / len(df)) * 100
    
    return missing_info

