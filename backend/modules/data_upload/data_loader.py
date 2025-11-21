"""Data loading module for CSV and Excel files."""

import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Union
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_csv(file_path: Union[str, Path], **kwargs) -> Optional[pd.DataFrame]:
    """
    Load CSV file into pandas DataFrame.
    
    Args:
        file_path: Path to CSV file
        **kwargs: Additional arguments to pass to pd.read_csv
        
    Returns:
        pd.DataFrame or None if error
    """
    try:
        # Default encoding and separator options
        default_kwargs = {
            'encoding': 'utf-8',
            'low_memory': False
        }
        default_kwargs.update(kwargs)
        
        df = pd.read_csv(file_path, **default_kwargs)
        logger.info(f"CSV dosyası başarıyla yüklendi: {file_path}")
        return df
    except UnicodeDecodeError:
        try:
            # Try with different encoding
            df = pd.read_csv(file_path, encoding='latin-1', **kwargs)
            logger.info(f"CSV dosyası latin-1 encoding ile yüklendi: {file_path}")
            return df
        except Exception as e:
            logger.error(f"CSV yükleme hatası: {str(e)}")
            st.error(f"CSV dosyası okunamadı: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"CSV yükleme hatası: {str(e)}")
        st.error(f"CSV dosyası okunamadı: {str(e)}")
        return None


def load_excel(file_path: Union[str, Path], **kwargs) -> Optional[pd.DataFrame]:
    """
    Load Excel file into pandas DataFrame.
    
    Args:
        file_path: Path to Excel file
        **kwargs: Additional arguments to pass to pd.read_excel
        
    Returns:
        pd.DataFrame or None if error
    """
    try:
        # Default options
        default_kwargs = {
            'engine': 'openpyxl'
        }
        default_kwargs.update(kwargs)
        
        df = pd.read_excel(file_path, **default_kwargs)
        logger.info(f"Excel dosyası başarıyla yüklendi: {file_path}")
        return df
    except Exception as e:
        logger.error(f"Excel yükleme hatası: {str(e)}")
        st.error(f"Excel dosyası okunamadı: {str(e)}")
        return None


def load_data(file_path: Union[str, Path], file_format: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Load data file (CSV or Excel) based on file extension or format.
    
    Args:
        file_path: Path to data file
        file_format: Optional format hint ('csv' or 'excel'). If None, auto-detect from extension.
        
    Returns:
        pd.DataFrame or None if error
    """
    file_path = Path(file_path)
    
    # Auto-detect format if not provided
    if file_format is None:
        extension = file_path.suffix.lower()
        if extension == '.csv':
            file_format = 'csv'
        elif extension in ['.xlsx', '.xls']:
            file_format = 'excel'
        else:
            st.error(f"Desteklenmeyen dosya formatı: {extension}")
            logger.error(f"Desteklenmeyen format: {extension}")
            return None
    
    # Load based on format
    if file_format.lower() == 'csv':
        return load_csv(file_path)
    elif file_format.lower() in ['excel', 'xlsx', 'xls']:
        return load_excel(file_path)
    else:
        st.error(f"Desteklenmeyen format: {file_format}")
        logger.error(f"Desteklenmeyen format: {file_format}")
        return None

