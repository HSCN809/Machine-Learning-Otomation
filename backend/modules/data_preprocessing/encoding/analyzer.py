"""Encoding analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict, List


def analyze_categorical_columns(df: pd.DataFrame) -> Dict:
    """Analyze categorical columns for encoding recommendations.
    
    Returns:
        Dictionary with categorical column analysis including:
        - column_name: Column name
        - data_type: Data type
        - unique_count: Number of unique values
        - cardinality: 'Yüksek' (>10) or 'Düşük' (<=10)
        - encoding_status: 'Yapıldı' or 'Yapılmadı' (based on whether column is numeric)
    """
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    analysis = {
        'categorical_columns': [],
        'total_categorical': len(categorical_cols),
        'total_rows': len(df)
    }
    
    for col in categorical_cols:
        unique_count = df[col].nunique()
        cardinality = 'Yüksek' if unique_count > 10 else 'Düşük'
        
        # Check if column has been encoded (converted to numeric)
        # This is a simple heuristic: if column is numeric, it might be encoded
        # But we'll track encoding status separately in session state
        encoding_status = 'Yapılmadı'  # Default, will be updated by frontend
        
        col_info = {
            'column_name': col,
            'data_type': str(df[col].dtype),
            'unique_count': unique_count,
            'cardinality': cardinality,
            'encoding_status': encoding_status
        }
        
        analysis['categorical_columns'].append(col_info)
    
    return analysis


def get_categorical_statistics(df: pd.DataFrame) -> Dict:
    """Get detailed statistics for categorical columns.
    
    Returns:
        Dictionary with statistics for each categorical column
    """
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    stats = {}
    for col in categorical_cols:
        stats[col] = {
            'unique_count': df[col].nunique(),
            'total_count': len(df),
            'missing_count': df[col].isnull().sum(),
            'missing_percentage': (df[col].isnull().sum() / len(df)) * 100 if len(df) > 0 else 0,
            'most_frequent': df[col].mode().iloc[0] if len(df[col].mode()) > 0 else None,
            'most_frequent_count': df[col].value_counts().iloc[0] if len(df[col].value_counts()) > 0 else 0,
            'most_frequent_percentage': (df[col].value_counts().iloc[0] / len(df)) * 100 if len(df[col].value_counts()) > 0 else 0
        }
    
    return stats

