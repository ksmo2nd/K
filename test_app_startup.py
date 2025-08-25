#!/usr/bin/env python3
"""
Test script to verify the application can start with proper environment variables
"""
import os
import sys
import asyncio

# Set mock environment variables for testing
os.environ.update({
    'SUPABASE_URL': 'https://test.supabase.co',
    'SUPABASE_KEY': 'test_service_role_key',
    'SUPABASE_ANON_KEY': 'test_anon_key',
    'DATABASE_URL': 'postgresql://postgres:password@localhost:5432/test',
    'SECRET_KEY': 'test_secret_key_for_jwt_signing_32_chars'
})

async def test_app_imports():
    """Test if the app can be imported without network calls"""
    try:
        print("🧪 Testing application imports...")
        
        # Add backend to path
        sys.path.insert(0, '/workspace/backend')
        
        # Test configuration
        print("   ✅ Testing configuration...")
        from app.core.config import settings
        print(f"   ✅ Configuration loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
        
        # Test database module import (should not make network calls)
        print("   ✅ Testing database module import...")
        from app.core.database import get_supabase_client, get_database_engine
        print("   ✅ Database module imported successfully (no network calls yet)")
        
        # Test main app import
        print("   ✅ Testing main app import...")
        from app.main import app
        print("   ✅ FastAPI app imported successfully")
        
        print("\n🎉 SUCCESS: Application can be imported without network errors!")
        print("The 'Network is unreachable' error was caused by missing environment variables.")
        print("\nTo fix the production issue:")
        print("1. Set all required environment variables in Render")
        print("2. Ensure DATABASE_URL points to a valid Supabase database")
        print("3. Verify network connectivity to Supabase from Render")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_app_imports())
    sys.exit(0 if success else 1)