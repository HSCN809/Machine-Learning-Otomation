"""File handling utilities for uploaded files."""

import os
import tempfile
import logging
from pathlib import Path
from typing import Optional

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from backend.modules.config.settings import TEMP_DIR

logger = logging.getLogger(__name__)


def save_uploaded_file(uploaded_file) -> Optional[str]:
    """
    Save uploaded file to temporary directory.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        str: Path to saved file, or None if error
    """
    try:
        # Create temp directory if it doesn't exist
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(uploaded_file.name).suffix
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension,
            dir=TEMP_DIR
        )
        
        # Write file content
        temp_file.write(uploaded_file.getvalue())
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        if STREAMLIT_AVAILABLE:
            st.error(f"Dosya kaydedilirken hata oluştu: {str(e)}")
        else:
            logger.error("Dosya kaydedilirken hata oluştu: %s", e)
        return None


def cleanup_temp_files(file_path: Optional[str] = None):
    """
    Clean up temporary files.
    
    Args:
        file_path: Specific file to delete, or None to clean all temp files
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        elif file_path is None:
            # Clean all temp files older than 1 hour
            import time
            current_time = time.time()
            for file in TEMP_DIR.glob('*'):
                if os.path.isfile(file):
                    file_time = os.path.getmtime(file)
                    if current_time - file_time > 3600:  # 1 hour
                        os.remove(file)
    except Exception as e:
        logger.debug("Temp file cleanup failed: %s", e, exc_info=True)


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        float: File size in MB
    """
    if not os.path.exists(file_path):
        return 0.0
    
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)

