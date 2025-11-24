"""Model training analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def analyze_training_data(X: pd.DataFrame, y: pd.Series) -> Dict:
    """
    Analyze training data before model training.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        
    Returns:
        Dictionary with training data analysis
    """
    analysis = {
        'n_samples': len(X),
        'n_features': len(X.columns),
        'target_distribution': y.value_counts().to_dict() if hasattr(y, 'value_counts') else None,
        'missing_values': {
            'X_missing': int(X.isnull().sum().sum()),
            'y_missing': int(y.isnull().sum()) if hasattr(y, 'isnull') else 0
        },
        'feature_types': {
            'numeric': X.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical': X.select_dtypes(include=['object', 'category']).columns.tolist()
        }
    }
    
    logger.debug(f"Training data analysis: {analysis['n_samples']} samples, {analysis['n_features']} features")
    return analysis


def check_data_quality(X: pd.DataFrame, y: pd.Series) -> tuple[bool, str]:
    """
    Check if data is suitable for training.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for empty data
    if len(X) == 0:
        return False, "Feature data is empty"
    
    if len(y) == 0:
        return False, "Target data is empty"
    
    # Check for size mismatch
    if len(X) != len(y):
        return False, f"Feature and target sizes don't match: X={len(X)}, y={len(y)}"
    
    # Check for too many missing values
    missing_ratio = X.isnull().sum().sum() / (len(X) * len(X.columns)) if len(X.columns) > 0 else 0
    if missing_ratio > 0.5:
        return False, f"Too many missing values in features: {missing_ratio:.1%}"
    
    # Check for constant features
    constant_features = [col for col in X.columns if X[col].nunique() <= 1]
    if constant_features:
        return False, f"Constant features found: {constant_features}"
    
    return True, "Data quality check passed"


def get_feature_info(X: pd.DataFrame) -> Dict:
    """
    Get information about features.
    
    Args:
        X: Feature DataFrame
        
    Returns:
        Dictionary with feature information
    """
    numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
    
    info = {
        'total_features': len(X.columns),
        'numeric_features': len(numeric_features),
        'categorical_features': len(categorical_features),
        'feature_names': X.columns.tolist(),
        'numeric_feature_names': numeric_features,
        'categorical_feature_names': categorical_features
    }
    
    if numeric_features:
        numeric_df = X[numeric_features]
        info['numeric_stats'] = {
            'mean_std': float(numeric_df.std().mean()) if len(numeric_df) > 0 else 0,
            'has_zeros': (numeric_df == 0).any().any()
        }
    
    return info


# ============================================================================
# Hyperparameter Optimization Analysis Functions
# ============================================================================

def analyze_hyperparameter_importance(optimization_results: Dict) -> Dict:
    """
    Analyze which hyperparameters are most important.
    
    Args:
        optimization_results: Results from hyperparameter optimization
        
    Returns:
        Dictionary with hyperparameter importance analysis
    """
    # This would analyze the optimization results to determine
    # which hyperparameters have the most impact
    # For now, return a placeholder structure
    
    analysis = {
        'important_parameters': [],
        'parameter_ranges': {},
        'optimization_impact': {}
    }
    
    if 'best_params' in optimization_results:
        analysis['best_parameters'] = optimization_results['best_params']
    
    if 'best_score' in optimization_results:
        analysis['best_score'] = optimization_results['best_score']
    
    logger.debug("Hyperparameter importance analysis completed")
    return analysis


def get_optimization_summary(optimization_results: Dict) -> Dict:
    """
    Get summary of optimization results.
    
    Args:
        optimization_results: Results from hyperparameter optimization
        
    Returns:
        Dictionary with optimization summary
    """
    summary = {
        'optimization_completed': 'best_score' in optimization_results,
        'best_score': optimization_results.get('best_score', None),
        'best_params': optimization_results.get('best_params', {}),
        'n_iterations': optimization_results.get('n_iterations', 0),
        'optimization_time': optimization_results.get('optimization_time', 0)
    }
    
    return summary


def suggest_parameter_ranges(model_name: str, problem_type: str) -> Dict:
    """
    Suggest parameter ranges for a model.
    
    Args:
        model_name: Name of the model
        problem_type: Problem type
        
    Returns:
        Dictionary with suggested parameter ranges
    """
    # This would use LLM or heuristics to suggest parameter ranges
    # For now, return empty dict (hyperparameter optimization removed)
    logger.debug("suggest_parameter_ranges called but hyperparameter optimization is disabled")
    return {}