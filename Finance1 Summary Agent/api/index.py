"""
Vercel entry point for FastAPI application.
This file imports the FastAPI app from server/main.py and exposes it for Vercel deployment.
"""
import sys
import os
from pathlib import Path

# Add the project root and server directory to Python path
# This allows imports from server/ modules to work correctly
project_root = Path(__file__).parent.parent
server_dir = project_root / "server"

# Add both to sys.path if not already present
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

# Change to server directory for relative imports to work
original_cwd = os.getcwd()
try:
    os.chdir(str(server_dir))
    
    # Import the FastAPI app from server/main.py
    # This import must happen after changing directory for relative imports to work
    from main import app
    
finally:
    # Restore original working directory
    os.chdir(original_cwd)

# Export the app for Vercel
# Vercel will automatically detect and use this FastAPI app instance
__all__ = ["app"]
