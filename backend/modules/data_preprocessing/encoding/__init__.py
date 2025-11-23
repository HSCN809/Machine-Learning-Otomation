"""Encoding module for data preprocessing."""

from .processor import (
    label_encode,
    one_hot_encode,
    ordinal_encode,
    binary_encode,
    frequency_encode
)

from .analyzer import (
    analyze_categorical_columns,
    get_categorical_statistics
)

from .llm_enhancer import suggest_encoding_steps

__all__ = [
    # Processor functions
    'label_encode',
    'one_hot_encode',
    'ordinal_encode',
    'binary_encode',
    'frequency_encode',
    # Analyzer functions
    'analyze_categorical_columns',
    'get_categorical_statistics',
    # LLM enhancer
    'suggest_encoding_steps'
]

