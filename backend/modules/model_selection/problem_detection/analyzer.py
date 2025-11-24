"""Problem detection analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def analyze_target_variable(df: pd.DataFrame, target_column: str) -> Dict:
    """
    Analyze target variable to understand its characteristics.
    
    Args:
        df: DataFrame containing the data
        target_column: Name of the target column
        
    Returns:
        Dictionary with target variable analysis
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in DataFrame")
    
    target_series = df[target_column]
    
    # Basic statistics
    is_numeric = pd.api.types.is_numeric_dtype(target_series)
    unique_count = target_series.nunique()
    total_count = len(target_series)
    missing_count = target_series.isnull().sum()
    missing_percentage = (missing_count / total_count) * 100 if total_count > 0 else 0
    
    analysis = {
        'column_name': target_column,
        'is_numeric': is_numeric,
        'data_type': str(target_series.dtype),
        'unique_count': unique_count,
        'total_count': total_count,
        'missing_count': missing_count,
        'missing_percentage': missing_percentage,
        'cardinality_ratio': unique_count / total_count if total_count > 0 else 0
    }
    
    # Numeric-specific analysis
    if is_numeric:
        analysis['numeric_stats'] = {
            'mean': float(target_series.mean()) if not target_series.empty else None,
            'median': float(target_series.median()) if not target_series.empty else None,
            'std': float(target_series.std()) if not target_series.empty else None,
            'min': float(target_series.min()) if not target_series.empty else None,
            'max': float(target_series.max()) if not target_series.empty else None,
            'skewness': float(target_series.skew()) if not target_series.empty else None
        }
        
        # Check if numeric values are actually categorical (integers with low cardinality)
        if unique_count <= 20 and target_series.dtype in ['int64', 'int32', 'int16', 'int8']:
            analysis['likely_categorical'] = True
            analysis['unique_values'] = sorted(target_series.dropna().unique().tolist())
        else:
            analysis['likely_categorical'] = False
    else:
        # Categorical-specific analysis
        analysis['categorical_stats'] = {
            'value_counts': target_series.value_counts().to_dict(),
            'most_frequent': target_series.mode().iloc[0] if len(target_series.mode()) > 0 else None,
            'most_frequent_count': target_series.value_counts().iloc[0] if len(target_series.value_counts()) > 0 else 0
        }
        analysis['unique_values'] = sorted(target_series.dropna().unique().tolist())
    
    logger.debug(f"Target variable analysis completed: {target_column}")
    return analysis


def get_target_statistics(df: pd.DataFrame, target_column: str) -> Dict:
    """
    Get comprehensive statistics for target variable.
    
    Args:
        df: DataFrame containing the data
        target_column: Name of the target column
        
    Returns:
        Dictionary with target statistics
    """
    target_series = df[target_column]
    
    stats = {
        'shape': {
            'rows': len(df),
            'columns': len(df.columns)
        },
        'target_info': {
            'name': target_column,
            'dtype': str(target_series.dtype),
            'nunique': target_series.nunique(),
            'missing': target_series.isnull().sum(),
            'missing_percentage': (target_series.isnull().sum() / len(target_series)) * 100 if len(target_series) > 0 else 0
        }
    }
    
    if pd.api.types.is_numeric_dtype(target_series):
        stats['target_info']['is_numeric'] = True
        stats['target_info']['statistics'] = {
            'mean': float(target_series.mean()) if not target_series.empty else None,
            'median': float(target_series.median()) if not target_series.empty else None,
            'std': float(target_series.std()) if not target_series.empty else None,
            'min': float(target_series.min()) if not target_series.empty else None,
            'max': float(target_series.max()) if not target_series.empty else None
        }
    else:
        stats['target_info']['is_numeric'] = False
        stats['target_info']['value_distribution'] = target_series.value_counts().to_dict()
    
    return stats


def detect_class_imbalance(df: pd.DataFrame, target_column: str, threshold: float = 0.1) -> Dict:
    """
    Detect class imbalance for classification problems.
    
    Args:
        df: DataFrame containing the data
        target_column: Name of the target column
        threshold: Minimum class proportion to consider balanced (default: 0.1)
        
    Returns:
        Dictionary with imbalance detection results
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in DataFrame")
    
    target_series = df[target_column].dropna()
    value_counts = target_series.value_counts()
    total = len(target_series)
    
    class_proportions = (value_counts / total).to_dict()
    min_proportion = min(class_proportions.values()) if class_proportions else 0
    
    is_imbalanced = min_proportion < threshold
    
    result = {
        'is_imbalanced': is_imbalanced,
        'threshold': threshold,
        'min_class_proportion': min_proportion,
        'class_proportions': class_proportions,
        'class_counts': value_counts.to_dict(),
        'total_samples': total,
        'num_classes': len(value_counts)
    }
    
    if is_imbalanced:
        result['imbalance_ratio'] = max(class_proportions.values()) / min_proportions.values() if min_proportions.values() else None
        result['minority_classes'] = [cls for cls, prop in class_proportions.items() if prop < threshold]
    
    logger.debug(f"Class imbalance detection: is_imbalanced={is_imbalanced}, min_proportion={min_proportion}")
    return result

