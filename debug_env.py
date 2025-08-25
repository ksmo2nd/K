#!/usr/bin/env python3
"""
Debug script to check environment variables and identify deployment issues
"""
import os
import sys

def check_environment():
    print("🔍 KSWiFi Backend Environment Validation")
    print("=" * 50)
    
    # Required environment variables
    required_vars = {
        'SUPABASE_URL': 'Supabase project URL (https://your-project.supabase.co)',
        'SUPABASE_KEY': 'Supabase service role key (from Settings → API)',
        'SUPABASE_ANON_KEY': 'Supabase anon key (from Settings → API)', 
        'DATABASE_URL': 'PostgreSQL connection string (from Supabase Settings → Database)',
        'SECRET_KEY': 'JWT secret key (generate with: openssl rand -hex 32)'
    }
    
    # Optional environment variables
    optional_vars = {
        'HOST': '0.0.0.0 (default)',
        'PORT': '8000 (default)', 
        'LOG_LEVEL': 'INFO (default)',
        'REDIS_URL': 'redis://localhost:6379 (default)',
        'ALLOWED_ORIGINS': '["https://your-frontend.vercel.app"] (default has localhost)'
    }
    
    print("\n📋 REQUIRED VARIABLES:")
    missing_required = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Show first 20 chars for security
            display_value = value[:20] + "..." if len(value) > 20 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            print(f"   Description: {description}")
            missing_required.append(var)
    
    print(f"\n📋 OPTIONAL VARIABLES:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            display_value = value[:30] + "..." if len(value) > 30 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"⚪ {var}: Using default - {description}")
    
    # Test configuration loading
    print(f"\n🧪 TESTING CONFIGURATION:")
    try:
        sys.path.insert(0, '/workspace/backend')
        from app.core.config import Settings
        settings = Settings()
        print("✅ Configuration loads successfully!")
        
        # Test Supabase connection
        print(f"\n🔗 TESTING SUPABASE CONNECTION:")
        try:
            from app.core.database import supabase_client
            # Simple test - try to access the client
            print("✅ Supabase client initialized")
        except Exception as e:
            print(f"❌ Supabase connection error: {e}")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        if missing_required:
            print(f"\n💡 SOLUTION: Set these {len(missing_required)} required variables in Render:")
            for var in missing_required:
                print(f"   {var}")
    
    print(f"\n" + "=" * 50)
    if missing_required:
        print(f"❌ RESULT: {len(missing_required)} required variables missing")
        return False
    else:
        print("✅ RESULT: All required variables set!")
        return True

if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)