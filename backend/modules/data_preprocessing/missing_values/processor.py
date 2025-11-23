"""Missing values handling processor functions."""

import pandas as pd
import numpy as np
from typing import List
from sklearn.impute import KNNImputer
import logging

logger = logging.getLogger(__name__)


def fill_missing_values_mean(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Fill missing values with mean for specified columns."""
    df = df.copy()
    for col in columns:
        if col in df.columns:
            try:
                # Check current dtype
                current_dtype = df[col].dtype
                logger.debug(f"Column {col} dtype: {current_dtype}")
                
                # Convert to numeric if needed
                if not pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    logger.debug(f"Column {col} converted to: {df[col].dtype}")
                
                # Check if numeric
                if pd.api.types.is_numeric_dtype(df[col]):
                    # Calculate mean (pandas automatically excludes NaN)
                    mean_val = df[col].mean()
                    missing_count_before = df[col].isnull().sum()
                    logger.debug(f"Column {col} mean: {mean_val}, missing count: {missing_count_before}")
                    
                    if pd.notna(mean_val):
                        # Fill missing values
                        df[col] = df[col].fillna(mean_val)
                        missing_count_after = df[col].isnull().sum()
                        filled_count = missing_count_before - missing_count_after
                        logger.debug(f"Column {col}: Filled {filled_count} values")
                    else:
                        logger.warning(f"Column {col}: Mean is NaN, cannot fill")
                else:
                    logger.warning(f"Column {col}: Not numeric after conversion. dtype: {df[col].dtype}")
            except Exception as e:
                logger.error(f"Error filling {col} with mean: {e}", exc_info=True)
    return df


def fill_missing_values_median(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Fill missing values with median for specified columns."""
    df = df.copy()
    for col in columns:
        if col in df.columns:
            try:
                # Check current dtype
                current_dtype = df[col].dtype
                logger.debug(f"Column {col} dtype: {current_dtype}")
                
                # Convert to numeric if needed
                if not pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    logger.debug(f"Column {col} converted to: {df[col].dtype}")
                
                # Check if numeric
                if pd.api.types.is_numeric_dtype(df[col]):
                    # Calculate median (pandas automatically excludes NaN)
                    median_val = df[col].median()
                    missing_count_before = df[col].isnull().sum()
                    logger.debug(f"Column {col} median: {median_val}, missing count: {missing_count_before}")
                    
                    if pd.notna(median_val):
                        # Fill missing values
                        df[col] = df[col].fillna(median_val)
                        missing_count_after = df[col].isnull().sum()
                        filled_count = missing_count_before - missing_count_after
                        logger.debug(f"Column {col}: Filled {filled_count} values")
                    else:
                        logger.warning(f"Column {col}: Median is NaN, cannot fill")
                else:
                    logger.warning(f"Column {col}: Not numeric after conversion. dtype: {df[col].dtype}")
            except Exception as e:
                logger.error(f"Error filling {col} with median: {e}", exc_info=True)
    return df


def fill_missing_values_mode(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Fill missing values with mode for specified columns."""
    df = df.copy()
    for col in columns:
        if col in df.columns:
            try:
                mode_values = df[col].mode()
                if len(mode_values) > 0:
                    mode_value = mode_values.iloc[0]  # Get first mode value
                    df[col] = df[col].fillna(mode_value)
                else:
                    logger.warning(f"Column {col} has no mode value")
            except Exception as e:
                logger.error(f"Error filling {col} with mode: {e}")
    return df


def fill_missing_values_forward_fill(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Fill missing values using forward fill method (ileri doldurma).
    
    Forward fill propagates the previous non-null value forward (downward) to fill missing values.
    Example: [1, NaN, NaN, 4] -> [1, 1, 1, 4]
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            try:
                # Use ffill() method instead of deprecated fillna(method='ffill')
                df[col] = df[col].ffill()
            except Exception as e:
                logger.error(f"Error forward filling {col}: {e}")
    return df


def fill_missing_values_backward_fill(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Fill missing values using backward fill method (geri doldurma).
    
    Backward fill propagates the next non-null value backward (upward) to fill missing values.
    Example: [1, NaN, NaN, 4] -> [1, 4, 4, 4]
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            try:
                # Use bfill() method instead of deprecated fillna(method='bfill')
                df[col] = df[col].bfill()
            except Exception as e:
                logger.error(f"Error backward filling {col}: {e}")
    return df


def fill_missing_values_interpolation(df: pd.DataFrame, columns: List[str], method: str = 'linear') -> pd.DataFrame:
    """Fill missing values using interpolation."""
    df = df.copy()
    for col in columns:
        if col in df.columns:
            try:
                # Check current dtype
                current_dtype = df[col].dtype
                logger.debug(f"Column {col} dtype: {current_dtype}")
                
                # Convert to numeric if needed
                if not pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    logger.debug(f"Column {col} converted to: {df[col].dtype}")
                
                # Check if numeric
                if pd.api.types.is_numeric_dtype(df[col]):
                    missing_count_before = df[col].isnull().sum()
                    logger.debug(f"Column {col} missing count before: {missing_count_before}")
                    
                    # Use linear as default
                    interp_method = 'linear'
                    if method in ['polynomial', 'spline']:
                        interp_method = method
                    
                    try:
                        if interp_method == 'linear':
                            df[col] = df[col].interpolate(method='linear', limit_direction='both')
                        elif interp_method == 'polynomial':
                            df[col] = df[col].interpolate(method='polynomial', order=2, limit_direction='both')
                        elif interp_method == 'spline':
                            df[col] = df[col].interpolate(method='spline', order=2, limit_direction='both')
                        
                        missing_count_after = df[col].isnull().sum()
                        filled_count = missing_count_before - missing_count_after
                        logger.debug(f"Column {col}: Interpolated {filled_count} values using {interp_method}")
                    except Exception as interp_error:
                        # Fallback to linear if method fails
                        logger.warning(f"Column {col}: {interp_method} interpolation failed, trying linear: {interp_error}")
                        df[col] = df[col].interpolate(method='linear', limit_direction='both')
                        missing_count_after = df[col].isnull().sum()
                        filled_count = missing_count_before - missing_count_after
                        logger.debug(f"Column {col}: Interpolated {filled_count} values using linear (fallback)")
                else:
                    logger.warning(f"Column {col}: Not numeric after conversion. dtype: {df[col].dtype}")
            except Exception as e:
                logger.error(f"Error interpolating {col}: {e}", exc_info=True)
    return df


def fill_missing_values_knn(df: pd.DataFrame, columns: List[str], n_neighbors: int = 5) -> pd.DataFrame:
    """Fill missing values using KNN imputation.
    
    KNN imputation requires multiple numeric columns to work effectively.
    This function uses all numeric columns in the dataset for imputation,
    but only fills missing values in the specified columns.
    """
    logger.info(f"🔍 KNN Imputation started for columns: {columns}")
    logger.debug(f"📊 Input DataFrame shape: {df.shape}, n_neighbors: {n_neighbors}")
    
    df = df.copy()
    
    # Get all numeric columns in the dataset (for KNN to work, we need multiple columns)
    all_numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    logger.debug(f"📈 Found {len(all_numeric_cols)} numeric columns: {all_numeric_cols}")
    
    # Convert target columns to numeric and check validity
    target_cols = []
    for col in columns:
        if col not in df.columns:
            logger.warning(f"⚠️ Column {col} not found in DataFrame")
            continue
            
        try:
            logger.debug(f"🔧 Processing column {col}: dtype={df[col].dtype}, missing={df[col].isnull().sum()}")
            
            # Convert to numeric if needed
            if not pd.api.types.is_numeric_dtype(df[col]):
                logger.debug(f"🔄 Converting column {col} to numeric")
                df[col] = pd.to_numeric(df[col], errors='coerce')
                logger.debug(f"✅ Column {col} converted to: {df[col].dtype}")
            
            # Check if numeric after conversion
            if pd.api.types.is_numeric_dtype(df[col]):
                # Add to all_numeric_cols if not already there
                if col not in all_numeric_cols:
                    all_numeric_cols.append(col)
                    logger.debug(f"➕ Added {col} to all_numeric_cols")
                target_cols.append(col)
                logger.debug(f"✅ Column {col} added to target_cols")
            else:
                logger.warning(f"⚠️ Column {col} is not numeric after conversion: {df[col].dtype}")
        except Exception as e:
            logger.error(f"❌ Column {col}: Could not convert to numeric: {e}", exc_info=True)
    
    logger.info(f"🎯 Target columns after processing: {target_cols}")
    
    if not target_cols:
        logger.warning("❌ No valid target columns for KNN imputation")
        return df
    
    # KNN needs at least 2 columns to work (one to predict, one as feature)
    if len(all_numeric_cols) < 2:
        logger.warning(f"⚠️ KNN imputation requires at least 2 numeric columns, found {len(all_numeric_cols)}")
        logger.info("🔄 Falling back to mean imputation for KNN target columns")
        return fill_missing_values_mean(df, target_cols)
    
    # Filter all_numeric_cols to only include columns with at least some non-null values
    valid_numeric_cols = []
    for col in all_numeric_cols:
        non_null_count = df[col].notna().sum()
        missing_count = df[col].isnull().sum()
        logger.debug(f"📊 Column {col}: non_null={non_null_count}, missing={missing_count}")
        if non_null_count > 0:
            valid_numeric_cols.append(col)
    
    logger.info(f"✅ Valid numeric columns (with non-null values): {valid_numeric_cols} ({len(valid_numeric_cols)} columns)")
    
    if len(valid_numeric_cols) < 2:
        logger.warning(f"⚠️ KNN imputation requires at least 2 numeric columns with non-null values, found {len(valid_numeric_cols)}")
        logger.info("🔄 Falling back to mean imputation for KNN target columns")
        return fill_missing_values_mean(df, target_cols)
    
    # Adjust n_neighbors if needed (can't be more than available samples)
    min_non_null = min(df[col].notna().sum() for col in valid_numeric_cols)
    actual_n_neighbors = min(n_neighbors, min_non_null - 1)  # -1 because we need at least one neighbor
    
    logger.debug(f"🔢 n_neighbors calculation: requested={n_neighbors}, min_non_null={min_non_null}, actual={actual_n_neighbors}")
    
    if actual_n_neighbors < 1:
        logger.warning(f"⚠️ Not enough non-null values for KNN (need at least {n_neighbors + 1}, found {min_non_null})")
        logger.info("🔄 Falling back to mean imputation for KNN target columns")
        return fill_missing_values_mean(df, target_cols)
    
    # Check KNNImputer signature BEFORE try block (so we can use it in exception handling)
    import inspect
    knn_sig = inspect.signature(KNNImputer.__init__)
    knn_params = list(knn_sig.parameters.keys())
    logger.info(f"📋 KNNImputer.__init__ signature: {knn_sig}")
    logger.info(f"📋 Supported parameters: {knn_params}")
    logger.info(f"📋 Parameters we're using: n_neighbors={actual_n_neighbors}")
    
    try:
        logger.info(f"🚀 Starting KNN imputation with {len(valid_numeric_cols)} columns, n_neighbors={actual_n_neighbors}")
        
        # Store original values for non-target columns (to preserve their missing values)
        original_df = df.copy()
        logger.debug("💾 Stored original DataFrame for non-target columns")
        
        # Prepare data for KNN imputation
        data_for_imputation = df[valid_numeric_cols].copy()
        logger.debug(f"📦 Data shape for imputation: {data_for_imputation.shape}")
        logger.debug(f"📊 Missing values per column before imputation:")
        for col in valid_numeric_cols:
            missing = data_for_imputation[col].isnull().sum()
            logger.debug(f"   - {col}: {missing} missing")
        
        # Apply KNN imputation on all valid numeric columns
        # IMPORTANT: KNNImputer does NOT support random_state parameter
        logger.debug(f"🔧 Creating KNNImputer with n_neighbors={actual_n_neighbors}")
        logger.debug(f"⚠️ Note: KNNImputer does NOT support random_state parameter")
        
        # Create imputer WITHOUT random_state (it doesn't support it)
        imputer = KNNImputer(n_neighbors=actual_n_neighbors)
        logger.debug("✅ KNNImputer created successfully")
        
        logger.info("🔄 Fitting and transforming data with KNN imputation...")
        imputed_data = imputer.fit_transform(data_for_imputation)
        logger.info("✅ KNN imputation completed")
        
        # Convert back to DataFrame preserving column names and index
        df_imputed = pd.DataFrame(imputed_data, columns=valid_numeric_cols, index=df.index)
        logger.debug(f"📦 Imputed DataFrame shape: {df_imputed.shape}")
        
        # Check missing values after imputation
        logger.debug(f"📊 Missing values per column after imputation:")
        for col in valid_numeric_cols:
            missing = df_imputed[col].isnull().sum()
            logger.debug(f"   - {col}: {missing} missing")
        
        # Update ONLY the target columns in the original dataframe
        total_filled = 0
        for col in target_cols:
            if col in df_imputed.columns:
                # Only update missing values in target columns
                missing_mask = df[col].isnull()
                missing_count_before = missing_mask.sum()
                
                if missing_count_before > 0:
                    df.loc[missing_mask, col] = df_imputed.loc[missing_mask, col]
                    missing_count_after = df[col].isnull().sum()
                    filled_count = missing_count_before - missing_count_after
                    total_filled += filled_count
                    logger.info(f"✅ Column {col}: filled {filled_count} missing values (before: {missing_count_before}, after: {missing_count_after})")
                else:
                    logger.debug(f"ℹ️ Column {col}: no missing values to fill")
        
        logger.info(f"🎉 Total filled: {total_filled} missing values across {len(target_cols)} target columns")
        
        # Restore original values for non-target columns (preserve their missing values)
        restored_count = 0
        for col in valid_numeric_cols:
            if col not in target_cols:
                df[col] = original_df[col]
                restored_count += 1
        logger.debug(f"🔄 Restored {restored_count} non-target columns to original values")
        
    except TypeError as e:
        logger.error(f"❌ TypeError in KNN imputation: {e}")
        logger.error(f"📋 KNNImputer signature: {knn_sig}")
        logger.error(f"📋 Supported parameters: {knn_params}")
        logger.error(f"📋 Parameters we tried to use: n_neighbors={actual_n_neighbors}")
        if 'random_state' in str(e):
            logger.error(f"❌ KNNImputer does NOT support random_state parameter. Error: {e}")
            logger.info("🔄 Retrying without random_state parameter...")
            # This should not happen since we're not using random_state, but just in case
            try:
                imputer = KNNImputer(n_neighbors=actual_n_neighbors)
                imputed_data = imputer.fit_transform(df[valid_numeric_cols])
                df_imputed = pd.DataFrame(imputed_data, columns=valid_numeric_cols, index=df.index)
                for col in target_cols:
                    if col in df_imputed.columns:
                        missing_mask = df[col].isnull()
                        df.loc[missing_mask, col] = df_imputed.loc[missing_mask, col]
                for col in valid_numeric_cols:
                    if col not in target_cols:
                        df[col] = original_df[col]
                logger.info("✅ KNN imputation completed after retry")
            except Exception as retry_e:
                logger.error(f"❌ Retry also failed: {retry_e}", exc_info=True)
                logger.info("🔄 Falling back to mean imputation")
                return fill_missing_values_mean(df, target_cols)
        else:
            logger.error(f"❌ TypeError details: {type(e).__name__}: {e}", exc_info=True)
            logger.info("🔄 Falling back to mean imputation")
            return fill_missing_values_mean(df, target_cols)
    except Exception as e:
        logger.error(f"❌ Error in KNN imputation: {e}", exc_info=True)
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(f"❌ Error args: {e.args}")
        logger.info("🔄 Falling back to mean imputation due to KNN error")
        return fill_missing_values_mean(df, target_cols)
    
    logger.info(f"✅ KNN imputation completed successfully for columns: {target_cols}")
    return df


def fill_missing_values_drop(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Drop columns with missing values."""
    df = df.copy()
    if columns:
        # Drop specified columns
        df = df.drop(columns=columns, errors='ignore')
    else:
        # Backward compatibility: drop rows if no columns specified
        df = df.dropna()
    return df

