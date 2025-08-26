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

# Print debug info
print(f"🔧 Python version: {sys.version}")
print(f"📍 Current directory: {os.getcwd()}")
print(f"📍 Backend path: {backend_dir}")
print(f"📍 Backend exists: {backend_dir.exists()}")

# Check if app/main.py exists
app_main = backend_dir / "app" / "main.py"
print(f"📍 App main.py path: {app_main}")
print(f"📍 App main.py exists: {app_main.exists()}")

# List backend directory contents
if backend_dir.exists():
    print(f"📁 Backend directory contents: {list(backend_dir.iterdir())}")
    app_dir = backend_dir / "app"
    if app_dir.exists():
        print(f"📁 App directory contents: {list(app_dir.iterdir())}")

# Change to backend directory for relative imports to work
os.chdir(backend_dir)
print(f"📍 Changed working directory to: {os.getcwd()}")

# Now import and run the backend
if __name__ == "__main__":
    try:
        from app.main import app
        print("✅ Successfully imported app from backend")
        
        import uvicorn
        
        # Get port from environment (Render sets this)
        port = int(os.environ.get("PORT", 8000))
        
        print(f"🚀 Starting KSWiFi Backend Service on port {port}")
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)