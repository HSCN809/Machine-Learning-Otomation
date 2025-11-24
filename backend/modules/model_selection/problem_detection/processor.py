"""Problem detection processor functions."""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

from .analyzer import analyze_target_variable, detect_class_imbalance

logger = logging.getLogger(__name__)


def detect_problem_type(df: pd.DataFrame, target_column: str) -> str:
    """
    Detect problem type (classification or regression) based on target variable.
    
    Args:
        df: DataFrame containing the data
        target_column: Name of the target column
        
    Returns:
        Problem type: 'classification', 'regression', 'binary_classification', 'multiclass_classification'
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in DataFrame")
    
    target_series = df[target_column].dropna()
    
    if len(target_series) == 0:
        raise ValueError(f"Target column '{target_column}' is empty or contains only missing values")
    
    # Analyze target variable
    analysis = analyze_target_variable(df, target_column)
    
    is_numeric = analysis['is_numeric']
    unique_count = analysis['unique_count']
    total_count = analysis['total_count']
    
    # Decision logic
    if is_numeric:
        # Check if numeric but likely categorical (low cardinality integers)
        if analysis.get('likely_categorical', False) and unique_count <= 20:
            # Treat as classification
            if unique_count == 2:
                problem_type = 'binary_classification'
            else:
                problem_type = 'multiclass_classification'
        else:
            # True regression (continuous numeric values)
            problem_type = 'regression'
    else:
        # Categorical - always classification
        if unique_count == 2:
            problem_type = 'binary_classification'
        else:
            problem_type = 'multiclass_classification'
    
    logger.info(f"Problem type detected: {problem_type} (target: {target_column}, unique: {unique_count}, numeric: {is_numeric})")
    return problem_type


def get_problem_type_info(df: pd.DataFrame, target_column: str) -> Dict:
    """
    Get comprehensive information about the problem type.
    
    Args:
        df: DataFrame containing the data
        target_column: Name of the target column
        
    Returns:
        Dictionary with problem type information
    """
    problem_type = detect_problem_type(df, target_column)
    analysis = analyze_target_variable(df, target_column)
    
    info = {
        'problem_type': problem_type,
        'target_column': target_column,
        'target_analysis': analysis,
        'is_classification': problem_type in ['binary_classification', 'multiclass_classification'],
        'is_regression': problem_type == 'regression',
        'is_binary': problem_type == 'binary_classification',
        'is_multiclass': problem_type == 'multiclass_classification'
    }
    
    # Add classification-specific info
    if info['is_classification']:
        imbalance_info = detect_class_imbalance(df, target_column)
        info['class_imbalance'] = imbalance_info
        info['num_classes'] = analysis['unique_count']
        
        if info['is_binary']:
            info['classes'] = sorted(df[target_column].dropna().unique().tolist())
        else:
            info['classes'] = sorted(df[target_column].dropna().unique().tolist())
            info['class_distribution'] = df[target_column].value_counts().to_dict()
    
    # Add regression-specific info
    if info['is_regression']:
        target_series = df[target_column].dropna()
        info['target_range'] = {
            'min': float(target_series.min()),
            'max': float(target_series.max()),
            'mean': float(target_series.mean()),
            'std': float(target_series.std())
        }
    
    logger.debug(f"Problem type info generated: {problem_type}")
    return info


def validate_target_variable(df: pd.DataFrame, target_column: str) -> tuple:
    """
    Validate that target variable is suitable for machine learning.
    
    Args:
        df: DataFrame containing the data
        target_column: Name of the target column
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if target_column not in df.columns:
        return False, f"Target column '{target_column}' not found in DataFrame"
    
    target_series = df[target_column]
    
    # Check for empty column
    if len(target_series) == 0:
        return False, f"Target column '{target_column}' is empty"
    
    # Check for too many missing values (>50%)
    missing_percentage = (target_series.isnull().sum() / len(target_series)) * 100
    if missing_percentage > 50:
        return False, f"Target column '{target_column}' has too many missing values ({missing_percentage:.1f}%)"
    
    # Check for constant values (no variance)
    non_null_series = target_series.dropna()
    if len(non_null_series) > 0:
        if non_null_series.nunique() <= 1:
            return False, f"Target column '{target_column}' has no variance (all values are the same)"
    
    # Check for too many unique values in categorical (might be an ID column)
    if not pd.api.types.is_numeric_dtype(target_series):
        unique_ratio = non_null_series.nunique() / len(non_null_series) if len(non_null_series) > 0 else 0
        if unique_ratio > 0.95:
            return False, f"Target column '{target_column}' appears to be an identifier (too many unique values)"
    
    return True, None

