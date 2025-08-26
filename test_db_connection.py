#!/usr/bin/env python3
"""
Test Supabase Database Connection
"""

import psycopg2
import urllib.parse

def test_connection_with_url():
    """Test connection using full DATABASE_URL"""
    
    # Your database details
    password = "OLAmilekan@$112"
    # URL encode the password
    encoded_password = urllib.parse.quote_plus(password)
    
    DATABASE_URL = f"postgresql://postgres:{encoded_password}@db.tmxdpjmtjqvizkldvylo.supabase.co:5432/postgres"
    
    print("🔍 Testing Supabase Database Connection...")
    print(f"📡 Host: db.tmxdpjmtjqvizkldvylo.supabase.co")
    print(f"🔑 Password (encoded): {encoded_password}")
    print(f"🌐 Full URL: {DATABASE_URL}")
    print()
    
    try:
        print("🔌 Attempting connection...")
        connection = psycopg2.connect(DATABASE_URL)
        print("✅ Connection successful!")
        
        # Create a cursor to execute SQL queries
        cursor = connection.cursor()
        
        # Test query
        print("📊 Testing query...")
        cursor.execute("SELECT NOW(), version();")
        result = cursor.fetchone()
        print(f"🕐 Current Time: {result[0]}")
        print(f"📋 PostgreSQL Version: {result[1][:50]}...")
        
        # Test if we can create a simple table (to verify permissions)
        print("🔧 Testing table creation permissions...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                test_message TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Insert test data
        cursor.execute("""
            INSERT INTO test_connection (test_message) 
            VALUES ('KSWiFi connection test successful!');
        """)
        
        # Query test data
        cursor.execute("SELECT * FROM test_connection ORDER BY created_at DESC LIMIT 1;")
        test_result = cursor.fetchone()
        print(f"✅ Test record: {test_result}")
        
        # Clean up test table
        cursor.execute("DROP TABLE IF EXISTS test_connection;")
        connection.commit()
        
        # Close connections
        cursor.close()
        connection.close()
        print("✅ Connection closed successfully.")
        print()
        print("🎉 DATABASE CONNECTION TEST PASSED!")
        print("🚀 Your Supabase database is ready for KSWiFi!")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        print()
        
        # Try to diagnose the issue
        if "password authentication failed" in str(e):
            print("🔑 Issue: Password authentication failed")
            print("💡 Solution: Check your database password in Supabase dashboard")
        elif "could not translate host name" in str(e):
            print("🌐 Issue: Host name resolution failed")
            print("💡 Solution: Check your database host URL")
        elif "timeout" in str(e):
            print("⏰ Issue: Connection timeout")
            print("💡 Solution: Check network connectivity and firewall settings")
        else:
            print("🔍 Check your Supabase project settings:")
            print("   1. Go to Supabase Dashboard → Settings → Database")
            print("   2. Verify the connection string")
            print("   3. Check if the database is paused")
        
        return False

def test_connection_with_params():
    """Test connection using individual parameters"""
    print("\n" + "="*50)
    print("🔄 Testing with individual parameters...")
    
    try:
        connection = psycopg2.connect(
            host="db.tmxdpjmtjqvizkldvylo.supabase.co",
            port=5432,
            user="postgres",
            password="OLAmilekan@$112",
            database="postgres"
        )
        print("✅ Parameter-based connection successful!")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Parameter-based connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🗄️  KSWiFi Database Connection Test")
    print("="*50)
    
    # Test with full URL
    url_success = test_connection_with_url()
    
    # Test with parameters
    param_success = test_connection_with_params()
    
    print("\n" + "="*50)
    print("📋 SUMMARY:")
    print(f"   URL Connection: {'✅ PASS' if url_success else '❌ FAIL'}")
    print(f"   Parameter Connection: {'✅ PASS' if param_success else '❌ FAIL'}")
    
    if url_success or param_success:
        print("\n🎯 RESULT: Database connection works!")
        print("🚀 You can now update your Render environment variables.")
    else:
        print("\n🚨 RESULT: Database connection failed!")
        print("🔧 Check your Supabase credentials and try again.")