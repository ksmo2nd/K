#!/usr/bin/env python3
"""
Test script for the enhanced WiFi QR system
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.wifi_captive_service import WiFiCaptiveService


async def test_wifi_qr_generation():
    """Test the WiFi QR code generation system"""
    
    print("🧪 Testing Enhanced WiFi QR System")
    print("=" * 50)
    
    try:
        # Initialize the service
        wifi_service = WiFiCaptiveService()
        print("✅ WiFi service initialized")
        
        # Test QR code generation
        print("\n1️⃣ Testing QR code generation...")
        
        result = await wifi_service.create_wifi_access_token(
            user_id="test-user-123",
            session_id="test-session-456", 
            data_limit_mb=5000
        )
        
        if result["success"]:
            print("✅ QR code generated successfully!")
            print(f"📶 Network Name: {result['network_name']}")
            print(f"🔐 WiFi Password: {result['wifi_password']}")
            print(f"🔒 Security: {result['wifi_security']}")
            print(f"📊 Data Limit: {result['data_limit_mb']} MB")
            print(f"⏰ Session Duration: {result['session_duration']}")
            print(f"🎯 Access Type: {result['access_type']}")
            
            # Test QR data format
            print(f"\n📱 QR Code Data: {result['wifi_qr_data']}")
            
            # Verify QR data format
            if result['wifi_qr_data'].startswith("WIFI:T:WPA;S:KSWiFi_Global_"):
                print("✅ QR code format is correct")
            else:
                print("❌ QR code format is incorrect")
                
            # Test connection validation
            print("\n2️⃣ Testing connection validation...")
            validation = await wifi_service.validate_wifi_session_connection(
                result['network_name'],
                "AA:BB:CC:DD:EE:FF"
            )
            
            if validation["success"]:
                print("✅ Connection validation successful!")
                print(f"📋 Session ID: {validation['session_id']}")
                print(f"👤 User ID: {validation['user_id']}")
                print(f"💾 Data Limit: {validation['data_limit_mb']} MB")
            else:
                print(f"❌ Connection validation failed: {validation['error']}")
                
        else:
            print(f"❌ QR generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


def test_qr_format():
    """Test QR code format parsing"""
    print("\n3️⃣ Testing QR format parsing...")
    
    # Test WiFi QR format
    test_qr = "WIFI:T:WPA;S:KSWiFi_Global_ABC123;P:1234567890ABCDEF;H:false;;"
    
    if test_qr.startswith("WIFI:T:WPA;"):
        print("✅ QR format starts correctly")
        
        # Extract components
        parts = test_qr.replace("WIFI:", "").split(";")
        network_name = None
        password = None
        
        for part in parts:
            if part.startswith("S:"):
                network_name = part[2:]
            elif part.startswith("P:"):
                password = part[2:]
        
        print(f"📶 Extracted Network: {network_name}")
        print(f"🔐 Extracted Password: {password}")
        
        if network_name and network_name.startswith("KSWiFi_Global_"):
            print("✅ Network name format is correct")
        else:
            print("❌ Network name format is incorrect")
            
        if password and len(password) == 16:
            print("✅ Password format is correct")
        else:
            print("❌ Password format is incorrect")
    else:
        print("❌ QR format is incorrect")


if __name__ == "__main__":
    print("🚀 Starting WiFi QR System Tests")
    print("=" * 60)
    
    # Run QR format test (synchronous)
    test_qr_format()
    
    # Run async tests
    try:
        asyncio.run(test_wifi_qr_generation())
    except Exception as e:
        print(f"❌ Async test failed: {str(e)}")
    
    print("\n🎉 Tests completed!")