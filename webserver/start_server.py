#!/usr/bin/env python3
"""
LAN Communication Hub - Startup Script
This script helps users start the server easily
"""

import os
import sys
import subprocess
import platform
import webbrowser
import time
import socket

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask', 'flask_socketio', 'opencv-python', 
        'numpy', 'pillow', 'eventlet'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'opencv-python':
                import cv2
            elif package == 'pillow':
                import PIL
            elif package == 'flask_socketio':
                import flask_socketio
            else:
                __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is not installed")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ All packages installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please run: pip install -r requirements.txt")
            return False
    
    return True

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

def check_port_available(port):
    """Check if port is available"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))
        s.close()
        return True
    except:
        return False

def start_server():
    """Start the Flask server"""
    print("\n🚀 Starting LAN Communication Hub Server...")
    print("=" * 50)
    
    # Check if port is available
    if not check_port_available(5000):
        print("❌ Port 5000 is already in use")
        print("Please stop any other services using port 5000 or modify the server.py file")
        return False
    
    # Get local IP
    local_ip = get_local_ip()
    
    print(f"🌐 Server will be available at:")
    print(f"   Local:   http://localhost:5000")
    print(f"   Network: http://{local_ip}:5000")
    print(f"\n📱 Share the network URL with other users on your LAN")
    print(f"🔧 UDP streaming port: 5001")
    print("\n" + "=" * 50)
    
    # Start the server
    try:
        # Import and run the server
        import server
        print("✅ Server started successfully!")
        print("Press Ctrl+C to stop the server")
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://localhost:5000')
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Run the server
        server.socketio.run(server.app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🎯 LAN Communication Hub - Startup Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if server.py exists
    if not os.path.exists('server.py'):
        print("❌ server.py not found. Please run this script from the project directory")
        sys.exit(1)
    
    # Start server
    if not start_server():
        sys.exit(1)

if __name__ == "__main__":
    main()
