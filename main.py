#!/usr/bin/env python3
"""
KSWiFi Backend Service - Root Entry Point for Render
"""

import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Change to backend directory for relative imports to work
os.chdir(backend_dir)

# Now import and run the backend
if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Print startup info
    print(f"🚀 Starting KSWiFi Backend Service on port {port}")
    print(f"🔧 Python version: {sys.version}")
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"📍 Backend path: {backend_dir}")
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )