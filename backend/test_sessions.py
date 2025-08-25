#!/usr/bin/env python3
"""
Test Sessions API - Diagnose Issues
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_sessions():
    """Test sessions functionality"""
    
    print("🔍 Testing Sessions...")
    
    try:
        # Test 1: Import services
        print("\n1️⃣ Testing imports...")
        from app.services.session_service import SessionService
        from app.core.database import supabase_client
        print("✅ Imports successful")
        
        # Test 2: Create service
        print("\n2️⃣ Creating session service...")
        session_service = SessionService()
        print("✅ Service created")
        
        # Test 3: Test available sessions
        print("\n3️⃣ Testing available sessions...")
        try:
            sessions = await session_service.get_available_sessions()
            print(f"✅ Available sessions: {len(sessions)}")
            
            # Show first few sessions
            for i, session in enumerate(sessions[:5]):
                print(f"  📦 {session['name']}: {session['data_mb']}MB - ₦{session['price_ngn']}")
                
        except Exception as sessions_error:
            print(f"❌ Sessions error: {sessions_error}")
        
        # Test 4: Test database tables
        print("\n4️⃣ Testing database tables...")
        
        # Check internet_sessions table
        try:
            response = supabase_client.client.table('internet_sessions').select('count').execute()
            print(f"✅ internet_sessions table exists")
        except Exception as db_error:
            print(f"❌ internet_sessions table missing: {db_error}")
            print("\n🚨 DATABASE ISSUE:")
            print("The 'internet_sessions' table doesn't exist!")
            print("\n🔧 SOLUTION - Run this SQL in Supabase:")
            print("""
CREATE TABLE internet_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    session_name TEXT NOT NULL,
    data_mb INTEGER NOT NULL,
    price_ngn INTEGER DEFAULT 0,
    validity_days INTEGER,
    plan_type TEXT DEFAULT 'standard',
    status TEXT DEFAULT 'downloading',
    download_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    progress_percent INTEGER DEFAULT 0,
    esim_id UUID,
    data_used_mb INTEGER DEFAULT 0,
    data_remaining_mb INTEGER,
    expires_at TIMESTAMP WITH TIME ZONE,
    download_completed_at TIMESTAMP WITH TIME ZONE,
    activated_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

CREATE INDEX idx_sessions_user_id ON internet_sessions(user_id);
CREATE INDEX idx_sessions_status ON internet_sessions(status);
            """)
        
        # Check user_subscriptions table
        try:
            response = supabase_client.client.table('user_subscriptions').select('count').execute()
            print(f"✅ user_subscriptions table exists")
        except Exception as db_error:
            print(f"❌ user_subscriptions table missing: {db_error}")
            print("\n🔧 SOLUTION - Run this SQL in Supabase:")
            print("""
CREATE TABLE user_subscriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    price_ngn INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON user_subscriptions(status);
            """)
        
    except Exception as e:
        print(f"❌ Critical error: {e}")

if __name__ == "__main__":
    asyncio.run(test_sessions())