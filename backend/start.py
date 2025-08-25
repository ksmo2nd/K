#!/usr/bin/env python3
"""
KSWiFi Backend Service Startup Script for Render
"""

import os
import sys
import uvicorn
from app.main import app

if __name__ == "__main__":
    # Get port from environment (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Print startup info
    print(f"🚀 Starting KSWiFi Backend Service on port {port}")
    print(f"🔧 Python version: {sys.version}")
    print(f"📍 Current directory: {os.getcwd()}")
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )