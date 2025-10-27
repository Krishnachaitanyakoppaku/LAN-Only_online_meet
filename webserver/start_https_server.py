#!/usr/bin/env python3
"""
HTTPS Server Startup Script
Automatically generates SSL certificates and starts the server with HTTPS
"""

import os
import sys
import subprocess
from ssl_helper import get_ssl_context, get_local_ip

def main():
    print("🚀 Starting LAN Communication Server with HTTPS...")
    print("=" * 60)
    
    # Get server IP
    server_ip = get_local_ip()
    print(f"📍 Server IP: {server_ip}")
    
    # Generate SSL certificate
    print("🔒 Generating SSL certificate...")
    ssl_context = get_ssl_context(server_ip)
    
    if ssl_context:
        print("✅ SSL certificate ready!")
        print(f"   Certificate: {ssl_context[0]}")
        print(f"   Private Key: {ssl_context[1]}")
    else:
        print("❌ SSL certificate generation failed")
        print("   Server will try to use Flask's built-in SSL")
    
    print("\n🌐 Server URLs:")
    print(f"   Main Page:     https://{server_ip}:5000/")
    print(f"   Camera Test:   https://{server_ip}:5000/camera-test")
    print(f"   Media Test:    https://{server_ip}:5000/media-test")
    print(f"   Join Session:  https://{server_ip}:5000/join")
    print(f"   Host Session:  https://{server_ip}:5000/host")
    
    print("\n⚠️  Browser Security Warning:")
    print("   You will see a security warning for self-signed certificate")
    print("   Click 'Advanced' → 'Proceed to [IP] (unsafe)' to continue")
    print("   This is safe for local network use")
    
    print("\n📱 For mobile devices:")
    print(f"   Connect to the same WiFi network")
    print(f"   Open: https://{server_ip}:5000/camera-test")
    print(f"   Accept the security warning")
    
    print("\n" + "=" * 60)
    print("🎯 Starting server... Press Ctrl+C to stop")
    print("=" * 60)
    
    # Start the server
    try:
        os.system("python server.py")
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == "__main__":
    main()