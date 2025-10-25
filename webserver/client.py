#!/usr/bin/env python3
"""
LAN Meeting Web Client - Client Only
Opens client browser to connect to server
"""

import webbrowser
import sys
import time

def main():
    print("👥 LAN Meeting Web Client")
    print("=" * 40)
    
    # Get server IP from user
    server_ip = input("Enter server IP address (or press Enter for localhost): ").strip()
    
    if not server_ip:
        server_ip = "localhost"
    
    port = 5000
    client_url = f"http://{server_ip}:{port}/client"
    
    print(f"🌐 Connecting to: {client_url}")
    print("🚀 Opening client interface...")
    
    try:
        # Open client interface in browser
        webbrowser.open(client_url)
        print("✅ Client interface opened in browser")
        print("💡 If browser didn't open, manually visit:")
        print(f"   {client_url}")
        
    except Exception as e:
        print(f"❌ Error opening browser: {e}")
        print("💡 Please manually open your browser and visit:")
        print(f"   {client_url}")

if __name__ == '__main__':
    main()