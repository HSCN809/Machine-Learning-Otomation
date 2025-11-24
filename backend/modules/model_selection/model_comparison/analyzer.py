"""Model comparison analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def analyze_model_rankings(model_results: Dict[str, Dict], problem_type: str) -> Dict:
    """
    Analyze model rankings across different metrics.
    
    Args:
        model_results: Dictionary mapping model names to their results
        problem_type: Problem type
        
    Returns:
        Dictionary with ranking analysis
    """
    if problem_type in ['binary_classification', 'multiclass_classification']:
        primary_metric = 'accuracy'
        secondary_metrics = ['f1_score', 'precision', 'recall']
    else:
        primary_metric = 'r2_score'
        secondary_metrics = ['rmse', 'mae']
    
    rankings = {}
    
    # Rank by primary metric
    primary_scores = {}
    for model_name, results in model_results.items():
        metrics = results.get('metrics', {})
        if primary_metric in metrics:
            primary_scores[model_name] = metrics[primary_metric]
    
    if primary_scores:
        sorted_models = sorted(primary_scores.items(), key=lambda x: x[1], reverse=True)
        rankings['primary_metric'] = {
            'metric': primary_metric,
            'rankings': [{'model': name, 'score': score} for name, score in sorted_models]
        }
    
    # Rank by secondary metrics
    for metric in secondary_metrics:
        scores = {}
        for model_name, results in model_results.items():
            metrics = results.get('metrics', {})
            if metric in metrics:
                scores[model_name] = metrics[metric]
        
        if scores:
            # For regression metrics like RMSE, lower is better
            reverse = metric not in ['rmse', 'mae', 'mse']
            sorted_models = sorted(scores.items(), key=lambda x: x[1], reverse=reverse)
            rankings[metric] = {
                'metric': metric,
                'rankings': [{'model': name, 'score': score} for name, score in sorted_models]
            }
    
    return rankings


def identify_best_models(model_results: Dict[str, Dict], problem_type: str, top_n: int = 3) -> List[str]:
    """
    Identify best models based on multiple metrics.
    
    Args:
        model_results: Dictionary mapping model names to their results
        problem_type: Problem type
        top_n: Number of top models to return
        
    Returns:
        List of best model names
    """
    if problem_type in ['binary_classification', 'multiclass_classification']:
        primary_metric = 'accuracy'
    else:
        primary_metric = 'r2_score'
    
    scores = {}
    for model_name, results in model_results.items():
        metrics = results.get('metrics', {})
        if primary_metric in metrics:
            scores[model_name] = metrics[primary_metric]
    
    if not scores:
        return []
    
    # Sort and get top N
    sorted_models = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [name for name, _ in sorted_models[:top_n]]


def get_comparison_insights(model_results: Dict[str, Dict], problem_type: str) -> Dict:
    """
    Get insights from model comparison.
    
    Args:
        model_results: Dictionary mapping model names to their results
        problem_type: Problem type
        
    Returns:
        Dictionary with comparison insights
    """
    insights = {
        'summary': {},
        'recommendations': []
    }
    
    if not model_results:
        return insights
    
    # Get best model
    best_models = identify_best_models(model_results, problem_type, top_n=1)
    if best_models:
        best_model = best_models[0]
        insights['summary']['best_model'] = best_model
        insights['summary']['best_model_metrics'] = model_results[best_model].get('metrics', {})
    
    # Performance spread
    if problem_type in ['binary_classification', 'multiclass_classification']:
        metric = 'accuracy'
    else:
        metric = 'r2_score'
    
    scores = [results.get('metrics', {}).get(metric, 0) for results in model_results.values()]
    if scores:
        insights['summary']['performance_spread'] = {
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores))
        }
        
        # Recommendations
        if insights['summary']['performance_spread']['std'] < 0.05:
            insights['recommendations'].append('Modeller arasında performans farkı küçük. En basit modeli seçebilirsiniz.')
        elif insights['summary']['performance_spread']['max'] - insights['summary']['performance_spread']['min'] > 0.2:
            insights['recommendations'].append('Modeller arasında önemli performans farkı var. En iyi performanslı modeli seçin.')
    
    return insights

