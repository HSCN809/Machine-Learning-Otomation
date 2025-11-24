"""Model recommendation processor functions."""

import pandas as pd
from typing import Dict, List, Optional
import logging

from .analyzer import analyze_data_for_recommendation, assess_model_suitability

logger = logging.getLogger(__name__)


# Model definitions
CLASSIFICATION_MODELS = {
    'Logistic Regression': {
        'description': 'Doğrusal sınıflandırma modeli. Hızlı ve yorumlanabilir.',
        'pros': ['Hızlı eğitim', 'Yorumlanabilir', 'Küçük veri setleri için uygun'],
        'cons': ['Doğrusal ilişkiler varsayar', 'Yüksek feature sayısı için regularization gerekir'],
        'best_for': ['Küçük-orta veri setleri', 'Binary classification', 'Hızlı prototipleme']
    },
    'Random Forest': {
        'description': 'Ensemble ağaç tabanlı model. Güçlü ve esnek.',
        'pros': ['Yüksek performans', 'Feature importance sağlar', 'Overfitting\'e dirençli'],
        'cons': ['Yorumlanabilirlik düşük', 'Büyük veri setlerinde yavaş'],
        'best_for': ['Orta-büyük veri setleri', 'Non-linear ilişkiler', 'Feature importance gerekli']
    },
    'XGBoost': {
        'description': 'Gradient boosting tabanlı güçlü ensemble model.',
        'pros': ['Çok yüksek performans', 'Hızlı eğitim', 'Otomatik feature selection'],
        'cons': ['Hiperparametre tuning gerekir', 'Overfitting riski'],
        'best_for': ['Büyük veri setleri', 'Yarışmalar ve production', 'Yüksek doğruluk gerekli']
    },
    'SVM': {
        'description': 'Support Vector Machine. Kernel trick ile non-linear ilişkileri yakalar.',
        'pros': ['Non-linear ilişkiler', 'Yüksek boyutlu veriler için uygun'],
        'cons': ['Büyük veri setlerinde yavaş', 'Hiperparametre tuning kritik'],
        'best_for': ['Orta boyutlu veri setleri', 'Non-linear sınırlar', 'Yüksek boyutlu feature space']
    },
    'KNN': {
        'description': 'K-Nearest Neighbors. Basit ve anlaşılır.',
        'pros': ['Basit ve anlaşılır', 'Non-parametric', 'Hızlı eğitim'],
        'cons': ['Büyük veri setlerinde yavaş tahmin', 'Feature scaling gerekli'],
        'best_for': ['Küçük veri setleri', 'Non-linear ilişkiler', 'Hızlı prototipleme']
    },
    'Naive Bayes': {
        'description': 'Olasılık tabanlı basit sınıflandırıcı.',
        'pros': ['Çok hızlı', 'Küçük veri setleri için uygun', 'Yüksek boyutlu veriler için uygun'],
        'cons': ['Bağımsızlık varsayımı', 'Düşük performans'],
        'best_for': ['Küçük veri setleri', 'Text classification', 'Yüksek boyutlu veriler']
    }
}

REGRESSION_MODELS = {
    'Linear Regression': {
        'description': 'Doğrusal regresyon modeli. Basit ve yorumlanabilir.',
        'pros': ['Hızlı eğitim', 'Yorumlanabilir', 'Küçük veri setleri için uygun'],
        'cons': ['Doğrusal ilişkiler varsayar', 'Outlier\'lara duyarlı'],
        'best_for': ['Küçük-orta veri setleri', 'Doğrusal ilişkiler', 'Hızlı prototipleme']
    },
    'Random Forest': {
        'description': 'Ensemble ağaç tabanlı regresyon modeli.',
        'pros': ['Yüksek performans', 'Non-linear ilişkiler', 'Feature importance'],
        'cons': ['Yorumlanabilirlik düşük', 'Büyük veri setlerinde yavaş'],
        'best_for': ['Orta-büyük veri setleri', 'Non-linear ilişkiler']
    },
    'XGBoost': {
        'description': 'Gradient boosting tabanlı güçlü regresyon modeli.',
        'pros': ['Çok yüksek performans', 'Hızlı eğitim', 'Otomatik feature selection'],
        'cons': ['Hiperparametre tuning gerekir', 'Overfitting riski'],
        'best_for': ['Büyük veri setleri', 'Yüksek doğruluk gerekli']
    },
    'SVM': {
        'description': 'Support Vector Regression. Non-linear ilişkileri yakalar.',
        'pros': ['Non-linear ilişkiler', 'Yüksek boyutlu veriler'],
        'cons': ['Büyük veri setlerinde yavaş', 'Hiperparametre tuning kritik'],
        'best_for': ['Orta boyutlu veri setleri', 'Non-linear ilişkiler']
    },
    'Ridge': {
        'description': 'L2 regularization ile doğrusal regresyon.',
        'pros': ['Multicollinearity\'yi handle eder', 'Yüksek feature sayısı için uygun'],
        'cons': ['Feature selection yapmaz', 'Tüm feature\'ları kullanır'],
        'best_for': ['Yüksek feature sayısı', 'Multicollinearity problemi']
    },
    'Lasso': {
        'description': 'L1 regularization ile feature selection yapan regresyon.',
        'pros': ['Feature selection yapar', 'Sparse modeller oluşturur'],
        'cons': ['Sadece bir feature seçer (gruplar halinde değil)'],
        'best_for': ['Feature selection gerekli', 'Sparse modeller']
    },
    'Elastic Net': {
        'description': 'Ridge ve Lasso\'nun kombinasyonu.',
        'pros': ['Hem L1 hem L2 regularization', 'Feature selection ve multicollinearity'],
        'cons': ['İki hiperparametre tuning gerekir'],
        'best_for': ['Yüksek feature sayısı', 'Feature selection + regularization']
    }
}


