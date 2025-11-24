"""Model evaluation analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def analyze_model_performance(metrics: Dict, problem_type: str) -> Dict:
    """
    Analyze model performance based on metrics.
    
    Args:
        metrics: Dictionary of metrics
        problem_type: Problem type
        
    Returns:
        Dictionary with performance analysis
    """
    analysis = {
        'overall_performance': 'unknown',
        'strengths': [],
        'weaknesses': [],
        'recommendations': []
    }
    
    if problem_type in ['binary_classification', 'multiclass_classification']:
        accuracy = metrics.get('accuracy', 0)
        f1 = metrics.get('f1_score', 0)
        
        if accuracy >= 0.9:
            analysis['overall_performance'] = 'excellent'
            analysis['strengths'].append('Yüksek doğruluk oranı')
        elif accuracy >= 0.7:
            analysis['overall_performance'] = 'good'
            analysis['strengths'].append('İyi doğruluk oranı')
        elif accuracy >= 0.5:
            analysis['overall_performance'] = 'fair'
            analysis['weaknesses'].append('Düşük doğruluk oranı')
        else:
            analysis['overall_performance'] = 'poor'
            analysis['weaknesses'].append('Çok düşük doğruluk oranı')
        
        if f1 < 0.5:
            analysis['weaknesses'].append('Düşük F1 skoru - class imbalance olabilir')
            analysis['recommendations'].append('Class imbalance teknikleri kullanılabilir')
    
    elif problem_type == 'regression':
        r2 = metrics.get('r2_score', 0)
        rmse = metrics.get('rmse', float('inf'))
        
        if r2 >= 0.9:
            analysis['overall_performance'] = 'excellent'
            analysis['strengths'].append('Yüksek R² skoru')
        elif r2 >= 0.7:
            analysis['overall_performance'] = 'good'
            analysis['strengths'].append('İyi R² skoru')
        elif r2 >= 0.5:
            analysis['overall_performance'] = 'fair'
            analysis['weaknesses'].append('Düşük R² skoru')
        else:
            analysis['overall_performance'] = 'poor'
            analysis['weaknesses'].append('Çok düşük R² skoru')
    
    return analysis


def compare_metrics(metrics_list: List[Dict], metric_name: str) -> Dict:
    """
    Compare a specific metric across multiple models.
    
    Args:
        metrics_list: List of metric dictionaries
        metric_name: Name of metric to compare
        
    Returns:
        Dictionary with comparison results
    """
    values = [m.get(metric_name, None) for m in metrics_list]
    values = [v for v in values if v is not None]
    
    if not values:
        return {'error': f'Metric {metric_name} not found in any model'}
    
    return {
        'metric_name': metric_name,
        'values': values,
        'mean': float(np.mean(values)),
        'std': float(np.std(values)),
        'min': float(np.min(values)),
        'max': float(np.max(values)),
        'range': float(np.max(values) - np.min(values))
    }


def get_metric_explanations(problem_type: str) -> Dict[str, str]:
    """
    Get explanations for metrics based on problem type.
    
    Args:
        problem_type: Problem type
        
    Returns:
        Dictionary mapping metric names to explanations
    """
    if problem_type in ['binary_classification', 'multiclass_classification']:
        return {
            'accuracy': 'Doğru tahmin edilen örneklerin oranı. Genel performans göstergesi.',
            'precision': 'Pozitif olarak tahmin edilenlerin gerçekten pozitif olma oranı. False positive\'leri önler.',
            'recall': 'Gerçek pozitiflerin ne kadarının doğru tahmin edildiği. False negative\'leri önler.',
            'f1_score': 'Precision ve Recall\'un harmonik ortalaması. Dengeli performans ölçüsü.',
            'roc_auc': 'ROC eğrisinin altındaki alan. Binary classification için model ayırt etme gücü.',
            'confusion_matrix': 'Gerçek ve tahmin edilen değerlerin karşılaştırması. Hata türlerini gösterir.'
        }
    elif problem_type == 'regression':
        return {
            'mae': 'Mean Absolute Error. Ortalama mutlak hata. Gerçek değerlerden ortalama sapma.',
            'mse': 'Mean Squared Error. Ortalama karesel hata. Büyük hataları daha fazla cezalandırır.',
            'rmse': 'Root Mean Squared Error. MSE\'nin karekökü. Orijinal birimlerde hata ölçüsü.',
            'r2_score': 'R² skoru. Modelin varyansı açıklama oranı. 1\'e yakın = iyi performans.',
            'adjusted_r2': 'Düzeltilmiş R². Feature sayısını hesaba katan R² versiyonu.'
        }
    else:
        return {}

