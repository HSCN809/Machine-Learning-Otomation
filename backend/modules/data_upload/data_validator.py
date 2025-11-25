"""Data validation module for checking data quality and detecting issues."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import streamlit as st

from backend.modules.config.settings import (
    MAX_FILE_SIZE_MB,
    SUPPORTED_FORMATS,
    MIN_COLUMNS,
    MIN_ROWS,
    HIGH_MISSING_THRESHOLD
)


def validate_file_format(file, allowed_formats: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate file format. Sadece CSV, XLSX ve XLS dosyalarına izin verilir.
    
    Args:
        file: File object (Streamlit UploadedFile or file path)
        allowed_formats: List of allowed formats. If None, uses SUPPORTED_FORMATS from config.
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if allowed_formats is None:
        allowed_formats = SUPPORTED_FORMATS
    
    # Get file extension
    if hasattr(file, 'name'):
        file_name = file.name
    else:
        file_name = str(file)
    
    file_extension = Path(file_name).suffix.lower()
    
    # Sıkı format kontrolü - sadece izin verilen formatlar
    if file_extension not in allowed_formats:
        allowed_formats_display = ', '.join([f.upper().replace('.', '') for f in allowed_formats])
        return False, f"Desteklenmeyen dosya formatı: {file_extension.upper()}. Sadece {allowed_formats_display} dosyaları yüklenebilir."
    
    return True, None


def validate_file_size(file, max_size_mb: Optional[float] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate file size.
    
    Args:
        file: File object (Streamlit UploadedFile or file path)
        max_size_mb: Maximum file size in MB. If None, uses MAX_FILE_SIZE_MB from config.
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if max_size_mb is None:
        max_size_mb = MAX_FILE_SIZE_MB
    
    # Get file size
    if hasattr(file, 'size'):
        size_bytes = file.size
    else:
        import os
        if os.path.exists(file):
            size_bytes = os.path.getsize(file)
        else:
            return False, "Dosya bulunamadı"
    
    size_mb = size_bytes / (1024 * 1024)
    
    if size_mb > max_size_mb:
        return False, f"Dosya boyutu çok büyük: {size_mb:.2f} MB. Maksimum boyut: {max_size_mb} MB"
    
    return True, None


def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """
    Perform basic DataFrame validation.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if df is None:
        return False, "DataFrame None değeri"
    
    if df.empty:
        return False, "DataFrame boş. Lütfen veri içeren bir dosya yükleyin."
    
    if len(df.columns) < MIN_COLUMNS:
        return False, f"DataFrame'de yeterli sütun yok. Minimum: {MIN_COLUMNS}, Mevcut: {len(df.columns)}"
    
    if len(df) < MIN_ROWS:
        return False, f"DataFrame'de yeterli satır yok. Minimum: {MIN_ROWS}, Mevcut: {len(df)}"
    
    return True, None


