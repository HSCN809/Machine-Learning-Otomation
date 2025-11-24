"""LLM enhancement functions for model training step."""

# LLM entegrasyonu şimdilik yok
# Bu dosya gelecekte LLM önerileri için kullanılabilir

import logging

logger = logging.getLogger(__name__)


def suggest_training_parameters(df, target_column, problem_type, model_name):
    """
    Placeholder for future LLM-based training parameter suggestions.
    
    Args:
        df: DataFrame
        target_column: Target column name
        problem_type: Problem type
        model_name: Model name
        
    Returns:
        Empty dict (no suggestions for now)
    """
    logger.debug("LLM suggestions not implemented yet for model training")
    return {}


def suggest_hyperparameter_ranges(model_name, problem_type, dataset_characteristics):
    """
    Placeholder for future LLM-based hyperparameter range suggestions.
    
    Args:
        model_name: Model name
        problem_type: Problem type
        dataset_characteristics: Dataset characteristics
        
    Returns:
        Empty dict (no suggestions for now)
    """
    logger.debug("LLM suggestions not implemented yet for hyperparameter optimization")
    return {}
