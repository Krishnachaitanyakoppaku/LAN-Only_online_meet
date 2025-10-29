#!/usr/bin/env python3
"""
Easy startup script for GUI LAN Communication Client
Handles dependencies and provides connection help
"""

import sys
import os
import subprocess

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    missing = []
    
    # Check PyQt6
    try:
        import PyQt6
        print("✅ PyQt6: OK")
    except ImportError:
        print("❌ PyQt6: Missing")
        missing.append("PyQt6")
    
    # Check OpenCV (optional)
    try:
        import cv2
        print("✅ OpenCV: OK")
    except ImportError:
        print("⚠️  OpenCV: Missing (video features disabled)")
    
    # Check PyAudio (optional)
    try:
        import pyaudio
        print("✅ PyAudio: OK")
    except ImportError:
        print("⚠️  PyAudio: Missing (audio features disabled)")
    
    if missing:
        print(f"\n❌ Missing required packages: {', '.join(missing)}")
        print("\n💡 Install with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("✅ All required dependencies available")
    return True

def show_connection_help():
    """Show connection help."""
    print("\n" + "=" * 60)
    print("🔗 CONNECTION HELP")
    print("=" * 60)
    print()
    print("1️⃣ Start the server first:")
    print("   python main_server.py")
    print()
    print("2️⃣ Find server IP:")
    print("   • Same machine: use 'localhost'")
    print("   • Different machine: use server's IP address")
    print("   • Run connection test: python connection_test.py")
    print()
    print("3️⃣ Common server IPs:")
    print("   • localhost (same machine)")
    print("   • 192.168.1.x (home network)")
    print("   • 10.0.0.x (office network)")
    print()
    print("4️⃣ Troubleshooting:")
    print("   • Check firewall allows ports 9000, 10000, 11000")
    print("   • Ensure you're on the same network")
    print("   • Try: python connection_test.py [SERVER_IP]")
    print()

def main():
    """Main startup function."""
    print("🚀 LAN Communication GUI Client")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot start client due to missing dependencies")
        return 1
    
    # Show connection help
    show_connection_help()
    
    # Check if main_client.py exists
    if not os.path.exists('main_client.py'):
        print("❌ main_client.py not found in current directory")
        print("💡 Make sure you're in the gui/ directory")
        return 1
    
    # Start the client
    print("🎯 Starting GUI client...")
    print("=" * 50)
    
    try:
        # Import and run the client
        from main_client import CollaborationClient, QApplication
        
        app = QApplication(sys.argv)
        client = CollaborationClient()
        client.show()
        
        print("✅ GUI client started successfully!")
        print("💡 Use the connection dialog to connect to server")
        
        return app.exec()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")
        return 1
    except Exception as e:
        print(f"❌ Startup error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())