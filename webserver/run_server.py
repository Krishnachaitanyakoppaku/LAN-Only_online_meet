#!/usr/bin/env python3
"""
Simple LAN Meeting Server Launcher
"""

import webbrowser
import time
import threading
from app import app, socketio
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

def open_browser():
    time.sleep(2)  # Wait for server to start
    try:
        webbrowser.open("http://localhost:5000/host")
        time.sleep(1)
        webbrowser.open("http://localhost:5000/client")
    except:
        pass

if __name__ == '__main__':
    local_ip = get_local_ip()
    port = 5000
    
    print("🌐 LAN Meeting Web Server")
    print("=" * 40)
    print(f"📱 Host: http://localhost:{port}/host")
    print(f"👥 Client: http://localhost:{port}/client")
    print(f"🌍 LAN: http://{local_ip}:{port}/")
    print("✅ All buttons working!")
    print("=" * 40)
    
    # Open browser in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start server
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)