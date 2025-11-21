"""Advanced data analysis functions for EDA module."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats


def calculate_correlations(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """
    Calculate correlation matrix for numeric columns.
    
    Args:
        df: DataFrame to analyze
        method: Correlation method ('pearson', 'kendall', 'spearman')
        
    Returns:
        Correlation matrix as DataFrame
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) < 2:
        return pd.DataFrame()
    
    return df[numeric_cols].corr(method=method)


def detect_outliers(df: pd.DataFrame, column: str, method: str = 'iqr') -> Dict:
    """
    Detect outliers in a numeric column.
    
    Args:
        df: DataFrame to analyze
        column: Column name
        method: Detection method ('iqr' or 'zscore')
        
    Returns:
        Dictionary with outlier information
    """
    if column not in df.columns:
        return {
            'outlier_count': 0,
            'outlier_percentage': 0.0,
            'outlier_indices': [],
            'method': method
        }
    
    col_data = df[column].dropna()
    
    if len(col_data) == 0:
        return {
            'outlier_count': 0,
            'outlier_percentage': 0.0,
            'outlier_indices': [],
            'method': method
        }
    
    if method == 'iqr':
        Q1 = col_data.quantile(0.25)
        Q3 = col_data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
        outlier_indices = outliers.index.tolist()
        
    elif method == 'zscore':
        z_scores = np.abs(stats.zscore(col_data))
        outlier_indices = col_data[z_scores > 3].index.tolist()
        outliers = col_data.loc[outlier_indices]
    else:
        return {
            'outlier_count': 0,
            'outlier_percentage': 0.0,
            'outlier_indices': [],
            'method': method
        }
    
    return {
        'outlier_count': len(outlier_indices),
        'outlier_percentage': (len(outlier_indices) / len(col_data)) * 100,
        'outlier_indices': outlier_indices,
        'outlier_values': outliers.tolist(),
        'method': method
    }


def analyze_distributions(df: pd.DataFrame, column: str) -> Dict:
    """
    Analyze distribution of a numeric column.
    
    Args:
        df: DataFrame to analyze
        column: Column name
        
    Returns:
        Dictionary with distribution statistics
    """
    if column not in df.columns:
        return {}
    
    col_data = df[column].dropna()
    
    if len(col_data) == 0:
        return {}
    
    # Basic statistics
    mean = col_data.mean()
    median = col_data.median()
    std = col_data.std()
    skewness = col_data.skew()
    kurtosis = col_data.kurtosis()
    
    # Normality test (Shapiro-Wilk for small samples, otherwise Kolmogorov-Smirnov)
    if len(col_data) <= 5000:
        try:
            stat, p_value = stats.shapiro(col_data)
            normality_test = 'shapiro-wilk'
        except:
            stat, p_value = stats.kstest(col_data, 'norm', args=(mean, std))
            normality_test = 'kolmogorov-smirnov'
    else:
        # For large samples, use Kolmogorov-Smirnov
        stat, p_value = stats.kstest(col_data, 'norm', args=(mean, std))
        normality_test = 'kolmogorov-smirnov'
    
    is_normal = p_value > 0.05
    
    return {
        'mean': mean,
        'median': median,
        'std': std,
        'skewness': skewness,
        'kurtosis': kurtosis,
        'normality_test': normality_test,
        'normality_statistic': stat,
        'normality_p_value': p_value,
        'is_normal': is_normal,
        'min': col_data.min(),
        'max': col_data.max(),
        'q25': col_data.quantile(0.25),
        'q75': col_data.quantile(0.75)
    }


def get_multivariate_stats(df: pd.DataFrame, columns: List[str]) -> Dict:
    """
    Get multivariate statistics for selected columns.
    
    Args:
        df: DataFrame to analyze
        columns: List of column names
        
    Returns:
        Dictionary with multivariate statistics
    """
    if not columns or len(columns) < 2:
        return {}
    
    # Filter to only numeric columns
    numeric_cols = [col for col in columns if col in df.columns and df[col].dtype in [np.number]]
    
    if len(numeric_cols) < 2:
        return {}
    
    subset_df = df[numeric_cols].dropna()
    
    if len(subset_df) == 0:
        return {}
    
    corr_matrix = subset_df.corr()
    
    return {
        'columns': numeric_cols,
        'correlation_matrix': corr_matrix,
        'sample_size': len(subset_df)
    }

