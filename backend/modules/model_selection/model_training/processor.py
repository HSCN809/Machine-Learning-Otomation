"""Model training processor functions."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, RandomizedSearchCV
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB
import logging
import time

logger = logging.getLogger(__name__)

try:
    import xgboost as xgb
except ImportError:
    xgb = None
    logger.warning("xgboost not available, XGBoost models will not work")


def create_model_instance(model_name: str, problem_type: str, random_state: int = 42) -> Any:
    """
    Create a model instance based on model name and problem type.
    
    Args:
        model_name: Name of the model
        problem_type: Problem type ('classification' or 'regression')
        random_state: Random state for reproducibility
        
    Returns:
        Model instance
    """
    is_classification = problem_type in ['binary_classification', 'multiclass_classification']
    
    if model_name == 'Logistic Regression':
        return LogisticRegression(random_state=random_state, max_iter=1000)
    elif model_name == 'Linear Regression':
        return LinearRegression()
    elif model_name == 'Random Forest':
        if is_classification:
            return RandomForestClassifier(n_estimators=100, random_state=random_state, n_jobs=-1)
        else:
            return RandomForestRegressor(n_estimators=100, random_state=random_state, n_jobs=-1)
    elif model_name == 'XGBoost':
        if xgb is None:
            raise ImportError("xgboost is not installed. Please install it with: pip install xgboost")
        if is_classification:
            return xgb.XGBClassifier(random_state=random_state, n_jobs=-1, eval_metric='logloss')
        else:
            return xgb.XGBRegressor(random_state=random_state, n_jobs=-1)
    elif model_name == 'SVM':
        if is_classification:
            return SVC(random_state=random_state, probability=True)
        else:
            return SVR()
    elif model_name == 'KNN':
        if is_classification:
            return KNeighborsClassifier(n_neighbors=5)
        else:
            return KNeighborsRegressor(n_neighbors=5)
    elif model_name == 'Naive Bayes':
        if is_classification:
            return GaussianNB()
        else:
            raise ValueError("Naive Bayes is only for classification")
    elif model_name == 'Ridge':
        return Ridge(random_state=random_state)
    elif model_name == 'Lasso':
        return Lasso(random_state=random_state, max_iter=1000)
    elif model_name == 'Elastic Net':
        return ElasticNet(random_state=random_state, max_iter=1000)
    else:
        raise ValueError(f"Unknown model name: {model_name}")


def split_data(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, 
               random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data into training and testing sets.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        test_size: Proportion of test set (default: 0.2)
        random_state: Random state for reproducibility
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y if y.dtype == 'object' or y.nunique() < 20 else None
    )
    
    logger.info(f"Data split: Train={len(X_train)}, Test={len(X_test)}")
    return X_train, X_test, y_train, y_test


def get_param_grid_for_model(model_name: str, problem_type: str, 
                             n_samples: int, n_features: int) -> Dict:
    """
    Get parameter grid for a model based on model type and dataset characteristics.
    
    Args:
        model_name: Name of the model
        problem_type: Problem type
        n_samples: Number of training samples
        n_features: Number of features
        
    Returns:
        Dictionary with parameter grid
    """
    is_classification = problem_type in ['binary_classification', 'multiclass_classification']
    
    # Determine grid complexity based on dataset size
    if n_samples < 1000:
        # Small dataset: simpler grid, fewer combinations
        grid_type = 'small'
        logger.info(f"📊 {model_name} için küçük veri seti tespit edildi ({n_samples} örnek) - Basit grid kullanılıyor")
    elif n_samples < 10000:
        # Medium dataset: normal grid
        grid_type = 'medium'
        logger.info(f"📊 {model_name} için orta veri seti tespit edildi ({n_samples} örnek) - Normal grid kullanılıyor")
    else:
        # Large dataset: more combinations
        grid_type = 'large'
        logger.info(f"📊 {model_name} için büyük veri seti tespit edildi ({n_samples} örnek) - Geniş grid kullanılıyor")
    
    if model_name == 'Logistic Regression':
        if grid_type == 'small':
            return {
                'C': [0.1, 1, 10],
                'penalty': ['l2'],
                'solver': ['lbfgs', 'liblinear']
            }
        elif grid_type == 'medium':
            return {
                'C': [0.01, 0.1, 1, 10, 100],
                'penalty': ['l1', 'l2'],
                'solver': ['liblinear', 'lbfgs']
            }
        else:  # large
            return {
                'C': [0.001, 0.01, 0.1, 1, 10, 100],
                'penalty': ['l1', 'l2'],
                'solver': ['liblinear', 'lbfgs', 'sag'] if n_samples > 50000 else ['liblinear', 'lbfgs']
            }
    
    elif model_name == 'Random Forest':
        if grid_type == 'small':
            return {
                'n_estimators': [50, 100],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5]
            }
        elif grid_type == 'medium':
            return {
                'n_estimators': [50, 100, 200],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2]
            }
        else:  # large
            return {
                'n_estimators': [100, 200, 300],
                'max_depth': [15, 20, 25, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
    
    elif model_name == 'XGBoost':
        if grid_type == 'small':
            return {
                'n_estimators': [50, 100],
                'max_depth': [3, 5],
                'learning_rate': [0.1, 0.3]
            }
        elif grid_type == 'medium':
            return {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.3],
                'subsample': [0.8, 1.0]
            }
        else:  # large
            return {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.3],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0]
            }
    
    elif model_name == 'SVM':
        # SVM is slow, use simpler grid for large datasets
        if n_samples > 10000:
            # For large datasets, prefer linear kernel
            return {
                'C': [0.1, 1, 10],
                'kernel': ['linear', 'rbf'],
                'gamma': ['scale']
            }
        elif grid_type == 'small':
            return {
                'C': [0.1, 1, 10],
                'kernel': ['linear', 'rbf'],
                'gamma': ['scale', 'auto']
            }
        else:  # medium
            return {
                'C': [0.1, 1, 10, 100],
                'kernel': ['linear', 'rbf', 'poly'],
                'gamma': ['scale', 'auto', 0.001, 0.01]
            }
    
    elif model_name == 'KNN':
        # KNN: n_neighbors should be based on dataset size
        max_neighbors = min(20, n_samples // 10)  # Don't use more than 20% of data
        if max_neighbors < 5:
            max_neighbors = 5
        
        return {
            'n_neighbors': list(range(3, max_neighbors + 1, 2))  # Odd numbers: 3, 5, 7, ...
        }
    
    elif model_name == 'Linear Regression':
        # Linear Regression has limited hyperparameters
        return {
            'fit_intercept': [True, False]
        }
    
    elif model_name == 'Naive Bayes':
        return {
            'var_smoothing': [1e-9, 1e-8, 1e-7, 1e-6, 1e-5]
        }
    
    elif model_name == 'Ridge':
        return {
            'alpha': [0.1, 1, 10, 100, 1000]
        }
    
    elif model_name == 'Lasso':
        return {
            'alpha': [0.001, 0.01, 0.1, 1, 10]
        }
    
    elif model_name == 'Elastic Net':
        return {
            'alpha': [0.001, 0.01, 0.1, 1, 10],
            'l1_ratio': [0.1, 0.5, 0.7, 0.9]
        }
    
    return {}


def train_model_with_hyperparameter_optimization(
    model_name: str, X_train: pd.DataFrame, y_train: pd.Series,
    problem_type: str, random_state: int = 42,
    use_cross_validation: bool = False, cv_folds: int = 5) -> Dict:
    """
    Train a model with automatic hyperparameter optimization using GridSearchCV.
    
    Args:
        model_name: Name of the model
        X_train: Training features
        y_train: Training target
        problem_type: Problem type
        random_state: Random state
        use_cross_validation: Whether to use cross-validation (always True for GridSearch)
        cv_folds: Number of CV folds for GridSearch
        
    Returns:
        Dictionary with trained model and training info
    """
    start_time = time.time()
    
    try:
        n_samples = len(X_train)
        n_features = len(X_train.columns)
        
        logger.info(f"🔍 {model_name} için parametre grid'i oluşturuluyor | Veri: {n_samples} örnek, {n_features} özellik")
        
        # Get parameter grid based on model and dataset
        param_grid = get_param_grid_for_model(model_name, problem_type, n_samples, n_features)
        
        if not param_grid:
            # No grid available, raise error
            error_msg = f"{model_name} için parametre grid'i bulunamadı. GridSearchCV çalıştırılamıyor."
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # Calculate number of parameter combinations
        import math
        total_combinations = 1
        for param_values in param_grid.values():
            total_combinations *= len(param_values) if isinstance(param_values, list) else 1
        
        logger.info(f"📋 {model_name} parametre grid'i hazır | {len(param_grid)} parametre, ~{total_combinations} kombinasyon")
        
        # Create base model
        base_model = create_model_instance(model_name, problem_type, random_state)
        
        # Handle missing values
        if X_train.isnull().any().any():
            logger.warning(f"Missing values found in training data, using simple imputation")
            from sklearn.impute import SimpleImputer
            imputer = SimpleImputer(strategy='mean' if X_train.select_dtypes(include=[np.number]).shape[1] > 0 else 'most_frequent')
            X_train_imputed = pd.DataFrame(
                imputer.fit_transform(X_train),
                columns=X_train.columns,
                index=X_train.index
            )
        else:
            X_train_imputed = X_train
        
        # Determine scoring
        scoring = 'accuracy' if problem_type in ['binary_classification', 'multiclass_classification'] else 'r2'
        
        # Use GridSearchCV for optimization
        logger.info(f"🔧 Starting GridSearchCV for {model_name} | Veri: {n_samples} örnek, {n_features} özellik | {total_combinations} parametre kombinasyonu | CV: {cv_folds} fold")
        logger.info(f"📋 {model_name} parametre grid'i: {list(param_grid.keys())}")
        
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=cv_folds,
            scoring=scoring,
            n_jobs=-1,
            verbose=0,
            return_train_score=False
        )
        
        logger.info(f"⚙️ {model_name} GridSearchCV eğitimi başlıyor...")
        grid_search.fit(X_train_imputed, y_train)
        
        training_time = time.time() - start_time
        
        # Get best model
        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        best_score = grid_search.best_score_
        n_combinations_tested = len(grid_search.cv_results_['params'])
        
        logger.info(f"✅ {model_name} GridSearchCV tamamlandı | Süre: {training_time:.2f}s | Test edilen kombinasyon: {n_combinations_tested}")
        logger.info(f"🎯 {model_name} En iyi CV skoru: {best_score:.4f}")
        logger.info(f"🎯 {model_name} En iyi parametreler: {best_params}")
        
        # Calculate CV scores on best model (for consistency)
        cv_scores = cross_val_score(best_model, X_train_imputed, y_train, cv=cv_folds, scoring=scoring)
        
        result = {
            'model': best_model,
            'model_name': model_name,
            'training_time': training_time,
            'training_samples': n_samples,
            'n_features': n_features,
            'cv_scores': cv_scores.tolist(),
            'cv_mean': float(cv_scores.mean()),
            'cv_std': float(cv_scores.std()),
            'best_params': best_params,
            'best_cv_score': float(best_score),
            'optimization_method': 'grid_search',
            'n_param_combinations': n_combinations_tested,
            'cv_folds': cv_folds,
            'success': True,
            'error': None
        }
        
        logger.info(f"✅ {model_name} optimize edildi ve eğitildi | Toplam süre: {training_time:.2f}s | CV Ortalama: {cv_scores.mean():.4f} | CV Std: {cv_scores.std():.4f}")
        return result
        
    except Exception as e:
        training_time = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ {model_name} GridSearchCV optimizasyonu sırasında hata: {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return error result - no fallback
        return {
            'model': None,
            'model_name': model_name,
            'training_time': training_time,
            'training_samples': n_samples,
            'n_features': n_features,
            'cv_scores': None,
            'cv_mean': None,
            'cv_std': None,
            'best_params': None,
            'best_cv_score': None,
            'optimization_method': None,
            'n_param_combinations': 0,
            'success': False,
            'error': error_msg
        }


def train_model(model_name: str, X_train: pd.DataFrame, y_train: pd.Series,
                problem_type: str, random_state: int = 42,
                use_cross_validation: bool = False, cv_folds: int = 5) -> Dict:
    """
    Train a single model with automatic hyperparameter optimization.
    
    Args:
        model_name: Name of the model
        X_train: Training features
        y_train: Training target
        problem_type: Problem type
        random_state: Random state
        use_cross_validation: Whether to use cross-validation (always True for GridSearch)
        cv_folds: Number of CV folds
        
    Returns:
        Dictionary with trained model and training info
    """
    # Always use hyperparameter optimization
    return train_model_with_hyperparameter_optimization(
        model_name, X_train, y_train, problem_type,
        random_state, use_cross_validation, cv_folds
    )


def train_multiple_models(model_names: List[str], X_train: pd.DataFrame, y_train: pd.Series,
                         problem_type: str, random_state: int = 42,
                         use_cross_validation: bool = False, cv_folds: int = 5) -> Dict[str, Dict]:
    """
    Train multiple models.
    
    Args:
        model_names: List of model names to train
        X_train: Training features
        y_train: Training target
        problem_type: Problem type
        random_state: Random state
        use_cross_validation: Whether to use cross-validation
        cv_folds: Number of CV folds
        
    Returns:
        Dictionary mapping model names to training results
    """
    results = {}
    
    for model_name in model_names:
        logger.info(f"Training model: {model_name}")
        result = train_model(
            model_name, X_train, y_train, problem_type,
            random_state, use_cross_validation, cv_folds
        )
        results[model_name] = result
    
    successful_models = [name for name, result in results.items() if result['success']]
    logger.info(f"Successfully trained {len(successful_models)}/{len(model_names)} models")
    
    return results


