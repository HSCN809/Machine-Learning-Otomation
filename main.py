"""
Main entry point for the Machine Learning Automation application.
Starts both FastAPI backend and Next.js frontend.

Usage:
    python main.py           # Start both backend and frontend
    python main.py --backend # Start only backend
    python main.py --frontend # Start only frontend
"""

import subprocess
import sys
import os
import time
from pathlib import Path

from backend.modules.utils.app_logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def start_backend(port: int = 8000, reload: bool = True):
    """Start FastAPI backend server"""
    logger.info("Starting FastAPI backend on port %s", port)
    
    # Change to project root for proper imports
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Add project root to path
    sys.path.insert(0, str(project_root))
    
    try:
        import uvicorn
        uvicorn.run(
            "backend.api.main:app",
            host="0.0.0.0",
            port=port,
            reload=reload,
            log_level="info"
        )
    except ImportError:
        logger.error("uvicorn is not installed. Run: pip install uvicorn")
        sys.exit(1)


def start_frontend():
    """Start Next.js frontend dev server"""
    logger.info("Starting Next.js frontend on port 3000")
    
    frontend_dir = Path(__file__).parent / "frontend-next"
    
    if not frontend_dir.exists():
        logger.error("Frontend directory not found: %s", frontend_dir)
        return
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        logger.info("Installing npm dependencies")
        subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True)
    
    # Start Next.js dev server
    subprocess.run(["npm", "run", "dev"], cwd=frontend_dir, shell=True)


def start_backend_process(port: int = 8000):
    """Start backend as a separate process"""
    project_root = Path(__file__).parent
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api.main:app", 
         "--host", "0.0.0.0", "--port", str(port)],
        cwd=project_root
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    
    if "--backend" in args:
        # Backend only (with reload)
        start_backend(reload=True)
    elif "--frontend" in args:
        # Frontend only
        start_frontend()
    else:
        # Start both backend and frontend
        logger.info("DataScience Copilot starting")
        logger.info("Backend:  http://localhost:8000")
        logger.info("Frontend: http://localhost:3000")
        logger.info("API Docs: http://localhost:8000/docs")
        
        # Start backend as separate process
        start_backend_process()
        
        # Wait a bit for backend to start
        time.sleep(2)
        
        # Start frontend in main thread
        start_frontend()




