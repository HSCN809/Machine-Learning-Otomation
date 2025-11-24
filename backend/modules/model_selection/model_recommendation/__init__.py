"""Model recommendation module for suggesting appropriate ML models."""

from .analyzer import (
    analyze_data_for_recommendation,
    get_dataset_characteristics,
    assess_model_suitability
)

from .processor import (
    recommend_models,
    get_model_descriptions,
    get_default_models,
    rank_models_by_suitability
)

__all__ = [
    # Analyzer functions
    'analyze_data_for_recommendation',
    'get_dataset_characteristics',
    'assess_model_suitability',
    # Processor functions
    'recommend_models',
    'get_model_descriptions',
    'get_default_models',
    'rank_models_by_suitability'
]

