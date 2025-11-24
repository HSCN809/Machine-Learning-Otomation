"""Model comparison processor functions."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def compare_models(model_results: Dict[str, Dict], problem_type: str) -> pd.DataFrame:
    """
    Compare multiple models and create a comparison table.
    
    Args:
        model_results: Dictionary mapping model names to their results
        problem_type: Problem type
        
    Returns:
        DataFrame with model comparison
    """
    comparison_data = []
    
    for model_name, results in model_results.items():
        metrics = results.get('metrics', {})
        training_info = results.get('training_info', {})
        
        row = {
            'Model': model_name,
            'Training Time (s)': training_info.get('training_time', 0)
        }
        
        # Add metrics based on problem type
        if problem_type in ['binary_classification', 'multiclass_classification']:
            row['Accuracy'] = metrics.get('accuracy', None)
            row['Precision'] = metrics.get('precision', None)
            row['Recall'] = metrics.get('recall', None)
            row['F1 Score'] = metrics.get('f1_score', None)
            if 'roc_auc' in metrics:
                row['ROC AUC'] = metrics.get('roc_auc', None)
        else:
            row['R² Score'] = metrics.get('r2_score', None)
            row['RMSE'] = metrics.get('rmse', None)
            row['MAE'] = metrics.get('mae', None)
            row['Adjusted R²'] = metrics.get('adjusted_r2', None)
        
        comparison_data.append(row)
    
    df = pd.DataFrame(comparison_data)
    return df


def get_best_model(model_results: Dict[str, Dict], problem_type: str, 
                  metric: Optional[str] = None) -> Optional[str]:
    """
    Get the best model based on primary metric.
    
    Args:
        model_results: Dictionary mapping model names to their results
        problem_type: Problem type
        metric: Optional specific metric to use
        
    Returns:
        Name of the best model, or None if no models
    """
    if not model_results:
        return None
    
    # Determine primary metric
    if metric is None:
        if problem_type in ['binary_classification', 'multiclass_classification']:
            metric = 'accuracy'
        else:
            metric = 'r2_score'
    
    best_model = None
    best_score = float('-inf') if metric != 'rmse' and metric != 'mae' else float('inf')
    
    for model_name, results in model_results.items():
        metrics = results.get('metrics', {})
        if metric in metrics:
            score = metrics[metric]
            
            # For regression metrics like RMSE, lower is better
            if metric in ['rmse', 'mae', 'mse']:
                if score < best_score:
                    best_score = score
                    best_model = model_name
            else:
                if score > best_score:
                    best_score = score
                    best_model = model_name
    
    return best_model


def create_comparison_table(model_results: Dict[str, Dict], problem_type: str) -> pd.DataFrame:
    """
    Create a formatted comparison table.
    
    Args:
        model_results: Dictionary mapping model names to their results
        problem_type: Problem type
        
    Returns:
        Formatted DataFrame
    """
    df = compare_models(model_results, problem_type)
    
    # Sort by primary metric
    if problem_type in ['binary_classification', 'multiclass_classification']:
        sort_col = 'Accuracy'
    else:
        sort_col = 'R² Score'
    
    if sort_col in df.columns:
        df = df.sort_values(by=sort_col, ascending=False, na_position='last')
    
    return df


def rank_models_by_metric(model_results: Dict[str, Dict], metric: str, 
                         ascending: bool = False) -> List[tuple]:
    """
    Rank models by a specific metric.
    
    Args:
        model_results: Dictionary mapping model names to their results
        metric: Metric name to rank by
        ascending: Whether to sort ascending (for metrics where lower is better)
        
    Returns:
        List of (model_name, score) tuples, sorted
    """
    scores = []
    
    for model_name, results in model_results.items():
        metrics = results.get('metrics', {})
        if metric in metrics:
            scores.append((model_name, metrics[metric]))
    
    scores.sort(key=lambda x: x[1], reverse=not ascending)
    return scores

