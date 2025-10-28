#!/usr/bin/env python3
"""
Client connection script - SSH tunnel for camera/microphone access
This allows clients to access the server via localhost (which browsers allow for HTTP media)
"""

import subprocess
import sys
import socket
import getpass

def get_server_ip():
    """Prompt user for server IP"""
    print("=" * 60)
    print("🔗 LAN Communication Hub - Client Connection")
    print("=" * 60)
    print()
    print("This will create an SSH tunnel so you can access the server via localhost")
    print("This is REQUIRED for camera/microphone access over HTTP")
    print()
    
    server_ip = input("Enter server IP address: ").strip()
    
    if not server_ip:
        print("❌ Server IP is required")
        return None
    
    return server_ip

def setup_ssh_tunnel():
    """Setup SSH tunnel for client"""
    server_ip = get_server_ip()
    
    if not server_ip:
        return False
    
    default_username = getpass.getuser()
    username = input(f"Enter username for {server_ip} (default: {default_username}): ").strip() or default_username
    
    print()
    print("=" * 60)
    print("🔌 Setting up SSH tunnel...")
    print("=" * 60)
    print(f"Server IP: {server_ip}")
    print(f"Username: {username}")
    print(f"Tunnel: localhost:5000 -> {server_ip}:5000")
    print()
    print("⚠️  Keep this terminal open while using the application!")
    print()
    print("After tunnel is established:")
    print(f"   1. Open browser and go to: http://localhost:5000")
    print(f"   2. Join session with session ID: {server_ip}")
    print(f"   3. Camera/microphone permissions will work!")
    print()
    print("Press Ctrl+C to close the tunnel")
    print("=" * 60)
    print()
    
    try:
        # Create SSH tunnel
        cmd = ["ssh", "-L", f"5000:{server_ip}:5000", f"{username}@{server_ip}"]
        
        print(f"Running: {' '.join(cmd)}")
        print()
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🔌 SSH tunnel closed")
        return True
    except FileNotFoundError:
        print("❌ SSH not found. Please install SSH:")
        print("   • Linux/Mac: Usually pre-installed")
        print("   • Windows: Install OpenSSH or PuTTY")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("💡 Troubleshooting:")
        print(f"   1. Make sure SSH is installed and accessible")
        print(f"   2. Test connection: ssh {username}@{server_ip}")
        print(f"   3. Check if server is running on {server_ip}:5000")
        return False
    
    return True

if __name__ == "__main__":
    try:
        setup_ssh_tunnel()
    except Exception as e:
        print(f"❌ Failed to setup tunnel: {e}")
        sys.exit(1)
