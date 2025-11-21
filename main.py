"""
Main entry point for the Machine Learning Automation application.
This file redirects to frontend/app.py to maintain proper project structure.

To run the application, use one of these commands:
- streamlit run frontend/app.py
- python main.py
- run.bat (Windows) or ./run.sh (Linux/Mac)
"""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    # Get the frontend app file
    frontend_dir = Path(__file__).parent / "frontend"
    app_file = frontend_dir / "app.py"
    
    if not app_file.exists():
        print(f"Error: {app_file} not found!")
        sys.exit(1)
    
    # Run streamlit from the frontend directory
    # This ensures that Streamlit finds the pages/ folder correctly
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        str(app_file)
    ])

