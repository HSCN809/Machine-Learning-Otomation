"""Encoding processor functions."""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict
from sklearn.preprocessing import LabelEncoder
import logging

logger = logging.getLogger(__name__)


def label_encode(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Label encode specified categorical columns.
    
    Label encoding assigns a unique integer to each category.
    Suitable for ordinal data or when categories have a natural order.
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            try:
                # Check if column is categorical
                if not pd.api.types.is_categorical_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                    logger.warning(f"Column {col} is not categorical, skipping label encoding")
                    continue
                
                # Use LabelEncoder
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                logger.info(f"✅ Label encoded column: {col}")
            except Exception as e:
                logger.error(f"Error label encoding {col}: {e}", exc_info=True)
    return df


def one_hot_encode(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """One-hot encode specified categorical columns.
    
    One-hot encoding creates binary columns for each category.
    Suitable for nominal data with low cardinality.
    Warning: High cardinality can create many new columns.
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            try:
                # Check if column is categorical
                if not pd.api.types.is_categorical_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                    logger.warning(f"Column {col} is not categorical, skipping one-hot encoding")
                    continue
                
                # Get unique values count for warning
                unique_count = df[col].nunique()
                if unique_count > 50:
                    logger.warning(f"⚠️ Column {col} has {unique_count} unique values. One-hot encoding will create {unique_count} new columns.")
                
                # Perform one-hot encoding
                dummies = pd.get_dummies(df[col], prefix=col, dtype=int)
                
                # Drop original column and add new columns
                df = df.drop(columns=[col])
                df = pd.concat([df, dummies], axis=1)
                
                logger.info(f"✅ One-hot encoded column: {col} → {unique_count} new columns")
            except Exception as e:
                logger.error(f"Error one-hot encoding {col}: {e}", exc_info=True)
    return df


def ordinal_encode(df: pd.DataFrame, columns: List[str], mapping: Optional[Dict[str, Dict]] = None) -> pd.DataFrame:
    """Ordinal encode specified categorical columns.
    
    Ordinal encoding assigns integers based on a custom mapping or automatic ordering.
    If mapping is provided, uses it. Otherwise, uses alphabetical order.
    
    Args:
        df: DataFrame to encode
        columns: List of column names to encode
        mapping: Optional dict mapping column names to value mappings
                 Example: {'col1': {'low': 0, 'medium': 1, 'high': 2}}
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            try:
                # Check if column is categorical
                if not pd.api.types.is_categorical_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                    logger.warning(f"Column {col} is not categorical, skipping ordinal encoding")
                    continue
                
                # Use provided mapping or create automatic mapping
                if mapping and col in mapping:
                    value_mapping = mapping[col]
                    df[col] = df[col].map(value_mapping)
                    logger.info(f"✅ Ordinal encoded column: {col} (using provided mapping)")
                else:
                    # Automatic mapping: assign integers based on sorted unique values
                    unique_values = sorted(df[col].dropna().unique())
                    value_mapping = {val: idx for idx, val in enumerate(unique_values)}
                    df[col] = df[col].map(value_mapping)
                    logger.info(f"✅ Ordinal encoded column: {col} (automatic mapping: {len(value_mapping)} values)")
            except Exception as e:
                logger.error(f"Error ordinal encoding {col}: {e}", exc_info=True)
    return df


def binary_encode(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Binary encode specified categorical columns.
    
    Binary encoding represents categories as binary digits.
    Suitable for high cardinality categorical data.
    Creates fewer columns than one-hot encoding.
    """
    logger.debug(f"🔍 [BINARY ENCODING] Starting binary encoding for columns: {columns}")
    logger.debug(f"🔍 [BINARY ENCODING] Input DataFrame shape: {df.shape}, columns: {list(df.columns)}")
    
    df = df.copy()
    for col in columns:
        logger.debug(f"🔍 [BINARY ENCODING] Processing column: {col}")
        
        if col not in df.columns:
            logger.warning(f"⚠️ [BINARY ENCODING] Column {col} not found in DataFrame. Available columns: {list(df.columns)}")
            continue
            
        try:
            # Check if column is categorical
            is_categorical = pd.api.types.is_categorical_dtype(df[col])
            is_object = pd.api.types.is_object_dtype(df[col])
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - is_categorical: {is_categorical}, is_object: {is_object}")
            
            if not is_categorical and not is_object:
                logger.warning(f"⚠️ [BINARY ENCODING] Column {col} is not categorical (dtype: {df[col].dtype}), skipping binary encoding")
                continue
            
            # Get column info
            total_rows = len(df)
            null_count = df[col].isna().sum()
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Total rows: {total_rows}, Null count: {null_count}")
            
            # Get unique values and assign integer codes
            unique_values = df[col].dropna().unique()
            unique_count = len(unique_values)
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Unique values count: {unique_count}")
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Unique values (first 10): {list(unique_values[:10])}")
            
            if unique_count == 0:
                logger.warning(f"⚠️ [BINARY ENCODING] Column {col} has no valid values, skipping binary encoding")
                continue
            
            # Create value to code mapping
            value_to_code = {val: idx for idx, val in enumerate(unique_values)}
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Value to code mapping (first 10): {dict(list(value_to_code.items())[:10])}")
            
            # Convert to integer codes (handle NaN values)
            encoded = df[col].map(value_to_code)
            encoded_null_count = encoded.isna().sum()
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Encoded series null count: {encoded_null_count}")
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Encoded values sample (first 10): {encoded.head(10).tolist()}")
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Encoded value range: min={encoded.min()}, max={encoded.max()}")
            
            # Calculate number of bits needed
            max_code = len(unique_values) - 1
            if max_code == 0:
                num_bits = 1
            else:
                num_bits = int(np.ceil(np.log2(max_code + 1)))
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Max code: {max_code}, Required bits: {num_bits}")
            
            # Create binary columns (handle NaN values)
            binary_columns_created = []
            for bit_pos in range(num_bits):
                bit_col_name = f"{col}_bin_{bit_pos}"
                logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Creating bit column {bit_pos}: {bit_col_name}")
                
                # Use fillna to handle NaN values before bit operations
                encoded_filled = encoded.fillna(0).astype(int)
                logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Bit {bit_pos}: encoded_filled sample (first 10): {encoded_filled.head(10).tolist()}")
                logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Bit {bit_pos}: encoded_filled dtype: {encoded_filled.dtype}")
                
                # Perform bit operation using numpy array to avoid Series bitwise issues
                encoded_array = encoded_filled.values  # Convert to numpy array
                binary_array = (encoded_array >> bit_pos) & 1
                binary_values = pd.Series(binary_array, index=df.index, dtype='int64')
                logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Bit {bit_pos}: binary_values sample (first 10): {binary_values.head(10).tolist()}")
                logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Bit {bit_pos}: binary_values unique: {sorted(binary_values.unique())}")
                
                df[bit_col_name] = binary_values
                
                # Restore NaN values in binary columns where original was NaN
                nan_mask = encoded.isna()
                nan_count = nan_mask.sum()
                logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Bit {bit_pos}: Restoring {nan_count} NaN values")
                df.loc[nan_mask, bit_col_name] = np.nan
                
                # Verify the column was created
                if bit_col_name in df.columns:
                    binary_columns_created.append(bit_col_name)
                    final_null_count = df[bit_col_name].isna().sum()
                    final_unique = sorted(df[bit_col_name].dropna().unique())
                    logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Bit {bit_pos}: Final null count: {final_null_count}, Final unique values: {final_unique}")
                else:
                    logger.error(f"❌ [BINARY ENCODING] Column {col} - Bit {bit_pos}: Failed to create column {bit_col_name}")
            
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Created binary columns: {binary_columns_created}")
            
            # Drop original column
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Dropping original column")
            df = df.drop(columns=[col])
            
            # Verify original column is gone and new columns exist
            if col in df.columns:
                logger.error(f"❌ [BINARY ENCODING] Column {col} - Original column still exists after drop!")
            else:
                logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Original column successfully removed")
            
            # Check if binary columns exist
            missing_binary_cols = [bc for bc in binary_columns_created if bc not in df.columns]
            if missing_binary_cols:
                logger.error(f"❌ [BINARY ENCODING] Column {col} - Missing binary columns: {missing_binary_cols}")
            else:
                logger.debug(f"🔍 [BINARY ENCODING] Column {col} - All binary columns exist in DataFrame")
            
            logger.info(f"✅ [BINARY ENCODING] Binary encoded column: {col} → {num_bits} new columns: {binary_columns_created}")
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Final DataFrame shape: {df.shape}, columns: {list(df.columns)}")
            
        except Exception as e:
            logger.error(f"❌ [BINARY ENCODING] Error binary encoding {col}: {e}", exc_info=True)
            logger.debug(f"🔍 [BINARY ENCODING] Column {col} - Exception details: {type(e).__name__}: {str(e)}")
    
    logger.debug(f"🔍 [BINARY ENCODING] Binary encoding completed. Final DataFrame shape: {df.shape}")
    return df


def frequency_encode(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Frequency encode specified categorical columns.
    
    Frequency encoding replaces categories with their frequency counts.
    Preserves original column and adds a new frequency column.
    Useful when frequency is informative for the model.
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            try:
                # Check if column is categorical
                if not pd.api.types.is_categorical_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                    logger.warning(f"Column {col} is not categorical, skipping frequency encoding")
                    continue
                
                # Calculate frequency for each value (exclude NaN)
                frequency_map = df[col].value_counts(dropna=True).to_dict()
                
                if len(frequency_map) == 0:
                    logger.warning(f"Column {col} has no valid values, skipping frequency encoding")
                    continue
                
                # Create new column with frequency values
                freq_col_name = f"{col}_freq"
                # Map frequencies, keeping NaN where original was NaN
                df[freq_col_name] = df[col].map(frequency_map)
                
                # Fill NaN with 0 only for values that exist in frequency map but weren't found
                # Keep original NaN values as NaN (or 0 if you want to count them)
                # For missing values in map, use 0; for original NaN, we can use 0 or keep NaN
                df[freq_col_name] = df[freq_col_name].fillna(0)
                
                logger.info(f"✅ Frequency encoded column: {col} → {freq_col_name} (original column preserved)")
            except Exception as e:
                logger.error(f"Error frequency encoding {col}: {e}", exc_info=True)
    return df

