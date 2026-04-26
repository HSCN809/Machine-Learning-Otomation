"""
FastAPI Backend - DataScience Copilot
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from time import perf_counter

# Routers
from .dependencies import require_authenticated_user
from .routers import auth, upload, eda, preprocessing, model, timeline
from backend.modules.data_upload import models as data_upload_models  # noqa: F401
from backend.modules.model_selection import models as model_selection_models  # noqa: F401
from backend.modules.utils.app_logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("FastAPI backend starting...")
    import os
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # Fail fast on schema drift instead of masking it with stamp/create_all.
    command.upgrade(alembic_cfg, "head")
    logger.info("Alembic migrations applied.")
    yield
    logger.info("FastAPI backend shutting down...")


# Create FastAPI app
app = FastAPI(
    title="DataScience Copilot API",
    description="Machine Learning Automation API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js dev
        "http://127.0.0.1:3000",
        "http://localhost:3001",      # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_http_requests(request, call_next):
    """Log request method, path, status code, and duration."""

    started_at = perf_counter()
    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.exception("%s %s failed in %.1fms", method, path, duration_ms)
        raise

    duration_ms = (perf_counter() - started_at) * 1000
    level = logging.WARNING if response.status_code >= 400 else logging.INFO
    logger.log(level, "%s %s -> %s %.1fms", method, path, response.status_code, duration_ms)
    return response

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(
    upload.router,
    prefix="/api/upload",
    tags=["Upload"],
    dependencies=[Depends(require_authenticated_user)],
)
app.include_router(
    eda.router,
    prefix="/api/eda",
    tags=["EDA"],
    dependencies=[Depends(require_authenticated_user)],
)
app.include_router(
    preprocessing.router,
    prefix="/api/preprocessing",
    tags=["Preprocessing"],
    dependencies=[Depends(require_authenticated_user)],
)
app.include_router(
    model.router,
    prefix="/api/model",
    tags=["Model"],
    dependencies=[Depends(require_authenticated_user)],
)
app.include_router(
    timeline.router,
    prefix="/api/timeline",
    tags=["Timeline"],
    dependencies=[Depends(require_authenticated_user)],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DataScience Copilot API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

