#!/usr/bin/env python3
"""
LAN Meeting Web Server Launcher
Simple script to start the web-based meeting application
"""

import subprocess
import sys
import os

def main():
    print("🚀 Starting LAN Meeting Web Server...")
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
    
    # Start the server
    try:
        print("🌐 Starting server...")
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == '__main__':
    main()