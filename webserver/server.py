#!/usr/bin/env python3
"""
LAN Meeting Web Server - Server Only
Starts only the server without opening client browser
"""

import subprocess
import sys
import os
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

def main():
    print("🌐 LAN Meeting Web Server - Server Mode")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found!")
        print("Please run this script from the webserver directory.")
        return
    
    # Check if requirements are installed
    try:
        import flask
        import flask_socketio
        print("✅ Dependencies found")
    except ImportError:
        print("❌ Missing dependencies!")
        print("Please install requirements: pip install -r requirements_web.txt")
        return
    
    local_ip = get_local_ip()
    port = 5000
    
    print(f"📱 Host Interface: http://localhost:{port}/host")
    print(f"👥 Client Interface: http://localhost:{port}/client")
    print(f"🌍 LAN Access: http://{local_ip}:{port}/")
    print("=" * 50)
    print("🚀 Starting server...")
    print("📝 Server will run without opening browser")
    print("💡 Clients can connect using the URLs above")
    print("=" * 50)
    
    # Start the server
    try:
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == '__main__':
    main()