def detect_data_issues(df: pd.DataFrame) -> List[Dict]:
    """
    Detect data quality issues in the DataFrame.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        List of issue dictionaries with keys: type, severity, column, description, suggestion
    """
    issues = []
    
    # Check for high missing values
    missing_ratios = df.isnull().sum() / len(df)
    high_missing_cols = missing_ratios[missing_ratios >= HIGH_MISSING_THRESHOLD]
    
    for col in high_missing_cols.index:
        missing_pct = missing_ratios[col] * 100
        issues.append({
            'type': 'high_missing_values',
            'severity': 'uyarı' if missing_pct < 80 else 'kritik',
            'column': col,
            'description': f"'{col}' sütununda %{missing_pct:.1f} eksik değer var.",
            'suggestion': ''  # Öneriler sadece LLM ile oluşturulacak
        })
    
    # Check for duplicate rows
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        duplicate_pct = (duplicate_count / len(df)) * 100
        severity = 'bilgi' if duplicate_pct < 5 else 'uyarı'
        issues.append({
            'type': 'duplicate_rows',
            'severity': severity,
            'column': None,
            'description': f"{duplicate_count} adet tekrar eden satır bulundu (%{duplicate_pct:.1f}).",
            'suggestion': ''  # Öneriler sadece LLM ile oluşturulacak
        })
    
    # Check for columns with single unique value (constant columns)
    for col in df.columns:
        # NaN olmayan değerleri kontrol et
        non_null_values = df[col].dropna()
        if len(non_null_values) == 0:
            continue  # Tüm değerler NaN ise atla
        
        unique_count = non_null_values.nunique()
        missing_ratio = df[col].isnull().sum() / len(df)
        
        # Sadece sütunun çoğu doluysa VE tüm değerler aynıysa uyarı ver
        if unique_count == 1 and missing_ratio < 0.5:
            issues.append({
                'type': 'constant_column',
                'severity': 'uyarı',
                'column': col,
                'description': f"'{col}' sütunu sabit değer içeriyor (tüm değerler aynı).",
                'suggestion': ''  # Öneriler sadece LLM ile oluşturulacak
            })
    
    # Check for potential data type issues
    for col in df.select_dtypes(include=['object']).columns:
        # Try to detect numeric columns stored as strings
        try:
            pd.to_numeric(df[col].dropna().head(100))
            issues.append({
                'type': 'wrong_data_type',
                'severity': 'bilgi',
                'column': col,
                'description': f"'{col}' sütunu sayısal değerler içeriyor ancak metin (object) tipinde.",
                'suggestion': ''  # Öneriler sadece LLM ile oluşturulacak
            })
        except:
            pass
    
    # Check for potential outliers in numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            outliers = ((df[col] < (Q1 - 3 * IQR)) | (df[col] > (Q3 + 3 * IQR))).sum()
            if outliers > 0:
                outlier_pct = (outliers / len(df)) * 100
                if outlier_pct > 5:
                    issues.append({
                        'type': 'potential_outliers',
                        'severity': 'bilgi',
                        'column': col,
                        'description': f"'{col}' sütununda potansiyel aykırı değerler (outlier) bulundu (%{outlier_pct:.1f}).",
                        'suggestion': ''  # Öneriler sadece LLM ile oluşturulacak
                    })
    
    return issues


def get_validation_report(df: pd.DataFrame) -> Dict:
    """
    Generate comprehensive validation report with LLM-enhanced suggestions.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Dictionary containing validation report with summary and LLM-enhanced issues
    """
    issues = detect_data_issues(df)
    
    # Categorize issues by severity
    critical_issues = [i for i in issues if i['severity'] == 'kritik']
    warning_issues = [i for i in issues if i['severity'] == 'uyarı']
    info_issues = [i for i in issues if i['severity'] == 'bilgi']
    
    report = {
        'summary': {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'total_issues': len(issues),
            'critical_count': len(critical_issues),
            'warning_count': len(warning_issues),
            'info_count': len(info_issues)
        },
        'issues': issues,
        'issues_by_severity': {
            'kritik': critical_issues,
            'uyarı': warning_issues,
            'bilgi': info_issues
        }
    }
    
    # Always enhance with LLM - öneriler sadece LLM ile oluşturulur
    try:
        from backend.modules.data_upload.llm_enhancer import enhance_validation_report_with_llm
        
        data_summary = get_data_summary(df)
        report = enhance_validation_report_with_llm(report, data_summary, df)
    except Exception as e:
        # LLM enhancement başarısız olursa detaylı hata logla
        import logging
        logger = logging.getLogger(__name__)
        error_msg = str(e)
        logger.error(f"LLM enhancement failed: {error_msg}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full error: {repr(e)}")
        # Report'u LLM olmadan döndür (öneriler boş olacak)
        # Exception'ı re-raise et ki frontend'de görünsün
        raise Exception(f"LLM önerisi oluşturulamadı: {error_msg}")
    
    return report


def get_data_summary(df: pd.DataFrame) -> Dict:
    """
    Get quick data summary for preview.
    
    Args:
        df: DataFrame to summarize
        
    Returns:
        Dictionary with basic statistics
    """
    summary = {
        'shape': {
            'rows': len(df),
            'columns': len(df.columns)
        },
        'missing_values': {
            'total': df.isnull().sum().sum(),
            'columns_with_missing': (df.isnull().sum() > 0).sum(),
            'missing_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        },
        'data_types': df.dtypes.value_counts().to_dict(),
        'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
        'categorical_columns': len(df.select_dtypes(include=['object']).columns),
        'duplicate_rows': df.duplicated().sum()
    }
    
    return summary

