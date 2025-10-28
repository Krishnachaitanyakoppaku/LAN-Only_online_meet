#!/usr/bin/env python3
"""
LAN Communication Hub - Client Connection Manager
Comprehensive client connection with multiple methods for camera/microphone access
"""

import subprocess
import sys
import os
import platform
import webbrowser
import getpass
import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor
import time

try:
    import requests
except ImportError:
    requests = None

def get_server_ip():
    """Prompt user for server IP"""
    print("Enter server IP address: ", end="")
    server_ip = input().strip()
    
    if not server_ip:
        print("❌ Server IP is required")
        return None
    
    return server_ip

def test_server_connection(server_ip, port=5000, timeout=3):
    """Test if server is reachable"""
    if not requests:
        return False
    try:
        response = requests.get(f"http://{server_ip}:{port}", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def find_chrome_executable():
    """Find Chrome executable on different platforms"""
    system = platform.system().lower()
    
    if system == "windows":
        paths = [
            os.path.join(os.environ.get("ProgramFiles", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
        ]
    elif system == "darwin":  # macOS
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    else:  # Linux
        paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def browser_override_connection(server_ip, port=5000):
    """Connect using browser override for camera/microphone access"""
    print("🌐 Browser Override Method")
    print("=" * 50)
    print("Starting browser with media access enabled...")
    
    chrome_path = find_chrome_executable()
    if not chrome_path:
        print("❌ Chrome not found")
        print("💡 Please install Google Chrome for this method")
        return False
    
    url = f"http://{server_ip}:{port}"
    temp_dir = os.path.join(os.path.expanduser("~"), ".chrome-dev-session")
    
    try:
        cmd = [
            chrome_path,
            f"--unsafely-treat-insecure-origin-as-secure={url}",
            f"--user-data-dir={temp_dir}",
            "--allow-running-insecure-content",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            url
        ]
        
        print(f"🚀 Opening: {url}")
        print("📱 Camera and microphone access enabled!")
        
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
        
    except Exception as e:
        print(f"❌ Failed to start browser: {e}")
        return False

def direct_connection(server_ip, port=5000):
    """Direct HTTP connection (no camera/microphone)"""
    print("🌐 Direct Connection Method")
    print("=" * 50)
    
    if test_server_connection(server_ip, port):
        print(f"✅ Server reachable at {server_ip}:{port}")
        url = f"http://{server_ip}:{port}"
        
        try:
            webbrowser.open(url)
            print(f"🚀 Opened: {url}")
            print("⚠️  Note: Camera/microphone may not work over HTTP")
            return True
        except Exception as e:
            print(f"❌ Could not open browser: {e}")
            print(f"Please manually open: {url}")
            return False
    else:
        print(f"❌ Cannot reach server at {server_ip}:{port}")
        return False

def ssh_tunnel_connection(server_ip):
    """SSH tunnel connection for secure camera/microphone access"""
    print("🔌 SSH Tunnel Method")
    print("=" * 50)
    
    default_username = getpass.getuser()
    username = input(f"Username for {server_ip} (default: {default_username}): ").strip() or default_username
    
    print(f"Creating tunnel: localhost:5000 -> {server_ip}:5000")
    print("⚠️  Keep this terminal open while using the application!")
    print()
    
    try:
        cmd = ["ssh", "-L", f"5000:{server_ip}:5000", f"{username}@{server_ip}"]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)
        return True
        
    except KeyboardInterrupt:
        print("\n🔌 SSH tunnel closed")
        return True
    except FileNotFoundError:
        print("❌ SSH not found")
        return False
    except Exception as e:
        print(f"❌ SSH Error: {e}")
        return False

def scan_local_network():
    """Scan local network for servers"""
    print("🔍 Network Scanner")
    print("=" * 50)
    
    try:
        # Get local network
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        print(f"Scanning {network}...")
        
        found_servers = []
        
        def check_ip(ip):
            if test_server_connection(str(ip), timeout=1):
                found_servers.append(str(ip))
                print(f"✅ Found server: {ip}")
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(check_ip, list(network.hosts())[:50])  # Limit scan
        
        if found_servers:
            print(f"\n🎉 Found {len(found_servers)} server(s)")
            for i, ip in enumerate(found_servers, 1):
                print(f"   {i}. {ip}")
            return found_servers[0]  # Return first found
        else:
            print("❌ No servers found")
            return None
            
    except Exception as e:
        print(f"❌ Network scan failed: {e}")
        return None

def main():
    print("=" * 60)
    print("🔗 LAN Communication Hub - Client Connection")
    print("=" * 60)
    print()
    print("Choose connection method:")
    print("1. Browser Override (Recommended - enables camera/mic)")
    print("2. Direct Connection (Simple - no camera/mic)")
    print("3. SSH Tunnel (Secure - enables camera/mic)")
    print("4. Auto-find Server")
    print()
    
    choice = input("Select method (1-4): ").strip()
    print()
    
    server_ip = None
    
    if choice == "4":
        server_ip = scan_local_network()
        if not server_ip:
            return
        choice = "1"  # Default to browser override
    else:
        server_ip = get_server_ip()
        if not server_ip:
            return
    
    print()
    
    if choice == "1":
        success = browser_override_connection(server_ip)
        if success:
            print("\n✅ Browser started with camera/microphone access!")
            print("📱 You can now use camera and microphone in the app")
    
    elif choice == "2":
        success = direct_connection(server_ip)
        if success:
            print("\n✅ Connected! Note: Camera/microphone may not work")
    
    elif choice == "3":
        success = ssh_tunnel_connection(server_ip)
        if success:
            print("\n✅ SSH tunnel established!")
            print("🌐 Access via: http://localhost:5000")
    
    else:
        print("❌ Invalid choice")
        return
    
    if choice in ["1", "2"]:
        print(f"\n🌐 Server URL: http://{server_ip}:5000")
        print("💡 If camera/microphone doesn't work, try SSH tunnel method")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Connection cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
