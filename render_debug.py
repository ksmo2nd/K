#!/usr/bin/env python3
"""
Debug script specifically for Render deployment issues
Run this in your Render deployment to diagnose problems
"""
import os
import sys
import socket
from urllib.parse import urlparse

def check_render_environment():
    print("🚀 Render Deployment Debug")
    print("=" * 60)
    
    # Check if we're running on Render
    render_service = os.getenv('RENDER_SERVICE_NAME', 'Unknown')
    render_region = os.getenv('RENDER_REGION', 'Unknown')
    
    print(f"🏢 Render Service: {render_service}")
    print(f"🌍 Render Region: {render_region}")
    print(f"🐍 Python Version: {sys.version}")
    print()
    
    # Check all environment variables
    print("📋 ALL ENVIRONMENT VARIABLES:")
    env_vars = dict(os.environ)
    
    # Filter out sensitive system variables
    filtered_vars = {}
    for key, value in env_vars.items():
        if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
            filtered_vars[key] = '*' * min(len(value), 20) if value else 'NOT_SET'
        else:
            filtered_vars[key] = value
    
    # Show our required variables
    required_vars = ['DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_ANON_KEY', 'SECRET_KEY']
    
    print("\n🔑 REQUIRED VARIABLES:")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'password' in var.lower() or 'key' in var.lower() or 'secret' in var.lower():
                display_value = f"SET ({len(value)} chars)"
            else:
                display_value = value[:30] + "..." if len(value) > 30 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    print(f"\n📊 ENVIRONMENT SUMMARY:")
    print(f"   Total variables: {len(env_vars)}")
    print(f"   Missing required: {len(missing_vars)}")
    
    if missing_vars:
        print(f"\n🚨 MISSING VARIABLES IN RENDER:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 TO FIX:")
        print("1. Go to Render Dashboard")
        print("2. Your Service → Environment")
        print("3. Add the missing variables")
        print("4. Redeploy the service")
        return False
    
    return True

def test_dns_resolution():
    print("\n🌐 DNS RESOLUTION TEST:")
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ Cannot test DNS - DATABASE_URL not set")
        return False
    
    try:
        parsed = urlparse(db_url)
        hostname = parsed.hostname
        
        if not hostname:
            print("❌ No hostname found in DATABASE_URL")
            return False
        
        print(f"🔍 Testing DNS resolution for: {hostname}")
        
        # Test DNS resolution
        try:
            ip_address = socket.gethostbyname(hostname)
            print(f"✅ DNS resolved: {hostname} → {ip_address}")
            
            # Test if it looks like a Supabase hostname
            if '.supabase.co' in hostname:
                print("✅ Hostname appears to be valid Supabase domain")
            else:
                print("⚠️  Hostname doesn't look like Supabase (.supabase.co)")
            
            return True
            
        except socket.gaierror as e:
            print(f"❌ DNS resolution failed: {e}")
            print("💡 POSSIBLE CAUSES:")
            print("   - Incorrect hostname in DATABASE_URL")
            print("   - Typo in Supabase project ID")
            print("   - Network connectivity issues")
            print("   - Supabase project doesn't exist")
            return False
            
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        return False

def validate_database_url_format():
    print("\n📋 DATABASE_URL FORMAT VALIDATION:")
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not set")
        return False
    
    print(f"🔍 URL: {db_url[:50]}...{db_url[-20:] if len(db_url) > 70 else ''}")
    
    try:
        parsed = urlparse(db_url)
        
        checks = [
            ("Scheme", parsed.scheme, parsed.scheme.startswith('postgresql')),
            ("Hostname", parsed.hostname, parsed.hostname and '.supabase.co' in parsed.hostname),
            ("Port", parsed.port, parsed.port == 5432),
            ("Username", parsed.username, parsed.username == 'postgres'),
            ("Password", "***", bool(parsed.password)),
            ("Database", parsed.path.lstrip('/'), parsed.path.lstrip('/') == 'postgres'),
            ("SSL Mode", parsed.query, 'sslmode=require' in parsed.query)
        ]
        
        all_good = True
        for name, value, is_valid in checks:
            status = "✅" if is_valid else "❌"
            print(f"   {status} {name}: {value}")
            if not is_valid:
                all_good = False
        
        if not all_good:
            print("\n💡 CORRECT FORMAT:")
            print("DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres?sslmode=require")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error validating URL: {e}")
        return False

def main():
    env_ok = check_render_environment()
    
    if env_ok:
        url_ok = validate_database_url_format()
        if url_ok:
            dns_ok = test_dns_resolution()
            
            if dns_ok:
                print("\n🎉 ALL CHECKS PASSED!")
                print("Database connection should work now.")
            else:
                print("\n🔧 DNS RESOLUTION ISSUE")
                print("Check your Supabase project ID and hostname.")
        else:
            print("\n🔧 DATABASE_URL FORMAT ISSUE")
            print("Fix the DATABASE_URL format in Render environment.")
    else:
        print("\n🔧 MISSING ENVIRONMENT VARIABLES")
        print("Add the required variables in Render dashboard.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()