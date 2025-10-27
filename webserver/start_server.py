#!/usr/bin/env python3
"""
Automated server startup with SSH tunnel setup for clients
"""

import os
import sys
import subprocess
import socket
import time
import threading
import signal
from datetime import datetime

def get_host_ip():
    """Get the host machine's IP address with multiple detection methods"""
    
    # Method 1: Connect to external server to get routable IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Verify it's a private network IP
        if local_ip.startswith(('192.168.', '10.', '172.')):
            print(f"✅ Detected network IP via external connection: {local_ip}")
            return local_ip
    except Exception as e:
        print(f"⚠️  External IP detection failed: {e}")
    
    # Method 2: Get all network interfaces
    try:
        import subprocess
        
        # Try different OS-specific commands
        commands = [
            ['hostname', '-I'],  # Linux
            ['ifconfig'],        # Linux/Mac
            ['ipconfig']         # Windows
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    output = result.stdout
                    
                    # Extract IP addresses from output
                    import re
                    ip_pattern = r'\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3})\b'
                    ips = re.findall(ip_pattern, output)
                    
                    if ips:
                        detected_ip = ips[0]
                        print(f"✅ Detected network IP via {cmd[0]}: {detected_ip}")
                        return detected_ip
                        
            except Exception:
                continue
                
    except Exception as e:
        print(f"⚠️  Network interface detection failed: {e}")
    
    # Method 3: Fallback to hostname resolution
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        if local_ip != '127.0.0.1' and local_ip.startswith(('192.168.', '10.', '172.')):
            print(f"✅ Detected IP via hostname resolution: {local_ip}")
            return local_ip
            
    except Exception as e:
        print(f"⚠️  Hostname resolution failed: {e}")
    
    # Final fallback
    print("❌ Could not detect network IP, using localhost")
    print("💡 You may need to manually specify the server IP for clients")
    return "localhost"

def print_banner():
    """Print startup banner"""
    print("=" * 70)
    print("🚀 LAN COMMUNICATION HUB - AUTO SETUP")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def install_requirements():
    """Install requirements from requirements.txt if available"""
    if os.path.exists('requirements.txt'):
        print("📦 Found requirements.txt - installing dependencies...")
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print(f"⚠️  Some dependencies may have failed to install:")
                print(f"   {result.stderr}")
                return True  # Continue anyway
        except Exception as e:
            print(f"❌ Failed to install requirements: {e}")
            return False
    else:
        print("📦 No requirements.txt found - checking individual packages...")
        return True

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Try to install from requirements.txt first
    if not install_requirements():
        return False
    
    # Check essential packages
    essential_missing = []
    optional_missing = []
    
    try:
        import flask
        import flask_socketio
        print("✅ Flask packages: OK")
    except ImportError as e:
        print(f"❌ Missing Flask packages: {e}")
        essential_missing.append("Flask Flask-SocketIO")
    
    # Check SSL support for HTTPS
    try:
        import ssl
        print("✅ SSL support: OK")
    except ImportError:
        print("⚠️  SSL support not available - will use HTTP only")
    
    # Check for pyOpenSSL (needed for adhoc SSL)
    try:
        import OpenSSL
        print("✅ pyOpenSSL: OK (HTTPS will work)")
    except ImportError:
        print("❌ pyOpenSSL not found (required for HTTPS)")
        essential_missing.append("pyOpenSSL")
    
    # Check optional packages
    try:
        import cv2
        import numpy as np
        from PIL import Image
        print("✅ Media processing packages: OK")
    except ImportError:
        print("ℹ️  Media processing packages not available (optional)")
        optional_missing.append("opencv-python Pillow numpy")
    
    # Check if server.py exists
    if not os.path.exists('server.py'):
        print("❌ server.py not found in current directory")
        return False
    
    if essential_missing:
        print(f"\n❌ Missing essential packages:")
        for pkg in essential_missing:
            print(f"   • {pkg}")
        print(f"\n💡 Install with:")
        print(f"   python3 install_essential.py")
        print("   OR")
        print(f"   pip install {' '.join(essential_missing)}")
        return False
    
    if optional_missing:
        print(f"\nℹ️  Optional packages not installed:")
        for pkg in optional_missing:
            print(f"   • {pkg}")
        print("💡 Install later with: pip install opencv-python Pillow numpy")
    
    print("✅ Essential dependencies: OK")
    return True

def start_server():
    """Start the main server"""
    print("🖥️  Starting main server...")
    
    try:
        # Start server in background
        server_process = subprocess.Popen([
            sys.executable, 'server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        if server_process.poll() is None:
            print("✅ Server started successfully")
            return server_process
        else:
            stdout, stderr = server_process.communicate()
            print(f"❌ Server failed to start:")
            print(f"   stdout: {stdout.decode()}")
            print(f"   stderr: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def create_client_script(server_ip):
    """Create SSH tunnel script for clients"""
    
    # Get current user as default
    import getpass
    default_username = getpass.getuser()
    
    # Windows batch script
    windows_script = f"""@echo off
echo 🔗 Setting up SSH tunnel for LAN Communication Hub
echo Server IP: {server_ip}
echo.
set /p username="Enter username for {server_ip} (default: {default_username}): "
if "%username%"=="" set username={default_username}
echo.
echo This will create a tunnel so you can access the server via localhost
echo Keep this window open while using the application
echo.
ssh -L 5000:{server_ip}:5000 %username%@{server_ip}
"""
    
    # Linux/Mac bash script
    unix_script = f"""#!/bin/bash
echo "🔗 Setting up SSH tunnel for LAN Communication Hub"
echo "Server IP: {server_ip}"
echo ""
read -p "Enter username for {server_ip} (default: {default_username}): " username
username=${{username:-{default_username}}}
echo ""
echo "This will create a tunnel so you can access the server via localhost"
echo "Keep this terminal open while using the application"
echo ""
ssh -L 5000:{server_ip}:5000 $username@{server_ip}
"""
    
    # Python script (cross-platform)
    python_script = f"""#!/usr/bin/env python3
import subprocess
import sys
import os
import getpass

def setup_ssh_tunnel():
    server_ip = "{server_ip}"
    default_username = getpass.getuser()
    username = input(f"Enter username for {{server_ip}} (default: {{default_username}}): ").strip() or default_username
    
    print("🔗 Setting up SSH tunnel for LAN Communication Hub")
    print(f"Server IP: {{server_ip}}")
    print(f"Username: {{username}}")
    print()
    print("This will create a tunnel so you can access via http://localhost:5000")
    print("Keep this terminal open while using the application")
    print()
    
    try:
        cmd = ["ssh", "-L", f"5000:{{server_ip}}:5000", f"{{username}}@{{server_ip}}"]
        print(f"Running: {{' '.join(cmd)}}")
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\\n🔌 SSH tunnel closed")
    except Exception as e:
        print(f"❌ Error: {{e}}")
        print()
        print("💡 Make sure SSH is installed and you can connect to the server")
        print(f"💡 Test connection: ssh {{username}}@{{server_ip}}")

if __name__ == "__main__":
    setup_ssh_tunnel()
"""
    
    # Write scripts
    try:
        with open('client_connect.bat', 'w') as f:
            f.write(windows_script)
        
        with open('client_connect.sh', 'w') as f:
            f.write(unix_script)
        
        # Make shell script executable
        os.chmod('client_connect.sh', 0o755)
        
        with open('client_connect.py', 'w') as f:
            f.write(python_script)
        
        print("✅ Client connection scripts created:")
        print("   📁 client_connect.bat (Windows)")
        print("   📁 client_connect.sh (Linux/Mac)")
        print("   📁 client_connect.py (Cross-platform)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating client scripts: {e}")
        return False

def show_connection_info(server_ip):
    """Show connection information"""
    print()
    print("=" * 70)
    print("🌐 CONNECTION INFORMATION")
    print("=" * 70)
    
    print(f"🖥️  SERVER (Host) - This Machine:")
    print(f"   HTTPS URL: https://localhost:5000 (recommended)")
    print(f"   HTTPS URL: https://{server_ip}:5000")
    print(f"   HTTP URL: http://localhost:5000 (fallback)")
    print(f"   Action: Create session")
    print()
    
    print(f"💻 CLIENTS (Participants) - Other Machines:")
    print(f"   🎯 RECOMMENDED: HTTPS Direct Connection")
    print(f"     URL: https://{server_ip}:5000")
    print(f"     Note: Browser will show security warning for self-signed certificate")
    print(f"     Action: Click 'Advanced' → 'Proceed to {server_ip} (unsafe)'")
    print(f"     Result: Camera/microphone will work!")
    print()
    
    print(f"   📋 ALTERNATIVE: SSH Tunnel (if HTTPS doesn't work)")
    print(f"     1. Run: python3 connect_client.py")
    print(f"     2. Access: http://localhost:5000")
    print(f"     3. Join with session ID: {server_ip}")
    print()
    
    print("🎯 SESSION INFORMATION:")
    print(f"   Server IP: {server_ip}")
    print(f"   Session ID: {server_ip}")
    print(f"   HTTPS Port: 5000")
    print()
    
    print("🔒 HTTPS CERTIFICATE INFO:")
    print("   • Server uses self-signed certificate")
    print("   • Browser will show security warning")
    print("   • This is normal and safe for local network")
    print("   • Click 'Advanced' and 'Proceed' to continue")
    print()
    
    print("🔧 TROUBLESHOOTING URLS:")
    print(f"   Media test (HTTPS): https://{server_ip}:5000/media-test")
    print(f"   Media test (HTTP): http://{server_ip}:5000/media-test")
    print(f"   Server debug: https://{server_ip}:5000/api/debug/sessions")
    print()

def handle_shutdown(signum, frame):
    """Handle shutdown gracefully"""
    print("\n🔌 Shutting down server...")
    sys.exit(0)

def monitor_server(server_process):
    """Monitor server process"""
    while True:
        if server_process.poll() is not None:
            print("❌ Server process stopped unexpectedly")
            break
        time.sleep(5)

def main():
    """Main startup function"""
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, handle_shutdown)
    
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please fix the issues above.")
        return 1
    
    # Get server IP
    server_ip = get_host_ip()
    print(f"🌐 Detected server IP: {server_ip}")
    
    # Start server
    server_process = start_server()
    if not server_process:
        print("\n❌ Failed to start server")
        return 1
    
    # Create client scripts
    if create_client_script(server_ip):
        print("✅ Client setup completed")
    
    # Show connection info
    show_connection_info(server_ip)
    
    print("=" * 70)
    print("🎉 SETUP COMPLETE!")
    print("=" * 70)
    print("Server is running. Press Ctrl+C to stop.")
    print()
    
    # Monitor server
    try:
        monitor_server(server_process)
    except KeyboardInterrupt:
        print("\n🔌 Shutting down...")
    finally:
        if server_process and server_process.poll() is None:
            server_process.terminate()
            server_process.wait()
        print("✅ Server stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())