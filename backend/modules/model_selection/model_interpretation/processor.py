"""Model interpretation processor functions."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from sklearn.inspection import permutation_importance
import logging

logger = logging.getLogger(__name__)


def get_feature_importance(model: Any, feature_names: List[str]) -> Dict[str, float]:
    """
    Get feature importance from a model.
    
    Args:
        model: Trained model
        feature_names: List of feature names
        
    Returns:
        Dictionary mapping feature names to importance scores
    """
    importance_dict = {}
    
    try:
        # Tree-based models have feature_importances_
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            importance_dict = dict(zip(feature_names, importances))
        # Linear models have coef_
        elif hasattr(model, 'coef_'):
            # For binary classification, coef_ is 1D
            # For multiclass, coef_ is 2D
            coef = model.coef_
            if coef.ndim > 1:
                # Use mean absolute coefficient across classes
                importances = np.mean(np.abs(coef), axis=0)
            else:
                importances = np.abs(coef)
            importance_dict = dict(zip(feature_names, importances))
        else:
            logger.warning("Model does not have feature_importances_ or coef_ attribute")
            # Return equal importance for all features
            importance_dict = {feat: 1.0 / len(feature_names) for feat in feature_names}
    
    except Exception as e:
        logger.error(f"Error getting feature importance: {e}")
        importance_dict = {feat: 0.0 for feat in feature_names}
    
    return importance_dict


def calculate_shap_values(model: Any, X: pd.DataFrame, 
                         max_samples: int = 100) -> Optional[Dict]:
    """
    Calculate SHAP values for model interpretation.
    
    Args:
        model: Trained model
        X: Feature DataFrame
        max_samples: Maximum number of samples to use (for performance)
        
    Returns:
        Dictionary with SHAP values, or None if SHAP is not available
    """
    try:
        import shap
    except ImportError:
        logger.warning("SHAP library not installed. Install with: pip install shap")
        return None
    
    try:
        # Limit samples for performance
        if len(X) > max_samples:
            X_sample = X.sample(n=max_samples, random_state=42)
        else:
            X_sample = X
        
        # Create SHAP explainer based on model type
        if hasattr(model, 'predict_proba'):
            explainer = shap.TreeExplainer(model) if hasattr(model, 'feature_importances_') else shap.KernelExplainer(model.predict_proba, X_sample)
        else:
            explainer = shap.TreeExplainer(model) if hasattr(model, 'feature_importances_') else shap.KernelExplainer(model.predict, X_sample)
        
        shap_values = explainer.shap_values(X_sample)
        
        # Handle different SHAP output formats
        if isinstance(shap_values, list):
            # Multi-class classification
            shap_values = np.mean([np.abs(sv) for sv in shap_values], axis=0)
        
        # Calculate mean absolute SHAP values per feature
        mean_shap = np.mean(np.abs(shap_values), axis=0)
        
        result = {
            'shap_values': shap_values.tolist() if isinstance(shap_values, np.ndarray) else shap_values,
            'mean_abs_shap': dict(zip(X.columns, mean_shap.tolist())),
            'feature_names': X.columns.tolist()
        }
        
        logger.info("SHAP values calculated successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error calculating SHAP values: {e}")
        return None


def get_permutation_importance(model: Any, X: pd.DataFrame, y: pd.Series,
                               scoring: Optional[str] = None, n_repeats: int = 10,
                               random_state: int = 42) -> Dict[str, float]:
    """
    Calculate permutation importance.
    
    Args:
        model: Trained model
        X: Feature DataFrame
        y: Target Series
        scoring: Scoring metric
        n_repeats: Number of repeats for permutation
        random_state: Random state
        
    Returns:
        Dictionary mapping feature names to importance scores
    """
    try:
        # Handle missing values
        if X.isnull().any().any():
            from sklearn.impute import SimpleImputer
            imputer = SimpleImputer(strategy='mean' if X.select_dtypes(include=[np.number]).shape[1] > 0 else 'most_frequent')
            X_imputed = pd.DataFrame(
                imputer.fit_transform(X),
                columns=X.columns,
                index=X.index
            )
        else:
            X_imputed = X
        
        # Calculate permutation importance
        perm_importance = permutation_importance(
            model, X_imputed, y, scoring=scoring,
            n_repeats=n_repeats, random_state=random_state, n_jobs=-1
        )
        
        importance_dict = dict(zip(X.columns, perm_importance.importances_mean))
        
        logger.info("Permutation importance calculated successfully")
        return importance_dict
        
    except Exception as e:
        logger.error(f"Error calculating permutation importance: {e}")
        return {feat: 0.0 for feat in X.columns}


def explain_prediction(model: Any, X: pd.DataFrame, instance_idx: int,
                      feature_names: List[str]) -> Dict:
    """
    Explain a single prediction.
    
    Args:
        model: Trained model
        X: Feature DataFrame
        instance_idx: Index of instance to explain
        feature_names: List of feature names
        
    Returns:
        Dictionary with prediction explanation
    """
    if instance_idx >= len(X):
        return {'error': f'Instance index {instance_idx} out of range'}
    
    instance = X.iloc[[instance_idx]]
    
    try:
        prediction = model.predict(instance)[0]
        
        explanation = {
            'instance_idx': instance_idx,
            'prediction': float(prediction) if isinstance(prediction, (int, float, np.number)) else str(prediction),
            'feature_values': instance.iloc[0].to_dict()
        }
        
        # Add probabilities if available
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(instance)[0]
            explanation['probabilities'] = probabilities.tolist()
        
        # Add feature importance if available
        importance = get_feature_importance(model, feature_names)
        explanation['feature_importance'] = importance
        
        return explanation
        
    except Exception as e:
        logger.error(f"Error explaining prediction: {e}")
        return {'error': str(e)}

