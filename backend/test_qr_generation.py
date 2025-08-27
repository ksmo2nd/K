#!/usr/bin/env python3
"""
Quick test for QR code generation to debug the yellow/blank issue
"""

import sys
import os
import base64

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.wifi_captive_service import WiFiCaptiveService


def test_qr_generation():
    """Test QR code generation with debug output"""
    
    print("🧪 Testing QR Code Generation")
    print("=" * 40)
    
    try:
        # Initialize the service
        wifi_service = WiFiCaptiveService()
        print("✅ WiFi service initialized")
        
        # Test QR data (standard WiFi format)
        test_qr_data = "WIFI:T:WPA;S:KSWiFi_Global_TEST123;P:1234567890ABCDEF;H:false;;"
        print(f"📱 Test QR Data: {test_qr_data}")
        
        # Generate QR code
        print("\n🔍 Generating QR code...")
        qr_image = wifi_service.generate_wifi_qr_code(test_qr_data)
        
        # Analyze the result
        print(f"\n📊 QR Code Analysis:")
        print(f"   • Format: {'✅ Valid' if qr_image.startswith('data:image/png;base64,') else '❌ Invalid'}")
        print(f"   • Base64 length: {len(qr_image) - 22}")  # Subtract prefix length
        
        # Extract just the base64 part
        base64_data = qr_image.replace('data:image/png;base64,', '')
        
        # Decode and check if it's valid image data
        try:
            image_bytes = base64.b64decode(base64_data)
            print(f"   • Image size: {len(image_bytes)} bytes")
            print(f"   • PNG header: {'✅ Valid' if image_bytes.startswith(b'\\x89PNG') else '❌ Invalid'}")
            
            # Save to file for manual inspection
            with open('test_qr_code.png', 'wb') as f:
                f.write(image_bytes)
            print(f"   • Saved as: test_qr_code.png")
            
        except Exception as e:
            print(f"   • ❌ Base64 decode error: {e}")
        
        print(f"\n✅ QR generation completed!")
        print(f"📱 Full QR data (first 100 chars): {qr_image[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_qr_colors():
    """Test different QR code color combinations"""
    
    print("\n🎨 Testing QR Code Colors")
    print("=" * 40)
    
    import qrcode
    from PIL import Image
    
    # Test basic QR generation
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data("WIFI:T:WPA;S:TestNetwork;P:TestPassword;H:false;;")
    qr.make(fit=True)
    
    # Test different color combinations
    color_tests = [
        ("black", "white", "Standard"),
        ("#000000", "#FFFFFF", "Hex colors"),
        ((0, 0, 0), (255, 255, 255), "RGB tuples")
    ]
    
    for i, (fill_color, back_color, description) in enumerate(color_tests):
        try:
            img = qr.make_image(fill_color=fill_color, back_color=back_color)
            print(f"   • {description}: ✅ Success (mode: {img.mode})")
            
            # Save test image
            img.save(f'qr_test_{i}.png')
            
        except Exception as e:
            print(f"   • {description}: ❌ Error - {e}")


if __name__ == "__main__":
    print("🚀 Starting QR Code Generation Tests")
    print("=" * 50)
    
    # Run main test
    success = test_qr_generation()
    
    # Run color tests
    test_qr_colors()
    
    print(f"\n🎉 Tests completed! {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("Check the generated PNG files to verify QR code appearance.")