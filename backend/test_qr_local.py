#!/usr/bin/env python3
"""
Local test for QR code generation
"""

import sys
import os
sys.path.append('.')

def test_qr_generation():
    try:
        import qrcode
        import io
        import base64
        import secrets
        
        # Generate test activation code
        test_code = f"LPA:1$kswifi.onrender.com$test{secrets.token_urlsafe(8)}"
        print(f"✅ Test activation code: {test_code}")
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(test_code)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        qr_image = f"data:image/png;base64,{img_str}"
        
        print(f"✅ QR code generated successfully!")
        print(f"✅ QR code length: {len(qr_image)} characters")
        print(f"✅ QR code starts with: {qr_image[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ QR generation failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing QR code generation locally...")
    success = test_qr_generation()
    if success:
        print("🎉 QR generation test PASSED!")
    else:
        print("💥 QR generation test FAILED!")