def get_default_models(problem_type: str) -> List[str]:
    """
    Get default models for a problem type.
    
    Args:
        problem_type: Problem type ('classification', 'regression', etc.)
        
    Returns:
        List of default model names
    """
    if problem_type in ['binary_classification', 'multiclass_classification']:
        return ['Logistic Regression', 'Random Forest', 'XGBoost', 'SVM', 'KNN', 'Naive Bayes']
    elif problem_type == 'regression':
        return ['Linear Regression', 'Random Forest', 'XGBoost', 'SVM', 'Ridge', 'Lasso', 'Elastic Net']
    else:
        return []


def recommend_models(df: pd.DataFrame, target_column: str, problem_type: str, 
                    max_models: int = 6) -> List[Dict]:
    """
    Recommend models based on dataset characteristics and problem type.
    
    Args:
        df: DataFrame containing the data
        target_column: Name of the target column
        problem_type: Problem type
        max_models: Maximum number of models to recommend
        
    Returns:
        List of recommended models with information
    """
    # Analyze dataset
    dataset_characteristics = analyze_data_for_recommendation(df, target_column, problem_type)
    
    # Get default models for problem type
    default_models = get_default_models(problem_type)
    
    # Assess suitability for each model
    model_suitabilities = []
    for model_name in default_models:
        suitability = assess_model_suitability(model_name, dataset_characteristics, problem_type)
        model_suitabilities.append(suitability)
    
    # Sort by suitability score
    model_suitabilities.sort(key=lambda x: x['suitability_score'], reverse=True)
    
    # Get top models
    top_models = model_suitabilities[:max_models]
    
    # Add model descriptions
    model_dict = CLASSIFICATION_MODELS if problem_type in ['binary_classification', 'multiclass_classification'] else REGRESSION_MODELS
    
    recommendations = []
    for model_info in top_models:
        model_name = model_info['model_name']
        if model_name in model_dict:
            recommendation = {
                'model_name': model_name,
                'description': model_dict[model_name]['description'],
                'pros': model_dict[model_name]['pros'],
                'cons': model_dict[model_name]['cons'],
                'best_for': model_dict[model_name]['best_for'],
                'suitability_score': model_info['suitability_score'],
                'reasons': model_info['reasons'],
                'warnings': model_info['warnings']
            }
            recommendations.append(recommendation)
    
    logger.info(f"Recommended {len(recommendations)} models for {problem_type}")
    return recommendations


def get_model_descriptions(problem_type: str) -> Dict[str, Dict]:
    """
    Get descriptions for all models of a problem type.
    
    Args:
        problem_type: Problem type
        
    Returns:
        Dictionary of model descriptions
    """
    if problem_type in ['binary_classification', 'multiclass_classification']:
        return CLASSIFICATION_MODELS
    elif problem_type == 'regression':
        return REGRESSION_MODELS
    else:
        return {}


def rank_models_by_suitability(df: pd.DataFrame, target_column: str, 
                               problem_type: str, model_names: List[str]) -> List[Dict]:
    """
    Rank models by their suitability for the dataset.
    
    Args:
        df: DataFrame containing the data
        target_column: Name of the target column
        problem_type: Problem type
        model_names: List of model names to rank
        
    Returns:
        List of models ranked by suitability
    """
    dataset_characteristics = analyze_data_for_recommendation(df, target_column, problem_type)
    
    rankings = []
    for model_name in model_names:
        suitability = assess_model_suitability(model_name, dataset_characteristics, problem_type)
        rankings.append(suitability)
    
    rankings.sort(key=lambda x: x['suitability_score'], reverse=True)
    return rankings

