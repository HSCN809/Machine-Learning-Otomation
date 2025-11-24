"""Model selection module for machine learning automation."""

# Problem Detection
from .problem_detection import (
    detect_problem_type,
    analyze_target_variable,
    get_problem_type_info
)

# Model Recommendation
from .model_recommendation import (
    recommend_models,
    get_model_descriptions,
    analyze_data_for_recommendation
)

# Model Training
from .model_training import (
    train_model,
    train_multiple_models,
    split_data
)

# Model Evaluation
from .model_evaluation import (
    evaluate_classification_model,
    evaluate_regression_model,
    calculate_metrics
)

# Model Comparison
from .model_comparison import (
    compare_models,
    get_best_model,
    create_comparison_table
)


# Model Interpretation
from .model_interpretation import (
    get_feature_importance,
    calculate_shap_values,
    get_permutation_importance
)

__all__ = [
    # Problem Detection
    'detect_problem_type',
    'analyze_target_variable',
    'get_problem_type_info',
    # Model Recommendation
    'recommend_models',
    'get_model_descriptions',
    'analyze_data_for_recommendation',
    # Model Training
    'train_model',
    'train_multiple_models',
    'split_data',
    # Model Evaluation
    'evaluate_classification_model',
    'evaluate_regression_model',
    'calculate_metrics',
    # Model Comparison
    'compare_models',
    'get_best_model',
    'create_comparison_table',
    # Model Interpretation
    'get_feature_importance',
    'calculate_shap_values',
    'get_permutation_importance'
]

