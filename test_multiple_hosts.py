#!/usr/bin/env python3
"""
Test Multiple Supabase Host URLs
"""

import psycopg2
import urllib.parse

def test_host(host):
    """Test a specific host"""
    password = "OLAmilekan@$112"
    encoded_password = urllib.parse.quote_plus(password)
    
    print(f"\n🔍 Testing host: {host}")
    
    try:
        connection = psycopg2.connect(
            host=host,
            port=5432,
            user="postgres",
            password=password,
            database="postgres",
            sslmode="require",
            connect_timeout=10
        )
        print(f"✅ SUCCESS: {host} works!")
        
        cursor = connection.cursor()
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print(f"🕐 Current Time: {result[0]}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {host} - {str(e)[:100]}...")
        return False

if __name__ == "__main__":
    print("🔍 Testing Multiple Supabase Host URLs")
    print("="*50)
    
    # Test various possible host patterns
    hosts_to_test = [
        "db.tmxdpjm.supabase.co",
        "db.tmxdpjmtjqvizkldvylo.supabase.co", 
        "aws-0-us-east-1.pooler.supabase.com",
        "aws-0-us-west-1.pooler.supabase.com",
        "aws-0-eu-west-1.pooler.supabase.com",
        "tmxdpjm.supabase.co",
        "tmxdpjmtjqvizkldvylo.supabase.co"
    ]
    
    working_hosts = []
    
    for host in hosts_to_test:
        if test_host(host):
            working_hosts.append(host)
    
    print("\n" + "="*50)
    print("📋 RESULTS:")
    if working_hosts:
        print("✅ Working hosts found:")
        for host in working_hosts:
            encoded_password = urllib.parse.quote_plus("OLAmilekan@$112")
            print(f"   🎯 postgresql://postgres:{encoded_password}@{host}:5432/postgres?sslmode=require")
    else:
        print("❌ No working hosts found!")
        print("💡 Please check your Supabase project settings:")
        print("   1. Go to Supabase Dashboard → Settings → Database")
        print("   2. Copy the exact connection string")
        print("   3. Make sure the project is not paused")