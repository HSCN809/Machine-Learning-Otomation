"""Model recommendation analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def analyze_data_for_recommendation(df: pd.DataFrame, target_column: str, problem_type: str) -> Dict:
    """
    Analyze dataset characteristics for model recommendation.
    
    Args:
        df: DataFrame containing the data
        target_column: Name of the target column
        problem_type: Problem type ('classification', 'regression', etc.)
        
    Returns:
        Dictionary with dataset characteristics
    """
    # Remove target column for feature analysis
    feature_df = df.drop(columns=[target_column])
    
    # Basic characteristics
    n_samples = len(df)
    n_features = len(feature_df.columns)
    
    # Feature types
    numeric_features = feature_df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = feature_df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Missing values
    missing_percentage = (feature_df.isnull().sum().sum() / (n_samples * n_features)) * 100 if n_samples > 0 and n_features > 0 else 0
    
    # Feature statistics
    feature_stats = {
        'n_samples': n_samples,
        'n_features': n_features,
        'n_numeric_features': len(numeric_features),
        'n_categorical_features': len(categorical_features),
        'missing_percentage': missing_percentage,
        'feature_ratio': n_features / n_samples if n_samples > 0 else 0
    }
    
    # Dataset size category
    if n_samples < 1000:
        feature_stats['size_category'] = 'small'
    elif n_samples < 10000:
        feature_stats['size_category'] = 'medium'
    else:
        feature_stats['size_category'] = 'large'
    
    # Feature count category
    if n_features < 10:
        feature_stats['feature_category'] = 'low'
    elif n_features < 50:
        feature_stats['feature_category'] = 'medium'
    else:
        feature_stats['feature_category'] = 'high'
    
    # Numeric feature statistics
    if numeric_features:
        numeric_df = feature_df[numeric_features]
        feature_stats['numeric_stats'] = {
            'mean_std': float(numeric_df.std().mean()) if len(numeric_df) > 0 else 0,
            'mean_range': float((numeric_df.max() - numeric_df.min()).mean()) if len(numeric_df) > 0 else 0
        }
    
    logger.debug(f"Data analysis completed: {n_samples} samples, {n_features} features")
    return feature_stats


def get_dataset_characteristics(df: pd.DataFrame, target_column: str) -> Dict:
    """
    Get comprehensive dataset characteristics.
    
    Args:
        df: DataFrame containing the data
        target_column: Name of the target column
        
    Returns:
        Dictionary with dataset characteristics
    """
    feature_df = df.drop(columns=[target_column])
    
    characteristics = {
        'shape': {
            'rows': len(df),
            'columns': len(df.columns),
            'features': len(feature_df.columns)
        },
        'data_types': {
            'numeric': feature_df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical': feature_df.select_dtypes(include=['object', 'category']).columns.tolist()
        },
        'missing_values': {
            'total': int(feature_df.isnull().sum().sum()),
            'percentage': float((feature_df.isnull().sum().sum() / (len(df) * len(feature_df.columns))) * 100) if len(df) > 0 and len(feature_df.columns) > 0 else 0
        },
        'sparsity': {
            'is_sparse': feature_df.isnull().sum().sum() > (len(df) * len(feature_df.columns) * 0.3)
        }
    }
    
    return characteristics


def assess_model_suitability(model_name: str, dataset_characteristics: Dict, problem_type: str) -> Dict:
    """
    Assess how suitable a model is for the given dataset.
    
    Args:
        model_name: Name of the model
        dataset_characteristics: Dataset characteristics dictionary
        problem_type: Problem type
        
    Returns:
        Dictionary with suitability assessment
    """
    n_samples = dataset_characteristics.get('n_samples', 0)
    n_features = dataset_characteristics.get('n_features', 0)
    size_category = dataset_characteristics.get('size_category', 'medium')
    feature_category = dataset_characteristics.get('feature_category', 'medium')
    
    suitability = {
        'model_name': model_name,
        'suitability_score': 0.5,  # Default score
        'reasons': [],
        'warnings': []
    }
    
    # Model-specific suitability rules
    if model_name in ['Logistic Regression', 'Linear Regression']:
        # Good for small to medium datasets
        if size_category == 'small' or size_category == 'medium':
            suitability['suitability_score'] = 0.8
            suitability['reasons'].append('Basit ve hızlı, küçük-orta veri setleri için uygun')
        else:
            suitability['suitability_score'] = 0.6
            suitability['reasons'].append('Büyük veri setleri için yavaş olabilir')
        
        # High feature count warning
        if feature_category == 'high':
            suitability['warnings'].append('Yüksek feature sayısı için regularization gerekebilir')
    
    elif model_name in ['Random Forest', 'XGBoost']:
        # Good for all sizes, better for medium to large
        if size_category in ['medium', 'large']:
            suitability['suitability_score'] = 0.9
            suitability['reasons'].append('Güçlü performans, orta-büyük veri setleri için ideal')
        else:
            suitability['suitability_score'] = 0.7
            suitability['reasons'].append('Küçük veri setleri için overfitting riski')
    
    elif model_name == 'SVM':
        # Good for medium datasets, struggles with large
        if size_category == 'medium':
            suitability['suitability_score'] = 0.8
            suitability['reasons'].append('Orta boyutlu veri setleri için uygun')
        elif size_category == 'small':
            suitability['suitability_score'] = 0.7
            suitability['reasons'].append('Küçük veri setleri için uygun')
        else:
            suitability['suitability_score'] = 0.5
            suitability['warnings'].append('Büyük veri setleri için yavaş olabilir')
    
    elif model_name in ['KNN', 'Naive Bayes']:
        # Good for small to medium datasets
        if size_category in ['small', 'medium']:
            suitability['suitability_score'] = 0.7
            suitability['reasons'].append('Küçük-orta veri setleri için uygun')
        else:
            suitability['suitability_score'] = 0.5
            suitability['warnings'].append('Büyük veri setleri için yavaş')
    
    elif model_name in ['Ridge', 'Lasso', 'Elastic Net']:
        # Good for high feature count
        if feature_category == 'high':
            suitability['suitability_score'] = 0.9
            suitability['reasons'].append('Yüksek feature sayısı için regularization sağlar')
        else:
            suitability['suitability_score'] = 0.7
            suitability['reasons'].append('Düşük feature sayısı için de uygun')
    
    return suitability

