#!/usr/bin/env python3
"""
Deployment script for LAN Communication Hub
Quick setup and verification
"""

import subprocess
import sys
import os
import platform

def print_header():
    print("🚀 LAN Communication Hub - Quick Deploy")
    print("=" * 50)

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def make_scripts_executable():
    """Make shell scripts executable on Unix systems"""
    if platform.system() != "Windows":
        try:
            os.chmod("client_connect.sh", 0o755)
            print("✅ Made scripts executable")
        except:
            pass

def show_usage():
    """Show usage instructions"""
    print("\n🎯 Quick Start:")
    print("=" * 50)
    
    system = platform.system()
    
    print("1️⃣ Start Server:")
    print("   python server.py")
    print()
    
    print("2️⃣ Connect Clients:")
    if system == "Windows":
        print("   Double-click: client_connect.bat")
    else:
        print("   Run: ./client_connect.sh")
    print("   Or: python connect_client.py")
    print()
    
    print("3️⃣ Choose Method:")
    print("   1 = Browser Override (Best for camera/mic)")
    print("   2 = Direct Connection (Simple)")
    print("   3 = SSH Tunnel (Secure)")
    print("   4 = Auto-Find Server")
    print()
    
    print("✅ Deployment complete! Ready to use.")

def main():
    print_header()
    
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        print("💡 Run this script from the webserver directory")
        return 1
    
    if install_dependencies():
        make_scripts_executable()
        show_usage()
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())