"""Model interpretation analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def analyze_feature_importance(importance_dict: Dict[str, float], top_n: int = 10) -> Dict:
    """
    Analyze feature importance results.
    
    Args:
        importance_dict: Dictionary mapping feature names to importance scores
        top_n: Number of top features to analyze
        
    Returns:
        Dictionary with feature importance analysis
    """
    if not importance_dict:
        return {'error': 'No feature importance data'}
    
    # Sort by importance
    sorted_features = sorted(importance_dict.items(), key=lambda x: abs(x[1]), reverse=True)
    
    top_features = sorted_features[:top_n]
    
    analysis = {
        'total_features': len(importance_dict),
        'top_features': [{'feature': feat, 'importance': float(imp)} for feat, imp in top_features],
        'importance_stats': {
            'mean': float(np.mean(list(importance_dict.values()))),
            'std': float(np.std(list(importance_dict.values()))),
            'max': float(np.max(list(importance_dict.values()))),
            'min': float(np.min(list(importance_dict.values())))
        }
    }
    
    # Calculate cumulative importance
    total_importance = sum(abs(imp) for _, imp in importance_dict.items())
    cumulative = 0
    cumulative_importance = []
    
    for feat, imp in sorted_features:
        cumulative += abs(imp)
        cumulative_importance.append({
            'feature': feat,
            'cumulative_importance': float(cumulative / total_importance) if total_importance > 0 else 0
        })
    
    analysis['cumulative_importance'] = cumulative_importance[:top_n]
    
    return analysis


def get_interpretation_summary(model, feature_names: List[str], 
                              importance_method: str = 'default') -> Dict:
    """
    Get summary of model interpretation.
    
    Args:
        model: Trained model
        feature_names: List of feature names
        importance_method: Method used for importance calculation
        
    Returns:
        Dictionary with interpretation summary
    """
    summary = {
        'model_type': type(model).__name__,
        'n_features': len(feature_names),
        'importance_method': importance_method,
        'has_feature_importance': hasattr(model, 'feature_importances_')
    }
    
    return summary


def identify_key_features(importance_dict: Dict[str, float], 
                         threshold: float = 0.1) -> List[str]:
    """
    Identify key features based on importance threshold.
    
    Args:
        importance_dict: Dictionary mapping feature names to importance scores
        threshold: Minimum importance threshold (as proportion of max)
        
    Returns:
        List of key feature names
    """
    if not importance_dict:
        return []
    
    max_importance = max(abs(imp) for imp in importance_dict.values())
    threshold_value = max_importance * threshold
    
    key_features = [
        feat for feat, imp in importance_dict.items()
        if abs(imp) >= threshold_value
    ]
    
    return key_features

