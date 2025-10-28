#!/usr/bin/env python3
import subprocess
import sys
import os
import getpass

def setup_ssh_tunnel():
    server_ip = "172.17.253.127"
    default_username = getpass.getuser()
    username = input(f"Enter username for {server_ip} (default: {default_username}): ").strip() or default_username
    
    print("🔗 Setting up SSH tunnel for LAN Communication Hub")
    print(f"Server IP: {server_ip}")
    print(f"Username: {username}")
    print()
    print("This will create a tunnel so you can access via http://localhost:5000")
    print("Keep this terminal open while using the application")
    print()
    
    try:
        cmd = ["ssh", "-L", f"5000:{server_ip}:5000", f"{username}@{server_ip}"]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🔌 SSH tunnel closed")
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("💡 Make sure SSH is installed and you can connect to the server")
        print(f"💡 Test connection: ssh {username}@{server_ip}")

if __name__ == "__main__":
    setup_ssh_tunnel()
