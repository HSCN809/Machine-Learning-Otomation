"""Feature engineering module for data preprocessing."""

from .processor import (
    remove_duplicate_rows,
    drop_columns,
    create_numeric_feature,
    create_datetime_feature,
    create_categorical_combination,
    apply_feature_engineering_method
)

from .analyzer import (
    analyze_duplicate_rows,
    analyze_irrelevant_columns,
    get_feature_engineering_summary
)

# LLM enhancer removed - will be added back later if needed
# from .llm_enhancer import (
#     suggest_feature_engineering_steps
# )

__all__ = [
    # Processor functions
    'remove_duplicate_rows',
    'drop_columns',
    'create_numeric_feature',
    'create_datetime_feature',
    'create_categorical_combination',
    'apply_feature_engineering_method',
    # Analyzer functions
    'analyze_duplicate_rows',
    'analyze_irrelevant_columns',
    'get_feature_engineering_summary',
    # LLM enhancer functions - removed, will be added back later if needed
    # 'suggest_feature_engineering_steps'
]

