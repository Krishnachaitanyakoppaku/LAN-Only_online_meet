#!/usr/bin/env python3
"""
LAN Meeting Web Server Launcher
Completely offline video conferencing solution
"""

import os
import sys
import webbrowser
import time
import threading
from web_server import LANMeetingWebServer

def get_local_ip():
    """Get local IP address"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

def open_browser_tabs(host, port):
    """Open browser tabs for host and client interfaces"""
    time.sleep(2)  # Wait for server to start
    
    try:
        # Open host interface
        webbrowser.open(f"http://{host}:{port}/host")
        time.sleep(1)
        
        # Open client interface
        webbrowser.open(f"http://{host}:{port}/client")
        
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print("Please open your browser manually and go to:")
        print(f"  Host: http://{host}:{port}/host")
        print(f"  Client: http://{host}:{port}/client")

def main():
    print("🎥 LAN Meeting Web Server")
    print("=" * 50)
    print("✅ Completely offline - no internet required!")
    print("🌐 Modern web interface - no GUI issues!")
    print("📱 Works on any device with a browser!")
    print()
    
    # Get network info
    local_ip = get_local_ip()
    port = 5000
    
    print(f"🖥️  Host Control Panel: http://localhost:{port}/host")
    print(f"👥 Client Interface: http://localhost:{port}/client")
    print(f"🌍 LAN Access: http://{local_ip}:{port}/")
    print()
    print("📋 Instructions:")
    print("1. Host opens the Host Control Panel")
    print("2. Clients open the Client Interface")
    print("3. Share the LAN address with other devices on your network")
    print("4. No internet connection needed!")
    print()
    
    # Create uploads directory
    os.makedirs('uploads', exist_ok=True)
    
    # Start browser opening in background
    browser_thread = threading.Thread(
        target=open_browser_tabs, 
        args=(local_ip, port),
        daemon=True
    )
    browser_thread.start()
    
    # Start the web server
    try:
        server = LANMeetingWebServer()
        print("🚀 Starting server...")
        server.run(host='0.0.0.0', port=port, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure port 5000 is not in use")
        print("2. Check if all required packages are installed:")
        print("   pip install -r requirements_web.txt")
        print("3. Try running as administrator if needed")

if __name__ == "__main__":
    main()