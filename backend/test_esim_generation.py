#!/usr/bin/env python3
"""
Test eSIM Generation - Diagnose Issues
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_esim_generation():
    """Test eSIM generation step by step"""
    
    print("🔍 Testing eSIM Generation...")
    
    try:
        # Test 1: Import services
        print("\n1️⃣ Testing imports...")
        from app.services.esim_service import ESIMService
        from app.core.database import get_supabase_client
        print("✅ Imports successful")
        
        # Test 2: Create service
        print("\n2️⃣ Creating eSIM service...")
        esim_service = ESIMService()
        print(f"✅ Service created, using KSWiFi inbuilt eSIM generation")
        
        # Test 3: Test database connection
        print("\n3️⃣ Testing database connection...")
        try:
            # Try to query esims table
            response = get_supabase_client().table('esims').select('count').execute()
            print(f"✅ esims table exists, count: {len(response.data) if response.data else 0}")
        except Exception as db_error:
            print(f"❌ Database/Table error: {db_error}")
            print("💡 The 'esims' table might not exist in Supabase")
        
        # Test 4: Try eSIM generation
        print("\n4️⃣ Testing eSIM generation...")
        test_user_id = "test-user-123"
        test_bundle_size = 1024  # 1GB
        
        try:
            result = await esim_service.provision_esim(test_user_id, test_bundle_size)
            print(f"✅ eSIM generation successful!")
            print(f"📱 eSIM ID: {result.get('esim_id')}")
            print(f"📶 ICCID: {result.get('iccid')}")
            print(f"🔑 Activation Code: {result.get('activation_code')[:50]}...")
        except Exception as gen_error:
            print(f"❌ eSIM generation failed: {gen_error}")
            print(f"❌ Error type: {type(gen_error).__name__}")
            
            # Check if it's a database table issue
            if "relation" in str(gen_error) or "table" in str(gen_error):
                print("\n🚨 DATABASE ISSUE DETECTED:")
                print("The 'esims' table doesn't exist in your Supabase database!")
                print("\n🔧 SOLUTION:")
                print("1. Go to Supabase Dashboard → SQL Editor")
                print("2. Run this SQL to create the table:")
                print("""
CREATE TABLE esims (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    iccid TEXT UNIQUE NOT NULL,
    imsi TEXT,
    msisdn TEXT,
    activation_code TEXT NOT NULL,
    qr_code_data TEXT,
    status TEXT DEFAULT 'pending',
    apn TEXT DEFAULT 'kswifi.internet',
    username TEXT,
    password TEXT,
    bundle_size_mb INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    activated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_esims_user_id ON esims(user_id);
CREATE INDEX idx_esims_status ON esims(status);
                """)
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        print(f"❌ Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_esim_generation())