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
        method: Detection method ('iqr')
        
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


def detect_multicollinearity(df: pd.DataFrame, threshold: float = 0.8) -> Dict:
    """
    Detect multicollinearity in numeric columns using correlation.
    
    Args:
        df: DataFrame to analyze
        threshold: Correlation threshold for multicollinearity (default: 0.8)
        
    Returns:
        Dictionary with multicollinearity information
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        return {
            'has_multicollinearity': False,
            'high_correlations': [],
            'threshold': threshold
        }
    
    corr_matrix = df[numeric_cols].corr()
    
    # Find high correlations (excluding diagonal)
    high_correlations = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            corr_value = corr_matrix.iloc[i, j]
            if abs(corr_value) >= threshold:
                high_correlations.append({
                    'column1': corr_matrix.columns[i],
                    'column2': corr_matrix.columns[j],
                    'correlation': corr_value
                })
    
    return {
        'has_multicollinearity': len(high_correlations) > 0,
        'high_correlations': high_correlations,
        'threshold': threshold,
        'total_pairs': len(high_correlations)
    }


def detect_skewness_kurtosis(df: pd.DataFrame, column: str) -> Dict:
    """
    Detect skewness and kurtosis in a numeric column.
    
    Args:
        df: DataFrame to analyze
        column: Column name
        
    Returns:
        Dictionary with skewness and kurtosis information
    """
    if column not in df.columns:
        return {}
    
    col_data = df[column].dropna()
    
    if len(col_data) == 0:
        return {}
    
    skewness = col_data.skew()
    kurtosis = col_data.kurtosis()
    
    # Interpretation
    skewness_interpretation = 'Normal' if abs(skewness) < 0.5 else ('Moderate' if abs(skewness) < 1 else 'High')
    if skewness > 0:
        skewness_direction = 'Right (positive)'
    elif skewness < 0:
        skewness_direction = 'Left (negative)'
    else:
        skewness_direction = 'Symmetric'
    
    kurtosis_interpretation = 'Normal' if abs(kurtosis) < 0.5 else ('Moderate' if abs(kurtosis) < 1 else 'High')
    if kurtosis > 0:
        kurtosis_type = 'Leptokurtic (heavy tails)'
    elif kurtosis < 0:
        kurtosis_type = 'Platykurtic (light tails)'
    else:
        kurtosis_type = 'Mesokurtic (normal)'
    
    return {
        'skewness': skewness,
        'kurtosis': kurtosis,
        'skewness_interpretation': skewness_interpretation,
        'skewness_direction': skewness_direction,
        'kurtosis_interpretation': kurtosis_interpretation,
        'kurtosis_type': kurtosis_type
    }


def calculate_statistical_tests(df: pd.DataFrame, column1: str, column2: Optional[str] = None, test_type: str = 't_test') -> Dict:
    """
    Calculate statistical tests for columns.
    
    Args:
        df: DataFrame to analyze
        column1: First column name
        column2: Second column name (for paired tests)
        test_type: Type of test ('t_test', 'mann_whitney', 'anova', 'chi_square')
        
    Returns:
        Dictionary with test results
    """
    if column1 not in df.columns:
        return {'error': f'Column {column1} not found'}
    
    col1_data = df[column1].dropna()
    
    if len(col1_data) == 0:
        return {'error': f'Column {column1} has no valid data'}
    
    results = {
        'test_type': test_type,
        'column1': column1,
        'column2': column2
    }
    
    if test_type == 't_test':
        # One-sample t-test (test if mean is different from 0)
        if column2 is None:
            stat, p_value = stats.ttest_1samp(col1_data, 0)
            results.update({
                'statistic': stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'interpretation': 'One-sample t-test (mean vs 0)'
            })
        else:
            # Two-sample t-test
            if column2 not in df.columns:
                return {'error': f'Column {column2} not found'}
            col2_data = df[column2].dropna()
            if len(col2_data) == 0:
                return {'error': f'Column {column2} has no valid data'}
            
            stat, p_value = stats.ttest_ind(col1_data, col2_data)
            results.update({
                'statistic': stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'interpretation': f'Two-sample t-test ({column1} vs {column2})'
            })
    
    elif test_type == 'mann_whitney':
        if column2 is None:
            return {'error': 'Mann-Whitney test requires two columns'}
        
        if column2 not in df.columns:
            return {'error': f'Column {column2} not found'}
        col2_data = df[column2].dropna()
        if len(col2_data) == 0:
            return {'error': f'Column {column2} has no valid data'}
        
        stat, p_value = stats.mannwhitneyu(col1_data, col2_data, alternative='two-sided')
        results.update({
            'statistic': stat,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'interpretation': f'Mann-Whitney U test ({column1} vs {column2})'
        })
    
    elif test_type == 'chi_square':
        if column2 is None:
            return {'error': 'Chi-square test requires two categorical columns'}
        
        if column2 not in df.columns:
            return {'error': f'Column {column2} not found'}
        
        # Create contingency table
        contingency = pd.crosstab(df[column1], df[column2])
        if contingency.size == 0:
            return {'error': 'Cannot create contingency table'}
        
        stat, p_value, dof, expected = stats.chi2_contingency(contingency)
        results.update({
            'statistic': stat,
            'p_value': p_value,
            'degrees_of_freedom': dof,
            'significant': p_value < 0.05,
            'interpretation': f'Chi-square test ({column1} vs {column2})'
        })
    
    return results


def analyze_feature_interactions(df: pd.DataFrame, columns: List[str]) -> Dict:
    """
    Analyze feature interactions between columns.
    
    Args:
        df: DataFrame to analyze
        columns: List of column names to analyze
        
    Returns:
        Dictionary with interaction analysis
    """
    if not columns or len(columns) < 2:
        return {}
    
    numeric_cols = [col for col in columns if col in df.columns and df[col].dtype in [np.number]]
    categorical_cols = [col for col in columns if col in df.columns and df[col].dtype in ['object', 'category']]
    
    interactions = {
        'numeric_interactions': [],
        'categorical_interactions': [],
        'mixed_interactions': []
    }
    
    # Numeric-numeric interactions (correlations)
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                interactions['numeric_interactions'].append({
                    'column1': corr_matrix.columns[i],
                    'column2': corr_matrix.columns[j],
                    'correlation': corr_value,
                    'strength': 'Strong' if abs(corr_value) > 0.7 else ('Moderate' if abs(corr_value) > 0.3 else 'Weak')
                })
    
    # Categorical-categorical interactions (chi-square)
    if len(categorical_cols) >= 2:
        for i in range(len(categorical_cols)):
            for j in range(i + 1, len(categorical_cols)):
                try:
                    contingency = pd.crosstab(df[categorical_cols[i]], df[categorical_cols[j]])
                    if contingency.size > 0:
                        stat, p_value, dof, expected = stats.chi2_contingency(contingency)
                        interactions['categorical_interactions'].append({
                            'column1': categorical_cols[i],
                            'column2': categorical_cols[j],
                            'chi_square_statistic': stat,
                            'p_value': p_value,
                            'significant': p_value < 0.05
                        })
                except:
                    pass
    
    # Mixed interactions (numeric vs categorical - group means)
    if len(numeric_cols) > 0 and len(categorical_cols) > 0:
        for num_col in numeric_cols[:3]:  # Limit to first 3 to avoid too many combinations
            for cat_col in categorical_cols[:3]:
                try:
                    group_means = df.groupby(cat_col)[num_col].mean()
                    interactions['mixed_interactions'].append({
                        'numeric_column': num_col,
                        'categorical_column': cat_col,
                        'group_means': group_means.to_dict(),
                        'mean_difference': group_means.max() - group_means.min()
                    })
                except:
                    pass
    
    return interactions


def detect_temporal_patterns(df: pd.DataFrame, date_column: str, value_column: str) -> Dict:
    """
    Detect temporal patterns in time series data.
    
    Args:
        df: DataFrame to analyze
        date_column: Column name containing dates
        value_column: Column name containing values
        
    Returns:
        Dictionary with temporal pattern information
    """
    if date_column not in df.columns or value_column not in df.columns:
        return {'error': 'Required columns not found'}
    
    try:
        # Convert date column to datetime
        df_copy = df.copy()
        df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_column, value_column])
        df_copy = df_copy.sort_values(date_column)
        
        if len(df_copy) == 0:
            return {'error': 'No valid temporal data'}
        
        # Calculate trends
        values = df_copy[value_column].values
        x = np.arange(len(values))
        
        # Linear trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # Detect seasonality (if enough data)
        patterns = {
            'trend': 'Increasing' if slope > 0 else ('Decreasing' if slope < 0 else 'Stable'),
            'slope': slope,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'significant_trend': p_value < 0.05
        }
        
        # Calculate rolling statistics
        if len(values) >= 7:
            rolling_mean = pd.Series(values).rolling(window=min(7, len(values)//10)).mean()
            patterns['rolling_mean'] = rolling_mean.dropna().tolist()
        
        return patterns
        
    except Exception as e:
        return {'error': str(e)}
