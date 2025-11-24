"""Model training module for training machine learning models."""

import logging
import time
import sys

logger = logging.getLogger(__name__)

# Retry mechanism for importing processor
def _import_processor_with_retry(max_retries=5, retry_delay=0.1):
    """
    Import processor module with retry mechanism.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        processor module or None if all retries fail
    """
    processor = None
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            # Clear module cache for retry (except first attempt)
            if attempt > 1:
                module_name = f"{__name__.rsplit('.', 1)[0]}.processor"
                if module_name in sys.modules:
                    del sys.modules[module_name]
                # Also try to clear from parent
                parent_module_name = __name__.rsplit('.', 1)[0]
                if parent_module_name in sys.modules:
                    if hasattr(sys.modules[parent_module_name], 'processor'):
                        delattr(sys.modules[parent_module_name], 'processor')
            
            # Import processor
            from . import processor
            
            # Verify all required functions exist
            required_functions = [
                'train_model',
                'train_multiple_models',
                'split_data'
            ]
            
            missing_functions = []
            for func_name in required_functions:
                if not hasattr(processor, func_name):
                    missing_functions.append(func_name)
            
            if missing_functions:
                raise AttributeError(f"Missing functions in processor: {missing_functions}")
            
            logger.info(f"✅ Processor module imported successfully on attempt {attempt}")
            return processor
            
        except (ImportError, AttributeError) as e:
            last_error = e
            logger.warning(f"⚠️ Processor import attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay * attempt)  # Exponential backoff
            else:
                logger.error(f"❌ All {max_retries} import attempts failed. Last error: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    return None

# Import processor module with retry
processor = _import_processor_with_retry(max_retries=5, retry_delay=0.1)

if processor is not None:
    # Export processor functions directly
    train_model = processor.train_model
    train_multiple_models = processor.train_multiple_models
    split_data = processor.split_data
    logger.info("✅ All processor functions exported successfully")
else:
    # If import failed after all retries, create wrapper functions that retry on call
    logger.error("❌ Processor import failed after all retries. Using lazy import wrappers.")
    
    def _lazy_import_processor():
        """Lazy import processor with retry."""
        processor = _import_processor_with_retry(max_retries=10, retry_delay=0.2)
        if processor is None:
            raise ImportError("Failed to import processor module after all retries")
        return processor
    
    def train_model(*args, **kwargs):
        processor = _lazy_import_processor()
        return processor.train_model(*args, **kwargs)
    
    def train_multiple_models(*args, **kwargs):
        processor = _lazy_import_processor()
        return processor.train_multiple_models(*args, **kwargs)
    
    def split_data(*args, **kwargs):
        processor = _lazy_import_processor()
        return processor.split_data(*args, **kwargs)

# Import analyzer functions
try:
    from .analyzer import (
        analyze_training_data,
        check_data_quality
    )
except ImportError as e:
    logger.warning(f"Failed to import analyzer functions: {e}")
    # Set to None
    analyze_training_data = None
    check_data_quality = None

__all__ = [
    # Processor functions
    'train_model',
    'train_multiple_models',
    'split_data',
    # Analyzer functions
    'analyze_training_data',
    'check_data_quality'
]
