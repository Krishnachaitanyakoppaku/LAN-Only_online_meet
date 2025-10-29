#!/usr/bin/env python3
"""
Easy startup script for LAN Collaboration Server
Handles dependencies and shows connection info
"""

import sys
import os
import socket
import subprocess

def get_local_ip():
    """Get local machine IP address."""
    try:
        # Connect to external server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    missing = []
    
    # Check core Python modules (should always be available)
    try:
        import asyncio, json, socket, threading
        print("✅ Core modules: OK")
    except ImportError as e:
        print(f"❌ Core modules: {e}")
        missing.append("core-modules")
    
    # Check optional media dependencies
    try:
        import cv2
        print("✅ OpenCV: OK")
    except ImportError:
        print("⚠️  OpenCV: Missing (video processing disabled)")
    
    try:
        import pyaudio
        print("✅ PyAudio: OK")
    except ImportError:
        print("⚠️  PyAudio: Missing (audio processing disabled)")
    
    if missing:
        print(f"\n❌ Missing required packages: {', '.join(missing)}")
        return False
    
    print("✅ All required dependencies available")
    return True

def check_ports():
    """Check if required ports are available."""
    print("\n🔍 Checking ports...")
    
    ports = [9000, 10000, 11000, 12000, 13000, 14000]
    busy_ports = []
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', port))
            sock.close()
            print(f"✅ Port {port}: Available")
        except OSError:
            print(f"⚠️  Port {port}: Busy")
            busy_ports.append(port)
    
    if busy_ports:
        print(f"\n⚠️  Some ports are busy: {busy_ports}")
        print("💡 Server will try to use alternative ports")
    
    return True

def show_server_info(local_ip):
    """Show server connection information."""
    print("\n" + "=" * 60)
    print("🌐 SERVER CONNECTION INFORMATION")
    print("=" * 60)
    print()
    print("📡 Server will be available at:")
    print(f"   • Local access: localhost:9000")
    print(f"   • Network access: {local_ip}:9000")
    print()
    print("🎯 For clients to connect:")
    print(f"   • Same machine: use 'localhost'")
    print(f"   • Other machines: use '{local_ip}'")
    print()
    print("🔧 Ports used:")
    print("   • TCP Control: 9000")
    print("   • UDP Video: 10000")
    print("   • UDP Audio: 11000")
    print("   • Screen Share: 12000")
    print("   • File Upload: 13000")
    print("   • File Download: 14000")
    print()
    print("💡 Troubleshooting:")
    print("   • Make sure firewall allows these ports")
    print("   • Check that no other services use these ports")
    print("   • For network access, ensure devices are on same LAN")
    print()

def main():
    """Main startup function."""
    print("🚀 LAN Collaboration Server Startup")
    print("=" * 50)
    
    # Get local IP
    local_ip = get_local_ip()
    print(f"🌐 Detected IP: {local_ip}")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot start server due to missing dependencies")
        print("💡 Run: python install.py")
        return 1
    
    # Check ports
    check_ports()
    
    # Show server info
    show_server_info(local_ip)
    
    # Check if main_server.py exists
    if not os.path.exists('main_server.py'):
        print("❌ main_server.py not found in current directory")
        print("💡 Make sure you're in the gui/ directory")
        return 1
    
    # Start the server
    print("🎯 Starting server...")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Run the server
        result = subprocess.run([sys.executable, 'main_server.py'], 
                              cwd=os.getcwd())
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n🔌 Server stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())