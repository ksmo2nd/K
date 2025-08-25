#!/usr/bin/env python3
"""Test backend configuration loading"""

import os
import sys

# Add backend to path
sys.path.insert(0, 'backend')

try:
    # Set minimal required env vars for testing
    os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
    os.environ['SUPABASE_KEY'] = 'test_key'
    os.environ['SUPABASE_ANON_KEY'] = 'test_anon_key'
    os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
    os.environ['SECRET_KEY'] = 'test_secret_key_32_characters_long'
    
    # Test import
    from app.core.config import settings
    
    print("✅ Backend config loads successfully!")
    print(f"📱 App Name: {settings.APP_NAME}")
    print(f"🔢 Version: {settings.APP_VERSION}")
    print(f"🌐 Host: {settings.HOST}:{settings.PORT}")
    print("🔧 Environment variables are properly configured")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("💡 Run: pip install -r backend/requirements.txt")
    
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    print("💡 Check environment variables")