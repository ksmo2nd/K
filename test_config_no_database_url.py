#!/usr/bin/env python3
"""
Test that config loads without DATABASE_URL
"""

import os
import sys
from pathlib import Path

# Add app to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

def test_config_without_database_url():
    """Test that config loads successfully without DATABASE_URL"""
    
    print("🔍 Testing config without DATABASE_URL")
    print("="*50)
    
    # Set minimal required environment variables (no DATABASE_URL)
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
    os.environ["SUPABASE_KEY"] = "test-key"
    os.environ["SUPABASE_ANON_KEY"] = "test-anon-key"
    os.environ["SECRET_KEY"] = "test-secret-key-32-characters-long"
    
    # Remove DATABASE_URL if it exists
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    
    try:
        from core.config import settings
        print("✅ Config loaded successfully!")
        print(f"📋 App Name: {settings.APP_NAME}")
        print(f"📋 App Version: {settings.APP_VERSION}")
        print(f"📋 Supabase URL: {settings.SUPABASE_URL}")
        print(f"📋 DATABASE_URL: {settings.DATABASE_URL}")
        
        # Verify DATABASE_URL is None or empty
        if settings.DATABASE_URL is None:
            print("✅ DATABASE_URL is None (correct)")
        elif settings.DATABASE_URL == "":
            print("✅ DATABASE_URL is empty (correct)")
        else:
            print(f"⚠️  DATABASE_URL has value: {settings.DATABASE_URL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        
        if "DATABASE_URL" in str(e) and "required" in str(e):
            print("🚨 DATABASE_URL is still required in config!")
            print("💡 Need to make DATABASE_URL optional in Settings class")
        
        return False

if __name__ == "__main__":
    success = test_config_without_database_url()
    
    print("\n" + "="*50)
    if success:
        print("🎉 SUCCESS: Config works without DATABASE_URL!")
        print("🚀 Ready for Render deployment!")
    else:
        print("❌ FAILED: Config still requires DATABASE_URL")
        print("🔧 Need to fix the Settings class")