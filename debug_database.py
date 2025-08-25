#!/usr/bin/env python3
"""
Debug script to diagnose database connection issues
"""
import os
import sys
import asyncio
from urllib.parse import urlparse

def check_database_url():
    print("🔍 Database Connection Debug")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL environment variable is NOT SET")
        print()
        print("📋 REQUIRED FORMAT:")
        print("DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres")
        print()
        print("📍 HOW TO GET IT:")
        print("1. Go to Supabase Dashboard")
        print("2. Settings → Database") 
        print("3. Copy 'Connection string'")
        print("4. Replace [YOUR-PASSWORD] with your actual password")
        return False
    
    print(f"✅ DATABASE_URL is set")
    
    # Parse the URL
    try:
        parsed = urlparse(db_url)
        print()
        print("📋 DATABASE_URL BREAKDOWN:")
        print(f"   Scheme: {parsed.scheme}")
        print(f"   Host: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Database: {parsed.path.lstrip('/')}")
        print(f"   Username: {parsed.username}")
        print(f"   Password: {'*' * len(parsed.password) if parsed.password else 'NOT SET'}")
        print(f"   Query params: {parsed.query}")
        
        # Check for SSL mode
        if 'sslmode=require' in db_url:
            print("✅ SSL mode is set to 'require' (good for Supabase)")
        elif 'sslmode' in db_url:
            print(f"⚠️  SSL mode is set but not 'require': {parsed.query}")
        else:
            print("❌ SSL mode not set - Supabase external connections need ?sslmode=require")
        
        # Validate components
        issues = []
        if not parsed.scheme.startswith('postgresql'):
            issues.append(f"❌ Invalid scheme: {parsed.scheme} (should be 'postgresql')")
        else:
            print("✅ Scheme is valid")
            
        if not parsed.hostname:
            issues.append("❌ Missing hostname")
        elif not parsed.hostname.endswith('.supabase.co'):
            issues.append(f"⚠️  Hostname doesn't look like Supabase: {parsed.hostname}")
        else:
            print("✅ Hostname looks valid")
            
        if not parsed.port:
            issues.append("❌ Missing port")
        elif parsed.port != 5432:
            issues.append(f"⚠️  Unusual port: {parsed.port} (expected 5432)")
        else:
            print("✅ Port is correct (5432)")
            
        if not parsed.username:
            issues.append("❌ Missing username")
        elif parsed.username != 'postgres':
            issues.append(f"⚠️  Unusual username: {parsed.username} (expected 'postgres')")
        else:
            print("✅ Username is correct")
            
        if not parsed.password:
            issues.append("❌ Missing password")
        else:
            print("✅ Password is set")
            
        if not parsed.path or parsed.path == '/':
            issues.append("❌ Missing database name")
        elif parsed.path.lstrip('/') != 'postgres':
            issues.append(f"⚠️  Unusual database: {parsed.path.lstrip('/')} (expected 'postgres')")
        else:
            print("✅ Database name is correct")
        
        if issues:
            print()
            print("🚨 ISSUES FOUND:")
            for issue in issues:
                print(f"   {issue}")
            return False
            
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        return False
    
    return True

async def test_database_connection():
    print()
    print("🧪 TESTING DATABASE CONNECTION:")
    
    try:
        # Test the database connection logic
        sys.path.insert(0, '/workspace/backend')
        from app.core.database import create_database_url
        
        db_url = create_database_url()
        print(f"✅ Database URL created successfully")
        print(f"   Async URL: {db_url[:50]}...")
        
        # Test actual connection
        import asyncpg
        
        raw_url = os.getenv('DATABASE_URL')
        print()
        print("🔌 Testing direct asyncpg connection...")
        print(f"   URL: {raw_url[:50]}...{raw_url[-20:] if len(raw_url) > 70 else ''}")
        
        try:
            conn = await asyncpg.connect(raw_url, timeout=10)
            await conn.close()
            print("✅ Direct asyncpg connection successful!")
            
            # Also test the processed URL
            print()
            print("🔌 Testing processed SQLAlchemy URL...")
            processed_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
            conn2 = await asyncpg.connect(processed_url, timeout=10)
            await conn2.close()
            print("✅ Processed URL connection successful!")
            
            return True
        except asyncpg.InvalidAuthorizationSpecificationError:
            print("❌ Authentication failed - check password")
            print("💡 Make sure you replaced [YOUR-PASSWORD] with actual password")
            return False
        except asyncpg.CannotConnectNowError:
            print("❌ Cannot connect - server may be down")
            print("💡 Check if your Supabase project is paused")
            return False
        except asyncpg.ConnectionDoesNotExistError:
            print("❌ Database does not exist")
            return False
        except asyncpg.InterfaceError as e:
            if "SSL" in str(e):
                print(f"❌ SSL connection failed: {e}")
                print("💡 Make sure you have ?sslmode=require at the end of DATABASE_URL")
            else:
                print(f"❌ Interface error: {e}")
            return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            if "SSL" in str(e) or "ssl" in str(e).lower():
                print("💡 This looks like an SSL issue - ensure ?sslmode=require is in your DATABASE_URL")
            return False
            
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False

async def main():
    url_ok = check_database_url()
    
    if url_ok:
        conn_ok = await test_database_connection()
        
        if conn_ok:
            print()
            print("🎉 DATABASE CONNECTION IS WORKING!")
            print("The issue might be elsewhere in the application.")
        else:
            print()
            print("💡 SOLUTIONS:")
            print("1. Check your Supabase database password")
            print("2. Ensure your Supabase project is not paused")
            print("3. Verify the connection string from Supabase dashboard")
            print("4. Check if your IP is allowed (Supabase should allow all by default)")
    else:
        print()
        print("💡 SOLUTION:")
        print("Fix the DATABASE_URL environment variable in Render")
    
    print()
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())