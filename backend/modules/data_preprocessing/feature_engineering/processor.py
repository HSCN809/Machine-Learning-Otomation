"""Feature engineering processor functions."""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict
import logging
from typing import Literal


logger = logging.getLogger(__name__)


def remove_duplicate_rows(df: pd.DataFrame, keep: str = 'first') -> pd.DataFrame:
    """Remove duplicate rows from DataFrame.
    
    Args:
        df: DataFrame to process
        keep: Which duplicates to keep ('first', 'last', or False to remove all)
    
    Returns:
        DataFrame with duplicates removed
    """
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Removing duplicate rows (keep={keep})")
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] DataFrame shape before: {df.shape}")
    
    df = df.copy()
    rows_before = len(df)
    
    if keep == False:
        # Remove all duplicates (keep only unique rows)
        df = df.drop_duplicates(keep=False)
    else:
        # Keep first or last occurrence
        df = df.drop_duplicates(keep=keep)
    
    rows_after = len(df)
    removed_count = rows_before - rows_after
    
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Removed {removed_count} duplicate rows")
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] DataFrame shape after: {df.shape}")
    logger.info(f"✅ Removed {removed_count} duplicate row(s) (kept {keep})")
    
    return df


def drop_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Drop specified columns from DataFrame.
    
    Args:
        df: DataFrame to process
        columns: List of column names to drop
    
    Returns:
        DataFrame with columns removed
    """
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Dropping columns: {columns}")
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] DataFrame shape before: {df.shape}")
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] DataFrame columns before: {list(df.columns)}")
    
    df = df.copy()
    
    # Filter to only columns that exist
    existing_columns = [col for col in columns if col in df.columns]
    missing_columns = [col for col in columns if col not in df.columns]
    
    if missing_columns:
        logger.warning(f"⚠️ [FEATURE ENGINEERING PROCESSOR] Columns not found: {missing_columns}")
    
    if existing_columns:
        df = df.drop(columns=existing_columns)
        logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Dropped {len(existing_columns)} column(s): {existing_columns}")
        logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] DataFrame shape after: {df.shape}")
        logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] DataFrame columns after: {list(df.columns)}")
        logger.info(f"✅ Dropped {len(existing_columns)} column(s): {', '.join(existing_columns)}")
    else:
        logger.warning(f"⚠️ [FEATURE ENGINEERING PROCESSOR] No valid columns to drop")
    
    return df


def create_numeric_feature(df: pd.DataFrame, operation: str, columns: List[str], new_column_name: str) -> pd.DataFrame:
    """Create new numeric feature from existing numeric columns.
    
    Args:
        df: DataFrame to process
        operation: Operation type ('add', 'subtract', 'multiply', 'divide')
        columns: List of column names to use (must be numeric)
        new_column_name: Name for the new column
    
    Returns:
        DataFrame with new column added
    """
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Creating numeric feature: {new_column_name}")
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Operation: {operation}, Columns: {columns}")
    
    df = df.copy()
    
    # Validate columns exist and are numeric
    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Columns not found: {missing_cols}")
        return df
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric_cols = [col for col in columns if col not in numeric_cols]
    if non_numeric_cols:
        logger.warning(f"⚠️ [FEATURE ENGINEERING PROCESSOR] Non-numeric columns: {non_numeric_cols}")
        return df
    
    if len(columns) < 2:
        logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Need at least 2 columns for numeric operation")
        return df
    
    try:
        if operation == 'add':
            df[new_column_name] = df[columns].sum(axis=1)
        elif operation == 'subtract':
            if len(columns) == 2:
                df[new_column_name] = df[columns[0]] - df[columns[1]]
            else:
                logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Subtract operation requires exactly 2 columns")
                return df
        elif operation == 'multiply':
            df[new_column_name] = df[columns].prod(axis=1)
        elif operation == 'divide':
            if len(columns) == 2:
                # Avoid division by zero
                df[new_column_name] = df[columns[0]] / df[columns[1]].replace(0, np.nan)
            else:
                logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Divide operation requires exactly 2 columns")
                return df
        else:
            logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Unknown operation: {operation}")
            return df
        
        logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Created column: {new_column_name}")
        logger.info(f"✅ Created numeric feature '{new_column_name}' using {operation} operation on {len(columns)} column(s)")
    except Exception as e:
        logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Error creating numeric feature: {e}", exc_info=True)
    
    return df


def create_datetime_feature(df: pd.DataFrame, column: str, feature_type: str, new_column_name: str) -> pd.DataFrame:
    """Extract datetime features from a datetime column.
    
    Args:
        df: DataFrame to process
        column: Name of datetime column
        feature_type: Type of feature to extract ('year', 'month', 'day', 'weekday', 'hour', 'minute', 'second')
        new_column_name: Name for the new column
    
    Returns:
        DataFrame with new column added
    """
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Creating datetime feature: {new_column_name}")
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Column: {column}, Feature type: {feature_type}")
    
    df = df.copy()
    
    # Validate column exists
    if column not in df.columns:
        logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Column not found: {column}")
        return df
    
    # Convert to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(df[column]):
        try:
            df[column] = pd.to_datetime(df[column], errors='coerce')
        except Exception as e:
            logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Cannot convert column to datetime: {e}")
            return df
    
    try:
        if feature_type == 'year':
            df[new_column_name] = df[column].dt.year
        elif feature_type == 'month':
            df[new_column_name] = df[column].dt.month
        elif feature_type == 'day':
            df[new_column_name] = df[column].dt.day
        elif feature_type == 'weekday':
            df[new_column_name] = df[column].dt.weekday
        elif feature_type == 'hour':
            df[new_column_name] = df[column].dt.hour
        elif feature_type == 'minute':
            df[new_column_name] = df[column].dt.minute
        elif feature_type == 'second':
            df[new_column_name] = df[column].dt.second
        else:
            logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Unknown feature type: {feature_type}")
            return df
        
        logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Created datetime feature: {new_column_name}")
        logger.info(f"✅ Created datetime feature '{new_column_name}' ({feature_type}) from column '{column}'")
    except Exception as e:
        logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Error creating datetime feature: {e}", exc_info=True)
    
    return df


def create_categorical_combination(df: pd.DataFrame, columns: List[str], new_column_name: str, separator: str = '_') -> pd.DataFrame:
    """Combine categorical columns into a new column.
    
    Args:
        df: DataFrame to process
        columns: List of categorical column names to combine
        new_column_name: Name for the new column
        separator: Separator to use when combining values
    
    Returns:
        DataFrame with new column added
    """
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Creating categorical combination: {new_column_name}")
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Columns: {columns}, Separator: {separator}")
    
    df = df.copy()
    
    # Validate columns exist
    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Columns not found: {missing_cols}")
        return df
    
    try:
        # Convert all columns to string and combine
        df[new_column_name] = df[columns].astype(str).agg(separator.join, axis=1)
        
        logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Created categorical combination: {new_column_name}")
        logger.info(f"✅ Created categorical combination '{new_column_name}' from {len(columns)} column(s)")
    except Exception as e:
        logger.error(f"❌ [FEATURE ENGINEERING PROCESSOR] Error creating categorical combination: {e}", exc_info=True)
    
    return df


def create_binned_feature(
    df: pd.DataFrame,
    column: str,
    new_column_name: str,
    strategy: Literal['equal_width', 'quantile'] = 'equal_width',
    bin_count: int = 5,
) -> pd.DataFrame:
    """Create a categorical binning feature from a numeric column."""
    df = df.copy()

    if column not in df.columns:
        logger.error("Column not found: %s", column)
        return df

    if not np.issubdtype(df[column].dtype, np.number):
        logger.error("Column is not numeric: %s", column)
        return df

    valid_bin_count = max(2, int(bin_count))

    try:
        if strategy == 'quantile':
            df[new_column_name] = pd.qcut(df[column], q=valid_bin_count, duplicates='drop')
        elif strategy == 'equal_width':
            df[new_column_name] = pd.cut(df[column], bins=valid_bin_count)
        else:
            logger.error("Unknown binning strategy: %s", strategy)
            return df

        df[new_column_name] = df[new_column_name].astype(str)
    except Exception as e:
        logger.error("Error creating binned feature: %s", e, exc_info=True)

    return df


def apply_feature_engineering_method(df: pd.DataFrame, method: str, **kwargs) -> pd.DataFrame:
    """Apply feature engineering method based on method name.
    
    Args:
        df: DataFrame to process
        method: Method name ('remove_duplicates', 'drop_column', 'create_numeric_feature', 'create_datetime_feature', 'create_categorical_combination')
        **kwargs: Additional arguments for the method
    
    Returns:
        Processed DataFrame
    """
    logger.debug(f"🔍 [FEATURE ENGINEERING PROCESSOR] Applying method: {method}")
    
    if method == 'remove_duplicates':
        keep = kwargs.get('keep', 'first')
        return remove_duplicate_rows(df, keep=keep)
    elif method == 'drop_column':
        columns = kwargs.get('columns', [])
        return drop_columns(df, columns)
    elif method == 'create_numeric_feature':
        operation = kwargs.get('operation', 'add')
        columns = kwargs.get('columns', [])
        new_column_name = kwargs.get('new_column_name', '')
        return create_numeric_feature(df, operation, columns, new_column_name)
    elif method == 'create_datetime_feature':
        column = kwargs.get('column', '')
        feature_type = kwargs.get('feature_type', 'year')
        new_column_name = kwargs.get('new_column_name', '')
        return create_datetime_feature(df, column, feature_type, new_column_name)
    elif method == 'create_categorical_combination':
        columns = kwargs.get('columns', [])
        new_column_name = kwargs.get('new_column_name', '')
        separator = kwargs.get('separator', '_')
        return create_categorical_combination(df, columns, new_column_name, separator)
    else:
        logger.warning(f"⚠️ [FEATURE ENGINEERING PROCESSOR] Unknown method: {method}")
        return df

