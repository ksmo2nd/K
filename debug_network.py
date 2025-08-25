#!/usr/bin/env python3
"""
Deep network debugging for Render deployment issues
"""
import os
import sys
import socket
import asyncio
import time
from urllib.parse import urlparse

async def deep_network_debug():
    print("🔍 DEEP NETWORK ANALYSIS")
    print("=" * 60)
    
    # Check environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not set - cannot debug network")
        return
    
    parsed = urlparse(db_url)
    hostname = parsed.hostname
    port = parsed.port or 5432
    
    print(f"🎯 Target: {hostname}:{port}")
    print()
    
    # 1. DNS Resolution Analysis
    print("1️⃣ DNS RESOLUTION ANALYSIS:")
    try:
        print(f"   Resolving {hostname}...")
        start_time = time.time()
        
        # Get all IP addresses
        addr_info = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        resolve_time = time.time() - start_time
        
        print(f"   ✅ DNS resolved in {resolve_time:.3f}s")
        print(f"   📋 Found {len(addr_info)} addresses:")
        
        ipv4_addrs = []
        ipv6_addrs = []
        
        for family, type_, proto, canonname, sockaddr in addr_info:
            ip = sockaddr[0]
            if family == socket.AF_INET:
                ipv4_addrs.append(ip)
                print(f"      IPv4: {ip}")
            elif family == socket.AF_INET6:
                ipv6_addrs.append(ip)
                print(f"      IPv6: {ip}")
        
        return ipv4_addrs, ipv6_addrs, port
        
    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return [], [], port
    except Exception as e:
        print(f"   ❌ DNS error: {e}")
        return [], [], port

def test_socket_connection(ip, port, family):
    """Test direct socket connection"""
    try:
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        
        start_time = time.time()
        result = sock.connect_ex((ip, port))
        connect_time = time.time() - start_time
        
        sock.close()
        
        if result == 0:
            return True, f"Connected in {connect_time:.3f}s"
        else:
            return False, f"Connection failed (errno {result}) after {connect_time:.3f}s"
            
    except Exception as e:
        return False, f"Socket error: {e}"

async def test_connectivity(ipv4_addrs, ipv6_addrs, port):
    print("\n2️⃣ CONNECTIVITY TESTING:")
    
    # Test IPv4 addresses
    if ipv4_addrs:
        print("   📡 Testing IPv4 connections:")
        for ip in ipv4_addrs:
            success, message = test_socket_connection(ip, port, socket.AF_INET)
            status = "✅" if success else "❌"
            print(f"      {status} {ip}:{port} - {message}")
    else:
        print("   ⚪ No IPv4 addresses to test")
    
    # Test IPv6 addresses
    if ipv6_addrs:
        print("   📡 Testing IPv6 connections:")
        for ip in ipv6_addrs:
            success, message = test_socket_connection(ip, port, socket.AF_INET6)
            status = "✅" if success else "❌"
            print(f"      {status} [{ip}]:{port} - {message}")
    else:
        print("   ⚪ No IPv6 addresses to test")

def check_render_environment():
    print("\n3️⃣ RENDER ENVIRONMENT ANALYSIS:")
    
    # Check if we're on Render
    render_service = os.getenv('RENDER_SERVICE_NAME', 'Unknown')
    render_region = os.getenv('RENDER_REGION', 'Unknown')
    
    print(f"   🏢 Render Service: {render_service}")
    print(f"   🌍 Render Region: {render_region}")
    
    # Check network interfaces
    try:
        import subprocess
        result = subprocess.run(['ip', 'route'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("   🛣️  Network routes:")
            for line in result.stdout.strip().split('\n')[:3]:  # Show first 3 routes
                print(f"      {line}")
        else:
            print("   ⚪ Could not get network routes")
    except:
        print("   ⚪ Network route check unavailable")
    
    # Check if we can reach internet
    print("\n   🌐 Internet connectivity test:")
    try:
        success, message = test_socket_connection('8.8.8.8', 53, socket.AF_INET)
        status = "✅" if success else "❌"
        print(f"      {status} Google DNS (8.8.8.8:53) - {message}")
        
        success, message = test_socket_connection('1.1.1.1', 53, socket.AF_INET)
        status = "✅" if success else "❌"
        print(f"      {status} Cloudflare DNS (1.1.1.1:53) - {message}")
        
    except Exception as e:
        print(f"      ❌ Internet test failed: {e}")

async def test_asyncpg_connection():
    print("\n4️⃣ ASYNCPG CONNECTION TEST:")
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("   ❌ DATABASE_URL not set")
        return
    
    try:
        # Test with original URL (including sslmode and pgbouncer)
        print(f"   🔌 Testing original DATABASE_URL...")
        print(f"      URL: {db_url[:50]}...{db_url[-30:] if len(db_url) > 80 else ''}")
        
        import asyncpg
        
        start_time = time.time()
        conn = await asyncio.wait_for(asyncpg.connect(db_url), timeout=15)
        connect_time = time.time() - start_time
        
        await conn.close()
        print(f"   ✅ asyncpg connection successful in {connect_time:.3f}s")
        
    except asyncio.TimeoutError:
        print("   ❌ asyncpg connection timed out after 15s")
    except Exception as e:
        print(f"   ❌ asyncpg connection failed: {e}")
        print(f"      Error type: {type(e).__name__}")
        
        # Check for specific network errors
        if "Network is unreachable" in str(e):
            print("      💡 This is the exact error we're seeing!")
        elif "Connection refused" in str(e):
            print("      💡 Connection refused - service may be down")
        elif "timeout" in str(e).lower():
            print("      💡 Timeout - network latency or firewall issue")

async def main():
    ipv4_addrs, ipv6_addrs, port = await deep_network_debug()
    
    if ipv4_addrs or ipv6_addrs:
        await test_connectivity(ipv4_addrs, ipv6_addrs, port)
    
    check_render_environment()
    await test_asyncpg_connection()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("If all tests pass but asyncpg fails, the issue might be:")
    print("1. Import-time initialization before network is ready")
    print("2. Render's container networking restrictions")
    print("3. Supabase-specific connection requirements")
    print("4. SSL/TLS handshake issues")

if __name__ == "__main__":
    asyncio.run(main())