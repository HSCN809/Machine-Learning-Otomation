"""Model evaluation module for evaluating machine learning models."""

from .analyzer import (
    get_metric_explanations
)

from .processor import (
    evaluate_classification_model,
    evaluate_regression_model,
    calculate_metrics,
    get_confusion_matrix
)

__all__ = [
    # Analyzer functions
    'get_metric_explanations',
    # Processor functions
    'evaluate_classification_model',
    'evaluate_regression_model',
    'calculate_metrics',
    'get_confusion_matrix'
]

