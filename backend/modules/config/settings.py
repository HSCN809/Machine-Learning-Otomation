"""Configuration settings for the application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (override=True to reload)
load_dotenv(override=True)

# File upload settings
MAX_FILE_SIZE_MB = 200
SUPPORTED_FORMATS = ['.csv', '.xlsx', '.xls']

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
AUTH_SESSION_TTL_MINUTES = int(os.getenv('AUTH_SESSION_TTL_MINUTES', '480'))
AUTH_RATE_LIMIT_ATTEMPTS = int(os.getenv('AUTH_RATE_LIMIT_ATTEMPTS', '5'))
AUTH_RATE_LIMIT_WINDOW_MINUTES = int(os.getenv('AUTH_RATE_LIMIT_WINDOW_MINUTES', '15'))

