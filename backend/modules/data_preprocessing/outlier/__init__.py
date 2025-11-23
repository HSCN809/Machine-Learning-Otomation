"""Outlier handling module for data preprocessing."""

# Import processor functions
from .processor import remove_outliers_iqr
from .processor import cap_outliers_iqr
from .processor import remove_outliers_zscore
from .processor import cap_outliers_zscore
from .processor import remove_outliers_isolation_forest
from .processor import remove_outliers_lof
from .processor import apply_outlier_method

# Import analyzer functions
from .analyzer import get_data_statistics
from .analyzer import compare_data_statistics
from .analyzer import analyze_outliers
from .analyzer import analyze_outliers_iqr
from .analyzer import analyze_outliers_zscore
from .analyzer import analyze_outliers_isolation_forest
from .analyzer import analyze_outliers_lof
from .analyzer import get_all_outlier_info

__all__ = [
    # Processor functions
    'remove_outliers_iqr',
    'cap_outliers_iqr',
    'remove_outliers_zscore',
    'cap_outliers_zscore',
    'remove_outliers_isolation_forest',
    'remove_outliers_lof',
    'apply_outlier_method',
    # Analyzer functions
    'get_data_statistics',
    'compare_data_statistics',
    'analyze_outliers',
    'analyze_outliers_iqr',
    'analyze_outliers_zscore',
    'analyze_outliers_isolation_forest',
    'analyze_outliers_lof',
    'get_all_outlier_info'
]

