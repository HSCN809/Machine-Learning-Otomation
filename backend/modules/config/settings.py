"""Configuration settings for the application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables without overriding real runtime env.
load_dotenv()


def _get_int_env(name: str, default: int, *, minimum: int | None = None) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc

    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")

    return value


def _get_float_env(name: str, default: float, *, minimum: float | None = None) -> float:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number.") from exc

    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum:g}.")

    return value


def _get_extensions_env(name: str, default: list[str]) -> list[str]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    extensions = []
    for item in raw_value.split(","):
        extension = item.strip().lower()
        if not extension:
            continue
        if not extension.startswith("."):
            extension = f".{extension}"
        extensions.append(extension)

    if not extensions:
        raise ValueError(f"{name} must include at least one file extension.")

    return extensions


# File upload settings
MAX_FILE_SIZE_MB = _get_int_env('MAX_FILE_SIZE_MB', 200, minimum=1)
SUPPORTED_FORMATS = _get_extensions_env('SUPPORTED_FORMATS', ['.csv', '.xlsx', '.xls'])
UPLOAD_ALLOWED_EXTENSIONS = _get_extensions_env(
    'UPLOAD_ALLOWED_EXTENSIONS',
    ['.csv', '.xlsx', '.xls', '.json'],
)
UPLOAD_CHUNK_SIZE_MB = _get_int_env('UPLOAD_CHUNK_SIZE_MB', 1, minimum=1)

# XLSX safety limits
MAX_XLSX_ZIP_ENTRIES = _get_int_env('MAX_XLSX_ZIP_ENTRIES', 1000, minimum=1)
MAX_XLSX_TOTAL_UNCOMPRESSED_MB = _get_int_env(
    'MAX_XLSX_TOTAL_UNCOMPRESSED_MB',
    300,
    minimum=1,
)
MAX_XLSX_ENTRY_UNCOMPRESSED_MB = _get_int_env(
    'MAX_XLSX_ENTRY_UNCOMPRESSED_MB',
    100,
    minimum=1,
)
MAX_XLSX_COMPRESSION_RATIO = _get_float_env(
    'MAX_XLSX_COMPRESSION_RATIO',
    100,
    minimum=1,
)

# DataFrame and timeline limits.
MAX_DATAFRAME_ROWS = _get_int_env('MAX_DATAFRAME_ROWS', 1_000_000, minimum=1)
MAX_DATAFRAME_COLUMNS = _get_int_env('MAX_DATAFRAME_COLUMNS', 500, minimum=1)
MAX_DATAFRAME_MEMORY_MB = _get_int_env('MAX_DATAFRAME_MEMORY_MB', 512, minimum=1)
MAX_TIMELINE_SNAPSHOTS = _get_int_env('MAX_TIMELINE_SNAPSHOTS', 1, minimum=1)
MAX_TIMELINE_SNAPSHOT_MEMORY_MB = _get_int_env(
    'MAX_TIMELINE_SNAPSHOT_MEMORY_MB',
    256,
    minimum=1,
)

# Temporary directory for uploaded files
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = BASE_DIR / 'backend'
TEMP_DIR = BACKEND_DIR / 'temp'
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Data validation settings
MIN_COLUMNS = 1
MIN_ROWS = 1
HIGH_MISSING_THRESHOLD = 0.5  # 50% or more missing values is considered high

# Logging
LOG_DIR = BACKEND_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# LLM Settings
LLM_ENABLED = os.getenv('LLM_ENABLED', 'true').lower() == 'true'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.7'))
LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '4000'))
LLM_TIMEOUT = int(os.getenv('LLM_TIMEOUT', '30'))  # seconds
LLM_MAX_RETRIES = int(os.getenv('LLM_MAX_RETRIES', '2'))

# Database
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql+psycopg://postgres:postgres@localhost:5432/ml_automation'
)

# Authentication
AUTH_COOKIE_NAME = os.getenv('AUTH_COOKIE_NAME', 'ml_auth_session')
AUTH_COOKIE_SECURE = os.getenv('AUTH_COOKIE_SECURE', 'false').lower() == 'true'
AUTH_COOKIE_SAMESITE = os.getenv('AUTH_COOKIE_SAMESITE', 'lax')
AUTH_COOKIE_DOMAIN = os.getenv('AUTH_COOKIE_DOMAIN') or None
AUTH_SESSION_TTL_MINUTES = int(os.getenv('AUTH_SESSION_TTL_MINUTES', '480'))
AUTH_RATE_LIMIT_ATTEMPTS = int(os.getenv('AUTH_RATE_LIMIT_ATTEMPTS', '5'))
AUTH_RATE_LIMIT_WINDOW_MINUTES = int(os.getenv('AUTH_RATE_LIMIT_WINDOW_MINUTES', '15'))

