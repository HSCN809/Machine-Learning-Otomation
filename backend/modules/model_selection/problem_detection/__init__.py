"""Problem detection module for identifying classification vs regression tasks."""

from .analyzer import (
    analyze_target_variable,
    get_target_statistics,
    detect_class_imbalance
)

from .processor import (
    detect_problem_type,
    get_problem_type_info,
    validate_target_variable
)

__all__ = [
    # Analyzer functions
    'analyze_target_variable',
    'get_target_statistics',
    'detect_class_imbalance',
    # Processor functions
    'detect_problem_type',
    'get_problem_type_info',
    'validate_target_variable'
]

