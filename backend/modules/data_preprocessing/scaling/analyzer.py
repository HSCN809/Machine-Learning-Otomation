"""Scaling analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from scipy import stats


def analyze_numeric_columns(df: pd.DataFrame) -> Dict:
    """Analyze numeric columns for scaling recommendations.
    
    Returns:
        Dictionary with numeric column analysis including:
        - column_name: Column name
        - data_type: Data type
        - mean: Mean value
        - std: Standard deviation
        - min: Minimum value
        - max: Maximum value
        - range: Value range (max - min)
        - coefficient_of_variation: CV = std / mean (if mean != 0)
        - skewness: Skewness value
        - scaling_status: 'Yapıldı' or 'Yapılmadı'
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    analysis = {
        'numeric_columns': [],
        'total_numeric': len(numeric_cols),
        'total_rows': len(df)
    }
    
    for col in numeric_cols:
        col_data = df[col].dropna()
        
        if len(col_data) == 0:
            continue
        
        mean_val = col_data.mean()
        std_val = col_data.std()
        min_val = col_data.min()
        max_val = col_data.max()
        range_val = max_val - min_val if max_val != min_val else 0
        cv = (std_val / mean_val) if mean_val != 0 else np.inf
        
        # Calculate skewness
        try:
            skewness = stats.skew(col_data)
        except:
            skewness = 0
        
        col_info = {
            'column_name': col,
            'data_type': str(df[col].dtype),
            'mean': float(mean_val) if pd.notna(mean_val) else None,
            'std': float(std_val) if pd.notna(std_val) else None,
            'min': float(min_val) if pd.notna(min_val) else None,
            'max': float(max_val) if pd.notna(max_val) else None,
            'range': float(range_val) if pd.notna(range_val) else None,
            'coefficient_of_variation': float(cv) if pd.notna(cv) and not np.isinf(cv) else None,
            'skewness': float(skewness) if pd.notna(skewness) else None,
            'scaling_status': 'Yapılmadı'  # Default, will be updated by frontend
        }
        
        analysis['numeric_columns'].append(col_info)
    
    return analysis


def get_scaling_statistics(df: pd.DataFrame) -> Dict:
    """Get detailed statistics for numeric columns to help with scaling decisions.
    
    Returns:
        Dictionary with statistics for each numeric column
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    stats_dict = {}
    for col in numeric_cols:
        col_data = df[col].dropna()
        
        if len(col_data) == 0:
            continue
        
        mean_val = col_data.mean()
        std_val = col_data.std()
        median_val = col_data.median()
        q1 = col_data.quantile(0.25)
        q3 = col_data.quantile(0.75)
        iqr = q3 - q1
        
        # Calculate skewness and kurtosis
        try:
            skewness = stats.skew(col_data)
            kurtosis = stats.kurtosis(col_data)
        except:
            skewness = 0
            kurtosis = 0
        
        # Check for outliers using IQR
        # Get min, max, and unique values for binary column check
        min_val = col_data.min()
        max_val = col_data.max()
        unique_values = col_data.unique()
        range_val = max_val - min_val if max_val != min_val else 0
        
        # Check if binary column (only 0 and 1 values, or range = 1 with min=0, max=1)
        is_binary = (
            (min_val == 0 and max_val == 1 and len(unique_values) <= 2) or
            (range_val == 1 and min_val == 0 and max_val == 1 and len(unique_values) <= 2)
        )
        
        # If IQR is 0, all values are the same, no outliers
        # Also check for binary columns (0-1 range) - outliers don't make sense for binary data
        if iqr == 0 or np.isnan(iqr) or is_binary:
            outliers = 0
            outlier_percentage = 0.0
        else:
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = ((col_data < lower_bound) | (col_data > upper_bound)).sum()
            outlier_percentage = (outliers / len(col_data)) * 100 if len(col_data) > 0 else 0
        
        stats_dict[col] = {
            'mean': float(mean_val) if pd.notna(mean_val) else None,
            'std': float(std_val) if pd.notna(std_val) else None,
            'median': float(median_val) if pd.notna(median_val) else None,
            'min': float(col_data.min()) if pd.notna(col_data.min()) else None,
            'max': float(col_data.max()) if pd.notna(col_data.max()) else None,
            'q1': float(q1) if pd.notna(q1) else None,
            'q3': float(q3) if pd.notna(q3) else None,
            'iqr': float(iqr) if pd.notna(iqr) else None,
            'skewness': float(skewness) if pd.notna(skewness) else None,
            'kurtosis': float(kurtosis) if pd.notna(kurtosis) else None,
            'outlier_count': int(outliers),
            'outlier_percentage': float(outlier_percentage),
            'has_outliers': outliers > 0
        }
    
    return stats_dict


def get_scaling_recommendations(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict:
    """Get scaling method recommendations for numeric columns.
    
    Args:
        df: Input DataFrame
        columns: List of column names to analyze (None for all numeric columns)
    
    Returns:
        Dictionary with recommendations for each column
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    recommendations = {}
    stats_dict = get_scaling_statistics(df)
    
    for col in columns:
        if col not in stats_dict:
            continue
        
        stats = stats_dict[col]
        skewness = stats.get('skewness', 0)
        has_outliers = stats.get('has_outliers', False)
        outlier_pct = stats.get('outlier_percentage', 0)
        
        # Recommendation logic
        if abs(skewness) > 1:
            # Highly skewed data -> power transform
            recommended_method = 'power_transform'
            reason = f"Veri çarpık (skewness: {skewness:.2f}). Power transformation normal dağılıma yaklaştırır."
        elif has_outliers and outlier_pct > 10:
            # Data with significant outliers -> robust scaler
            recommended_method = 'robust_scaler'
            reason = f"Aykırı değerler mevcut (%{outlier_pct:.1f}). Robust scaler aykırı değerlere karşı dayanıklıdır."
        elif abs(skewness) > 0.5:
            # Moderately skewed -> standard scaler or robust scaler
            recommended_method = 'robust_scaler'
            reason = f"Orta düzeyde çarpıklık (skewness: {skewness:.2f}). Robust scaler önerilir."
        else:
            # Normal distribution -> standard scaler
            recommended_method = 'standard_scaler'
            reason = "Normal dağılıma yakın veri. Standard scaler uygundur."
        
        recommendations[col] = {
            'recommended_method': recommended_method,
            'reason': reason,
            'stats': stats
        }
    
    return recommendations

