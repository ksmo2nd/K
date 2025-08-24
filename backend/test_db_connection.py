#!/usr/bin/env python3
"""
Test script to verify Supabase PostgreSQL connection
Run this after setting up your DATABASE_URL environment variable
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def test_supabase_connection():
    """Test connection to Supabase PostgreSQL database"""
    
    print("🔧 Testing Supabase PostgreSQL Connection")
    print("=" * 50)
    
    try:
        # Import after path setup
        from app.core.database import test_database_connection, get_database_health
        from app.core.config import settings
        
        print(f"📊 Configuration:")
        print(f"   Database URL: {settings.DATABASE_URL[:50]}...")
        print(f"   Supabase URL: {settings.SUPABASE_URL}")
        print()
        
        # Test basic connection
        print("🔌 Testing basic connection...")
        await test_database_connection()
        print("✅ Basic connection successful!")
        print()
        
        # Get detailed health info
        print("📋 Getting database health info...")
        health_info = await get_database_health()
        
        if health_info["status"] == "healthy":
            print("✅ Database health check passed!")
            print(f"   PostgreSQL Version: {health_info['postgres_version']}")
            print(f"   Database: {health_info['database']}")
            print(f"   Connected User: {health_info['user']}")
            print(f"   Server Time: {health_info['server_time']}")
            print(f"   Tables Count: {health_info['tables']}")
            print(f"   Connection Pool Size: {health_info['connection_pool']['size']}")
        else:
            print("❌ Database health check failed!")
            print(f"   Error: {health_info.get('error', 'Unknown error')}")
            return False
            
        print()
        print("🎉 All database tests passed!")
        print("✅ Your FastAPI app can connect to Supabase PostgreSQL!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Check your .env file has correct DATABASE_URL")
        print("   2. Verify Supabase project is running")
        print("   3. Check your database password and host")
        print("   4. Ensure your IP is allowed in Supabase settings")
        return False

async def test_supabase_client():
    """Test Supabase client connection"""
    
    print("\n🔧 Testing Supabase Client")
    print("=" * 30)
    
    try:
        from app.core.database import supabase
        
        # Test a simple query
        response = supabase.table('users').select('id').limit(1).execute()
        print("✅ Supabase client connection successful!")
        print(f"   Response: {len(response.data)} rows returned")
        return True
        
    except Exception as e:
        print(f"❌ Supabase client failed: {e}")
        print()
        print("💡 This might be normal if:")
        print("   - You haven't deployed the database schema yet")
        print("   - The 'users' table doesn't exist")
        print("   - Run: supabase db push  to deploy schema")
        return False

if __name__ == "__main__":
    print("🚀 KSWiFi Database Connection Test")
    print("=" * 60)
    
    # Check if .env file exists
    env_file = Path(backend_dir.parent) / ".env"
    if not env_file.exists():
        print("❌ .env file not found!")
        print("💡 Create .env file from .env.example and add your credentials")
        sys.exit(1)
    
    async def run_tests():
        success = True
        
        # Test PostgreSQL connection
        success &= await test_supabase_connection()
        
        # Test Supabase client
        success &= await test_supabase_client()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Your FastAPI app is ready to use Supabase PostgreSQL!")
        else:
            print("❌ SOME TESTS FAILED!")
            print("🔧 Fix the issues above before running your FastAPI app")
        
        return success
    
    # Run the tests
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)