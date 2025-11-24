"""Model evaluation processor functions."""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, classification_report,
    mean_absolute_error, mean_squared_error, r2_score
)
import logging

logger = logging.getLogger(__name__)


def calculate_metrics(y_true: pd.Series, y_pred: pd.Series, 
                     problem_type: str, y_pred_proba: Optional[np.ndarray] = None) -> Dict:
    """
    Calculate metrics based on problem type.
    
    Args:
        y_true: True target values
        y_pred: Predicted target values
        problem_type: Problem type
        y_pred_proba: Predicted probabilities (for classification)
        
    Returns:
        Dictionary of metrics
    """
    if problem_type in ['binary_classification', 'multiclass_classification']:
        return evaluate_classification_model(y_true, y_pred, y_pred_proba, problem_type)
    elif problem_type == 'regression':
        return evaluate_regression_model(y_true, y_pred)
    else:
        return {}


def evaluate_classification_model(y_true: pd.Series, y_pred: pd.Series,
                                 y_pred_proba: Optional[np.ndarray] = None,
                                 problem_type: str = 'multiclass_classification') -> Dict:
    """
    Evaluate classification model.
    
    Args:
        y_true: True target values
        y_pred: Predicted target values
        y_pred_proba: Predicted probabilities
        problem_type: Problem type
        
    Returns:
        Dictionary of classification metrics
    """
    metrics = {}
    
    try:
        # Basic metrics
        metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
        
        # For binary classification, use binary averaging
        # For multiclass, use macro and weighted averaging
        if problem_type == 'binary_classification':
            metrics['precision'] = float(precision_score(y_true, y_pred, average='binary', zero_division=0))
            metrics['recall'] = float(recall_score(y_true, y_pred, average='binary', zero_division=0))
            metrics['f1_score'] = float(f1_score(y_true, y_pred, average='binary', zero_division=0))
            
            # ROC AUC for binary classification
            if y_pred_proba is not None:
                try:
                    # Handle binary case - use probabilities for positive class
                    if y_pred_proba.ndim > 1 and y_pred_proba.shape[1] > 1:
                        y_pred_proba_binary = y_pred_proba[:, 1]
                    else:
                        y_pred_proba_binary = y_pred_proba.flatten()
                    
                    metrics['roc_auc'] = float(roc_auc_score(y_true, y_pred_proba_binary))
                except Exception as e:
                    logger.warning(f"ROC AUC calculation failed: {e}")
                    metrics['roc_auc'] = None
        else:
            # Multiclass classification
            metrics['precision_macro'] = float(precision_score(y_true, y_pred, average='macro', zero_division=0))
            metrics['precision_weighted'] = float(precision_score(y_true, y_pred, average='weighted', zero_division=0))
            metrics['recall_macro'] = float(recall_score(y_true, y_pred, average='macro', zero_division=0))
            metrics['recall_weighted'] = float(recall_score(y_true, y_pred, average='weighted', zero_division=0))
            metrics['f1_score_macro'] = float(f1_score(y_true, y_pred, average='macro', zero_division=0))
            metrics['f1_score_weighted'] = float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
            
            # Use macro as primary
            metrics['precision'] = metrics['precision_macro']
            metrics['recall'] = metrics['recall_macro']
            metrics['f1_score'] = metrics['f1_score_macro']
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        logger.debug(f"Classification metrics calculated: accuracy={metrics['accuracy']:.4f}")
        
    except Exception as e:
        logger.error(f"Error calculating classification metrics: {e}")
        metrics['error'] = str(e)
    
    return metrics


def evaluate_regression_model(y_true: pd.Series, y_pred: pd.Series) -> Dict:
    """
    Evaluate regression model.
    
    Args:
        y_true: True target values
        y_pred: Predicted target values
        
    Returns:
        Dictionary of regression metrics
    """
    metrics = {}
    
    try:
        metrics['mae'] = float(mean_absolute_error(y_true, y_pred))
        metrics['mse'] = float(mean_squared_error(y_true, y_pred))
        metrics['rmse'] = float(np.sqrt(metrics['mse']))
        metrics['r2_score'] = float(r2_score(y_true, y_pred))
        
        # Adjusted R²
        n = len(y_true)
        p = 1  # Number of features (simplified)
        if n - p - 1 > 0:
            metrics['adjusted_r2'] = float(1 - (1 - metrics['r2_score']) * (n - 1) / (n - p - 1))
        else:
            metrics['adjusted_r2'] = metrics['r2_score']
        
        # Mean Absolute Percentage Error (MAPE)
        if (y_true != 0).any():
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
            metrics['mape'] = float(mape)
        else:
            metrics['mape'] = None
        
        logger.debug(f"Regression metrics calculated: R²={metrics['r2_score']:.4f}, RMSE={metrics['rmse']:.4f}")
        
    except Exception as e:
        logger.error(f"Error calculating regression metrics: {e}")
        metrics['error'] = str(e)
    
    return metrics


def get_confusion_matrix(y_true: pd.Series, y_pred: pd.Series) -> np.ndarray:
    """
    Get confusion matrix.
    
    Args:
        y_true: True target values
        y_pred: Predicted target values
        
    Returns:
        Confusion matrix as numpy array
    """
    return confusion_matrix(y_true, y_pred)


def get_classification_report(y_true: pd.Series, y_pred: pd.Series, 
                             target_names: Optional[list] = None) -> str:
    """
    Get classification report as string.
    
    Args:
        y_true: True target values
        y_pred: Predicted target values
        target_names: Optional list of target class names
        
    Returns:
        Classification report string
    """
    return classification_report(y_true, y_pred, target_names=target_names)

