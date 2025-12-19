"""
FastAPI Backend - DataScience Copilot
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Routers
from .routers import upload, eda, preprocessing, model

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("🚀 FastAPI Backend starting...")
    yield
    logger.info("👋 FastAPI Backend shutting down...")


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

# Include routers
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(eda.router, prefix="/api/eda", tags=["EDA"])
app.include_router(preprocessing.router, prefix="/api/preprocessing", tags=["Preprocessing"])
app.include_router(model.router, prefix="/api/model", tags=["Model"])


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
