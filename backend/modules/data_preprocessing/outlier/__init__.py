"""Outlier handling module for data preprocessing."""

# Import processor functions
from .processor import cap_outliers_iqr
from .processor import apply_outlier_method

# Import analyzer functions
from .analyzer import get_data_statistics
from .analyzer import compare_data_statistics
from .analyzer import analyze_outliers
from .analyzer import analyze_outliers_iqr
from .analyzer import get_all_outlier_info

__all__ = [
    # Processor functions
    'cap_outliers_iqr',
    'apply_outlier_method',
    # Analyzer functions
    'get_data_statistics',
    'compare_data_statistics',
    'analyze_outliers',
    'analyze_outliers_iqr',
    'get_all_outlier_info'
]

