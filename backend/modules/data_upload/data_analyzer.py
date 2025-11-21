"""Data analysis module for statistical analysis of numeric and categorical columns."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path


def get_numeric_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get basic statistics for numeric columns.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        DataFrame with statistics (count, mean, std, min, 25%, 50%, 75%, max)
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        return pd.DataFrame()
    
    return df[numeric_cols].describe()


def get_categorical_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get basic statistics for categorical columns.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        DataFrame with statistics for each categorical column
    """
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    
    if len(categorical_cols) == 0:
        return pd.DataFrame()
    
    cat_stats = []
    for col in categorical_cols:
        col_data = df[col]
        unique_count = col_data.nunique()
        missing_count = col_data.isnull().sum()
        missing_pct = (missing_count / len(df)) * 100
        
        most_frequent = None
        most_frequent_count = 0
        most_frequent_pct = 0.0
        
        if not col_data.empty and col_data.notna().any():
            value_counts = col_data.value_counts()
            if len(value_counts) > 0:
                most_frequent = value_counts.index[0]
                most_frequent_count = value_counts.iloc[0]
                most_frequent_pct = (most_frequent_count / len(df)) * 100
        
        cat_stats.append({
            'Sütun': col,
            'Benzersiz Değer': unique_count,
            'En Sık Görülen': str(most_frequent) if most_frequent is not None else 'N/A',
            'En Sık Görülen Sayısı': most_frequent_count,
            'En Sık Görülen %': f"{most_frequent_pct:.1f}%",
            'Eksik Değer': missing_count,
            'Eksik Değer %': f"{missing_pct:.1f}%"
        })
    
    return pd.DataFrame(cat_stats)


def get_categorical_value_distribution(df: pd.DataFrame, column: str, top_n: int = 10) -> pd.DataFrame:
    """
    Get value distribution for a specific categorical column.
    
    Args:
        df: DataFrame to analyze
        column: Column name
        top_n: Number of top values to return
        
    Returns:
        DataFrame with value, count, and percentage
    """
    if column not in df.columns:
        return pd.DataFrame()
    
    col_data = df[column]
    value_counts = col_data.value_counts()
    value_counts_pct = (col_data.value_counts(normalize=True) * 100).round(2)
    
    result = pd.DataFrame({
        'Değer': value_counts.head(top_n).index,
        'Sayı': value_counts.head(top_n).values,
        'Yüzde (%)': value_counts_pct.head(top_n).values
    })
    
    return result


def get_column_cardinality_info(df: pd.DataFrame, column: str) -> Dict:
    """
    Get cardinality information for a column.
    
    Args:
        df: DataFrame to analyze
        column: Column name
        
    Returns:
        Dictionary with cardinality info and warnings
    """
    if column not in df.columns:
        return {
            'unique_count': 0,
            'total_count': 0,
            'cardinality_ratio': 0.0,
            'is_high_cardinality': False,
            'is_potential_id': False,
            'warning': None
        }
    
    col_data = df[column]
    unique_count = col_data.nunique()
    total_count = len(df)
    cardinality_ratio = unique_count / total_count if total_count > 0 else 0.0
    
    is_high_cardinality = unique_count > 50
    is_potential_id = unique_count == total_count
    
    warning = None
    if is_potential_id:
        warning = f"🔴 Her satır benzersiz! Bu sütun muhtemelen ID sütunu ve model için kullanılmamalı."
    elif is_high_cardinality:
        warning = f"⚠️ Yüksek kardinalite: {unique_count} benzersiz değer. Bu sütun model için karmaşık olabilir."
    
    return {
        'unique_count': unique_count,
        'total_count': total_count,
        'cardinality_ratio': cardinality_ratio,
        'is_high_cardinality': is_high_cardinality,
        'is_potential_id': is_potential_id,
        'warning': warning
    }


def get_data_types_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get summary of data types for all columns.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        DataFrame with column, data type, missing count, and missing percentage
    """
    dtype_df = pd.DataFrame({
        'Sütun': df.columns,
        'Veri Tipi': df.dtypes.astype(str),
        'Eksik Değer Sayısı': df.isnull().sum().values,
        'Eksik Değer Oranı (%)': (df.isnull().sum() / len(df) * 100).values
    })
    
    return dtype_df


def get_data_overview(df: pd.DataFrame) -> Dict:
    """
    Get comprehensive data overview including numeric and categorical statistics.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary with overview statistics
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    
    overview = {
        'shape': {
            'rows': len(df),
            'columns': len(df.columns)
        },
        'numeric_columns': {
            'count': len(numeric_cols),
            'columns': list(numeric_cols)
        },
        'categorical_columns': {
            'count': len(categorical_cols),
            'columns': list(categorical_cols)
        },
        'missing_values': {
            'total': df.isnull().sum().sum(),
            'columns_with_missing': (df.isnull().sum() > 0).sum(),
            'missing_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        }
    }
    
    return overview

