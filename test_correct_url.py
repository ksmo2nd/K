#!/usr/bin/env python3
"""
Test Correct Supabase DATABASE_URL
"""

import psycopg2
import urllib.parse

def test_correct_database_url():
    """Test with the exact DATABASE_URL format"""
    
    # Your exact password
    password = "OLAmilekan@$112"
    
    # URL encode the password for the connection string
    encoded_password = urllib.parse.quote_plus(password)
    
    # Your exact DATABASE_URL format with SSL required
    DATABASE_URL = f"postgresql://postgres:{encoded_password}@db.tmxdpjmtjqvizkldvylo.supabase.co:5432/postgres?sslmode=require"
    
    print("🔍 Testing Correct Supabase DATABASE_URL")
    print("="*60)
    print(f"📡 Host: db.tmxdpjmtjqvizkldvylo.supabase.co")
    print(f"🔑 Password: OLAmilekan@$112")
    print(f"🔒 Password (URL encoded): {encoded_password}")
    print(f"🌐 SSL Mode: require")
    print(f"📋 Full URL: {DATABASE_URL}")
    print()
    
    try:
        print("🔌 Attempting connection with SSL required...")
        connection = psycopg2.connect(DATABASE_URL)
        print("✅ CONNECTION SUCCESSFUL!")
        
        # Test basic operations
        cursor = connection.cursor()
        
        print("📊 Testing basic query...")
        cursor.execute("SELECT NOW(), version();")
        result = cursor.fetchone()
        print(f"🕐 Server Time: {result[0]}")
        print(f"📋 PostgreSQL Version: {result[1][:80]}...")
        
        print("🔧 Testing table operations...")
        # Test table creation (verify permissions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS render_test (
                id SERIAL PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Insert test data
        cursor.execute("""
            INSERT INTO render_test (message) 
            VALUES ('Render deployment test - connection works!');
        """)
        
        # Query the data
        cursor.execute("SELECT * FROM render_test ORDER BY created_at DESC LIMIT 1;")
        test_data = cursor.fetchone()
        print(f"✅ Test Record: ID={test_data[0]}, Message='{test_data[1]}'")
        
        # Clean up
        cursor.execute("DROP TABLE IF EXISTS render_test;")
        connection.commit()
        
        cursor.close()
        connection.close()
        print("✅ Connection closed successfully")
        
        print("\n🎉 DATABASE CONNECTION TEST PASSED!")
        print("🚀 This DATABASE_URL will work in Render!")
        print("\n📋 RENDER ENVIRONMENT VARIABLE:")
        print(f"DATABASE_URL={DATABASE_URL}")
        
        return True
        
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {e}")
        print(f"❌ Error Type: {type(e).__name__}")
        
        # Detailed error analysis
        error_str = str(e).lower()
        if "password authentication failed" in error_str:
            print("\n🔑 ISSUE: Password authentication failed")
            print("💡 SOLUTION: Check password in Supabase dashboard")
        elif "ssl" in error_str:
            print("\n🔒 ISSUE: SSL connection problem")
            print("💡 SOLUTION: Verify SSL settings in Supabase")
        elif "timeout" in error_str or "network" in error_str:
            print("\n🌐 ISSUE: Network connectivity problem")
            print("💡 NOTE: This might work in Render's environment")
        elif "host" in error_str or "name" in error_str:
            print("\n📡 ISSUE: Host name resolution failed")
            print("💡 SOLUTION: Verify the database host URL")
        else:
            print(f"\n🔍 UNKNOWN ISSUE: {e}")
            
        return False

if __name__ == "__main__":
    success = test_correct_database_url()
    
    print("\n" + "="*60)
    if success:
        print("🎯 RESULT: Ready for Render deployment!")
        print("📝 Next steps:")
        print("   1. Add psycopg2-binary to requirements.txt ✅ (Done)")
        print("   2. Set DATABASE_URL in Render environment variables")
        print("   3. Deploy and test")
    else:
        print("⚠️  RESULT: Connection failed locally")
        print("📝 Next steps:")
        print("   1. Update Render environment variable anyway")
        print("   2. Test in Render environment (might work there)")
        print("   3. Check Supabase project status")