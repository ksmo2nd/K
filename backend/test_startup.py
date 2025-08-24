#!/usr/bin/env python3
"""
Test script to check if the backend can start without external dependencies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        from app.core.config import settings
        print("✅ Config imported successfully")
        print(f"   App Name: {settings.APP_NAME}")
        print(f"   Version: {settings.APP_VERSION}")
        print(f"   Supabase URL: {settings.SUPABASE_URL or 'Not set'}")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from app.core.database import init_connections, init_session_factory
        print("✅ Database module imported successfully")
        
        # Test connection initialization
        init_connections()
        init_session_factory()
        print("✅ Database initialization completed (with fallbacks)")
    except Exception as e:
        print(f"❌ Database module failed: {e}")
        return False
    
    try:
        from app.services.session_service import SessionService
        session_service = SessionService()
        print("✅ Session service imported successfully")
    except Exception as e:
        print(f"❌ Session service import failed: {e}")
        return False
    
    try:
        from app.services.esim_service import ESIMService
        esim_service = ESIMService()
        print("✅ eSIM service imported successfully")
    except Exception as e:
        print(f"❌ eSIM service import failed: {e}")
        return False
    
    try:
        from app.main import app
        print("✅ FastAPI app imported successfully")
    except Exception as e:
        print(f"❌ FastAPI app import failed: {e}")
        return False
    
    return True

def test_session_service():
    """Test session service functionality"""
    print("\nTesting session service...")
    
    try:
        from app.services.session_service import SessionService
        service = SessionService()
        
        # Test getting available sessions
        import asyncio
        sessions = asyncio.run(service.get_available_sessions())
        print(f"✅ Available sessions: {len(sessions)} found")
        
        for session in sessions[:2]:  # Show first 2
            print(f"   - {session['name']}: {session['size']} ({'FREE' if session['is_free'] else 'Paid'})")
        
    except Exception as e:
        print(f"❌ Session service test failed: {e}")
        return False
    
    return True

def test_esim_service():
    """Test eSIM service with mock data"""
    print("\nTesting eSIM service...")
    
    try:
        from app.services.esim_service import ESIMService
        service = ESIMService()
        
        # Test mock provisioning
        import asyncio
        result = asyncio.run(service.provision_esim("test-user", 1024))
        print(f"✅ eSIM provisioning works (mock mode)")
        print(f"   ICCID: {result.get('iccid', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")
        
    except Exception as e:
        print(f"❌ eSIM service test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 KSWiFi Backend Startup Test")
    print("=" * 40)
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_session_service() 
    all_passed &= test_esim_service()
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Backend is ready to start (with mock data)")
        print("\n💡 To use real services, set these environment variables:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_KEY") 
        print("   - SUPABASE_ANON_KEY")
        print("   - DATABASE_URL")
        print("   - ESIM_PROVIDER_API_KEY")
        print("   - ESIM_PROVIDER_API_URL")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Check the errors above and fix the issues.")
    
    sys.exit(0 if all_passed else 1)