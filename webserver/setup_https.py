#!/usr/bin/env python3
"""
Setup HTTPS for the server to enable camera/microphone access
"""

import os
import subprocess
import sys

def generate_self_signed_cert():
    """Generate a self-signed SSL certificate"""
    print("🔐 Generating self-signed SSL certificate...")
    
    try:
        # Create certs directory
        os.makedirs("certs", exist_ok=True)
        
        # Generate private key and certificate
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:4096", 
            "-keyout", "certs/key.pem", 
            "-out", "certs/cert.pem", 
            "-days", "365", "-nodes",
            "-subj", "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        ]
        
        subprocess.run(cmd, check=True)
        print("✅ SSL certificate generated successfully")
        return True
        
    except subprocess.CalledProcessError:
        print("❌ Failed to generate certificate")
        print("💡 Make sure OpenSSL is installed:")
        print("   • Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        print("   • Linux: sudo apt install openssl")
        print("   • Mac: brew install openssl")
        return False
    except FileNotFoundError:
        print("❌ OpenSSL not found")
        print("💡 Install OpenSSL first")
        return False

def create_https_server():
    """Create HTTPS version of the server"""
    
    server_code = '''#!/usr/bin/env python3
"""
HTTPS version of the LAN Communication Hub server
Enables camera/microphone access by using SSL
"""

from flask import Flask
from flask_socketio import SocketIO
import ssl

# Import your existing app
try:
    from app import app, socketio
except ImportError:
    print("❌ Could not import app.py")
    print("💡 Make sure app.py exists in the same directory")
    exit(1)

if __name__ == '__main__':
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('certs/cert.pem', 'certs/key.pem')
    
    print("🔐 Starting HTTPS server...")
    print("📱 Camera/microphone access will be enabled!")
    print("🌐 Access via: https://[SERVER_IP]:5443")
    print("⚠️  You'll see a security warning - click 'Advanced' and 'Proceed'")
    print()
    
    # Run with SSL
    socketio.run(app, 
                host='0.0.0.0', 
                port=5443, 
                debug=True,
                ssl_context=context,
                allow_unsafe_werkzeug=True)
'''
    
    with open("app_https.py", "w") as f:
        f.write(server_code)
    
    print("✅ Created app_https.py")

def main():
    print("=" * 60)
    print("🔐 HTTPS Setup for Camera/Microphone Access")
    print("=" * 60)
    print()
    print("This will enable HTTPS on your server so browsers")
    print("allow camera and microphone access.")
    print()
    
    if generate_self_signed_cert():
        create_https_server()
        print()
        print("🎉 HTTPS setup complete!")
        print()
        print("📋 Next steps:")
        print("1. Run the HTTPS server: python app_https.py")
        print("2. Access via: https://[SERVER_IP]:5443")
        print("3. Accept the security warning in browser")
        print("4. Camera/microphone will now work!")
        print()
        print("⚠️  Note: You'll see a 'Not Secure' warning because")
        print("   it's a self-signed certificate. This is normal.")

if __name__ == "__main__":
    main()