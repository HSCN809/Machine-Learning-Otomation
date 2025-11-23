"""Feature engineering analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def analyze_duplicate_rows(df: pd.DataFrame) -> Dict:
    """Analyze duplicate rows in the dataset."""
    logger.debug(f"🔍 [FEATURE ENGINEERING ANALYZER] Analyzing duplicate rows")
    
    duplicate_info = {
        'total_duplicates': 0,
        'duplicate_percentage': 0.0,
        'unique_rows': 0,
        'duplicate_groups': []
    }
    
    if len(df) == 0:
        return duplicate_info
    
    # Count duplicates
    duplicated_mask = df.duplicated(keep=False)
    duplicate_count = duplicated_mask.sum()
    duplicate_info['total_duplicates'] = duplicate_count
    duplicate_info['unique_rows'] = len(df) - duplicate_count
    duplicate_info['duplicate_percentage'] = (duplicate_count / len(df)) * 100 if len(df) > 0 else 0
    
    # Get duplicate groups (rows that appear more than once)
    if duplicate_count > 0:
        duplicate_df = df[duplicated_mask]
        # Group by all columns to find duplicate groups
        duplicate_groups = duplicate_df.groupby(list(df.columns)).size().reset_index(name='count')
        duplicate_groups = duplicate_groups[duplicate_groups['count'] > 1]
        duplicate_info['duplicate_groups'] = duplicate_groups.to_dict('records')[:10]  # Limit to first 10
    
    logger.debug(f"🔍 [FEATURE ENGINEERING ANALYZER] Found {duplicate_count} duplicate rows ({duplicate_info['duplicate_percentage']:.2f}%)")
    
    return duplicate_info


def analyze_irrelevant_columns(df: pd.DataFrame, variance_threshold: float = 0.01, unique_ratio_threshold: float = 0.80) -> Dict:
    """Analyze irrelevant columns (constant, low variance, high unique ratio)."""
    logger.debug(f"🔍 [FEATURE ENGINEERING ANALYZER] Analyzing irrelevant columns")
    
    irrelevant_columns = {
        'constant_columns': [],
        'low_variance_columns': [],
        'high_unique_ratio_columns': [],
        'all_irrelevant': []
    }
    
    if len(df.columns) == 0:
        return irrelevant_columns
    
    total_rows = len(df)
    
    # 1. Constant columns (all values are the same)
    for col in df.columns:
        if df[col].nunique() <= 1:
            irrelevant_columns['constant_columns'].append({
                'column': col,
                'reason': 'Sabit değer (tüm değerler aynı)',
                'unique_count': df[col].nunique(),
                'value': df[col].iloc[0] if len(df) > 0 else None
            })
    
    # 2. Low variance columns (for numeric columns only)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in numeric_cols:
        if col not in [c['column'] for c in irrelevant_columns['constant_columns']]:
            variance = df[col].var()
            if pd.notna(variance) and variance < variance_threshold:
                irrelevant_columns['low_variance_columns'].append({
                    'column': col,
                    'reason': f'Düşük varyans (varyans: {variance:.6f})',
                    'variance': variance,
                    'std': df[col].std()
                })
    
    # 3. High unique ratio columns (unique_count / total_rows >= threshold)
    # This catches columns like ID columns where almost every value is unique
    for col in df.columns:
        if col not in [c['column'] for c in irrelevant_columns['constant_columns']]:
            unique_count = df[col].nunique()
            if total_rows > 0:
                unique_ratio = unique_count / total_rows
                if unique_ratio >= unique_ratio_threshold:
                    irrelevant_columns['high_unique_ratio_columns'].append({
                        'column': col,
                        'reason': f'Yüksek benzersizlik oranı (unique/toplam: {unique_ratio:.2%})',
                        'unique_count': unique_count,
                        'total_rows': total_rows,
                        'unique_ratio': unique_ratio
                    })
    
    # Combine all irrelevant columns
    all_irrelevant = []
    all_irrelevant.extend([c['column'] for c in irrelevant_columns['constant_columns']])
    all_irrelevant.extend([c['column'] for c in irrelevant_columns['low_variance_columns']])
    all_irrelevant.extend([c['column'] for c in irrelevant_columns['high_unique_ratio_columns']])
    
    irrelevant_columns['all_irrelevant'] = list(set(all_irrelevant))  # Remove duplicates
    
    logger.debug(f"🔍 [FEATURE ENGINEERING ANALYZER] Found {len(irrelevant_columns['all_irrelevant'])} irrelevant columns")
    
    return irrelevant_columns


def get_feature_engineering_summary(df: pd.DataFrame) -> Dict:
    """Get comprehensive summary for feature engineering step."""
    logger.debug(f"🔍 [FEATURE ENGINEERING ANALYZER] Getting feature engineering summary")
    
    duplicate_info = analyze_duplicate_rows(df)
    irrelevant_info = analyze_irrelevant_columns(df)
    
    summary = {
        'shape': {
            'rows': len(df),
            'columns': len(df.columns)
        },
        'duplicates': duplicate_info,
        'irrelevant_columns': irrelevant_info,
        'data_types': {
            'numeric': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical': df.select_dtypes(include=['object', 'category']).columns.tolist(),
            'datetime': df.select_dtypes(include=['datetime']).columns.tolist()
        }
    }
    
    return summary

