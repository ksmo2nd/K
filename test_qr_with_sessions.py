#!/usr/bin/env python3
"""
Test QR generation with actual user sessions
"""

import requests
import json

# Your backend URL
BASE_URL = "https://kswifi.onrender.com/api"

# Test user from your logs
TEST_USER_ID = "c49a70e6-d4ed-413a-9bda-921e8facdfbe"

# Test session IDs from your logs
TEST_SESSIONS = [
    "5363d7b4-984f-4a3a-819d-6cf1d7655664",  # 3072 MB
    "2161bdb4-6715-476f-9f97-8bc652be3333",  # 1024 MB
    "ba3c4fc0-ac7c-4da7-8d54-4b1663bfd98f"   # 1024 MB
]

def test_qr_generation():
    """Test QR generation for active sessions"""
    
    print("🧪 Testing WiFi QR Generation with Real Sessions")
    print("=" * 60)
    
    for i, session_id in enumerate(TEST_SESSIONS, 1):
        print(f"\n{i}️⃣ Testing Session: {session_id}")
        
        try:
            # Test the new direct endpoint
            url = f"{BASE_URL}/wifi/generate-qr-for-session/{session_id}"
            print(f"🔍 Calling: {url}")
            
            # You'll need to add proper authentication header here
            headers = {
                "Content-Type": "application/json",
                # Add your auth token here:
                # "Authorization": "Bearer YOUR_JWT_TOKEN"
            }
            
            response = requests.post(url, headers=headers, timeout=30)
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    qr_data = data["data"]
                    print(f"✅ QR Generated Successfully!")
                    print(f"   • Network: {qr_data.get('network_name')}")
                    print(f"   • Security: {qr_data.get('wifi_security')}")
                    print(f"   • Data Limit: {qr_data.get('data_limit_mb')} MB")
                    print(f"   • Session Status: {qr_data.get('session_status')}")
                    print(f"   • QR Data: {qr_data.get('qr_code_data')}")
                    
                    # Check QR image
                    qr_image = qr_data.get('qr_code_image', '')
                    if qr_image.startswith('data:image/png;base64,'):
                        base64_length = len(qr_image) - 22
                        print(f"   • QR Image: ✅ Valid PNG ({base64_length} chars)")
                        
                        # Save QR image for inspection
                        import base64
                        try:
                            image_data = base64.b64decode(qr_image.split(',')[1])
                            filename = f"qr_session_{i}.png"
                            with open(filename, 'wb') as f:
                                f.write(image_data)
                            print(f"   • Saved as: {filename}")
                        except Exception as e:
                            print(f"   • ❌ Save error: {e}")
                    else:
                        print(f"   • ❌ Invalid QR image format")
                        
                else:
                    print(f"❌ QR generation failed: {data}")
                    
            elif response.status_code == 401:
                print("❌ Authentication required - add JWT token to headers")
                break
                
            elif response.status_code == 404:
                print("❌ Session not found or endpoint missing")
                
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")


def test_health_endpoint():
    """Test if health endpoint is working"""
    
    print("\n🏥 Testing Health Endpoint")
    print("=" * 30)
    
    try:
        # Test health endpoint (should not need auth)
        response = requests.get(f"{BASE_URL.replace('/api', '')}/health", timeout=10)
        
        print(f"📊 Health Status: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health Check: {health_data.get('status')}")
            print(f"   • Service: {health_data.get('service')}")
            print(f"   • Version: {health_data.get('version')}")
            print(f"   • Database: {health_data.get('database', {}).get('status')}")
        else:
            print(f"❌ Health check failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")


if __name__ == "__main__":
    print("🚀 Starting WiFi QR Tests")
    print("=" * 60)
    
    # Test health first
    test_health_endpoint()
    
    # Test QR generation
    test_qr_generation()
    
    print(f"\n🎉 Tests completed!")
    print("\n💡 Next Steps:")
    print("   1. Add your JWT token to the headers")
    print("   2. Check generated PNG files")
    print("   3. Verify QR codes scan properly")
    print("   4. Test on mobile device")