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
import signal
import time
from pathlib import Path


def start_backend(port: int = 8000, reload: bool = True):
    """Start FastAPI backend server"""
    print("🚀 Starting FastAPI Backend on port", port)
    
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
        print("❌ uvicorn not installed. Run: pip install uvicorn")
        sys.exit(1)


def start_frontend():
    """Start Next.js frontend dev server"""
    print("🌐 Starting Next.js Frontend on port 3000")
    
    frontend_dir = Path(__file__).parent / "frontend-next"
    
    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        return None
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing npm dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True)
    
    # Start Next.js dev server as subprocess
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )
    return process


def start_backend_process(port: int = 8000):
    """Start backend as a separate process"""
    project_root = Path(__file__).parent
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api.main:app", 
         "--host", "0.0.0.0", "--port", str(port), "--reload"],
        cwd=project_root,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )
    return process


if __name__ == "__main__":
    args = sys.argv[1:]
    
    if "--backend" in args:
        # Backend only (with reload)
        start_backend(reload=True)
    elif "--frontend" in args:
        # Frontend only
        frontend_proc = start_frontend()
        if frontend_proc:
            try:
                frontend_proc.wait()
            except KeyboardInterrupt:
                frontend_proc.terminate()
    else:
        # Start both backend and frontend
        print("=" * 50)
        print("🤖 DataScience Copilot - Starting Application")
        print("=" * 50)
        print()
        print("📌 Backend:  http://localhost:8000")
        print("📌 Frontend: http://localhost:3000")
        print("📌 API Docs: http://localhost:8000/docs")
        print()
        print("Press Ctrl+C to stop both servers")
        print("=" * 50)
        
        # Start both as separate processes
        backend_proc = start_backend_process()
        time.sleep(2)
        frontend_proc = start_frontend()
        
        # Wait for both processes
        try:
            while True:
                # Check if processes are still running
                backend_alive = backend_proc.poll() is None
                frontend_alive = frontend_proc and frontend_proc.poll() is None
                
                if not backend_alive and not frontend_alive:
                    print("\n⚠️ Both processes stopped")
                    break
                
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping servers...")
            
            # Terminate processes
            if backend_proc.poll() is None:
                if os.name == 'nt':
                    backend_proc.terminate()
                else:
                    backend_proc.send_signal(signal.SIGINT)
            
            if frontend_proc and frontend_proc.poll() is None:
                if os.name == 'nt':
                    frontend_proc.terminate()
                else:
                    frontend_proc.send_signal(signal.SIGINT)
            
            # Wait for graceful shutdown
            time.sleep(2)
            
            # Force kill if still running
            if backend_proc.poll() is None:
                backend_proc.kill()
            if frontend_proc and frontend_proc.poll() is None:
                frontend_proc.kill()
            
            print("✅ Servers stopped")

