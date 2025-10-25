#!/usr/bin/env python3
"""
LAN Meeting Client Launcher
Simple tool to join meetings by entering server IP
"""

import webbrowser
import socket
import time
import sys
import os
from urllib.parse import urlparse
import requests

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print welcome banner"""
    print("🎥 LAN Meeting - Client Launcher")
    print("=" * 40)
    print("✅ Join meetings easily!")
    print("🌐 Just enter the server IP address")
    print("📱 Works on any device with a browser")
    print()

def validate_ip(ip):
    """Validate IP address format"""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def test_connection(server_ip, port=5000, timeout=5):
    """Test if server is reachable"""
    try:
        # Test HTTP connection
        response = requests.get(f"http://{server_ip}:{port}/api/status", timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        try:
            # Fallback: test socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((server_ip, port))
            sock.close()
            return result == 0
        except:
            return False

def get_server_info(server_ip, port=5000):
    """Get server information"""
    try:
        response = requests.get(f"http://{server_ip}:{port}/api/status", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return {
                'participants': data.get('participants', 0),
                'host_video': data.get('host_video', False),
                'host_screen_sharing': data.get('host_screen_sharing', False)
            }
    except:
        pass
    return None

def open_meeting_browser(server_ip, port=5000):
    """Open browser with meeting interface"""
    meeting_url = f"http://{server_ip}:{port}/client"
    
    print(f"🚀 Opening meeting in browser...")
    print(f"📍 Meeting URL: {meeting_url}")
    
    try:
        webbrowser.open(meeting_url)
        return True
    except Exception as e:
        print(f"❌ Could not open browser automatically: {e}")
        print(f"📋 Please open your browser manually and go to:")
        print(f"   {meeting_url}")
        return False

def main():
    """Main client launcher"""
    clear_screen()
    print_banner()
    
    while True:
        try:
            # Get server IP from user
            print("🌐 Enter Server Information:")
            server_input = input("Server IP Address (or 'quit' to exit): ").strip()
            
            if server_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                sys.exit(0)
            
            if not server_input:
                print("❌ Please enter a server IP address")
                continue
            
            # Handle different input formats
            server_ip = server_input
            port = 5000
            
            # Check if port is specified
            if ':' in server_input:
                try:
                    server_ip, port_str = server_input.split(':')
                    port = int(port_str)
                except ValueError:
                    print("❌ Invalid format. Use: IP:PORT or just IP")
                    continue
            
            # Validate IP address
            if not validate_ip(server_ip):
                print("❌ Invalid IP address format")
                print("💡 Examples: 192.168.1.100, 10.0.0.5, 172.16.1.10")
                continue
            
            print(f"🔍 Testing connection to {server_ip}:{port}...")
            
            # Test connection
            if not test_connection(server_ip, port):
                print(f"❌ Cannot connect to server at {server_ip}:{port}")
                print("🔧 Troubleshooting:")
                print("   • Make sure the server is running")
                print("   • Check if you're on the same network")
                print("   • Verify the IP address is correct")
                print("   • Try a different port if specified")
                print()
                
                retry = input("🔄 Try again? (y/n): ").strip().lower()
                if retry not in ['y', 'yes']:
                    continue
                else:
                    print()
                    continue
            
            print("✅ Server is reachable!")
            
            # Get server info
            server_info = get_server_info(server_ip, port)
            if server_info:
                print(f"📊 Meeting Status:")
                print(f"   👥 Participants: {server_info['participants']}")
                print(f"   📹 Host Video: {'On' if server_info['host_video'] else 'Off'}")
                print(f"   🖥️ Screen Sharing: {'Active' if server_info['host_screen_sharing'] else 'Inactive'}")
            
            print()
            
            # Confirm joining
            join_confirm = input("🚀 Join this meeting? (y/n): ").strip().lower()
            if join_confirm not in ['y', 'yes']:
                print("❌ Cancelled")
                continue
            
            # Open browser
            if open_meeting_browser(server_ip, port):
                print("✅ Browser opened successfully!")
                print()
                print("📋 Next Steps:")
                print("1. Enter your name in the browser")
                print("2. Choose your camera/microphone settings")
                print("3. Click 'Join Meeting'")
                print("4. Enjoy your meeting! 🎉")
                print()
                
                # Ask if user wants to join another meeting
                another = input("🔄 Join another meeting? (y/n): ").strip().lower()
                if another not in ['y', 'yes']:
                    print("👋 Happy meeting!")
                    break
                else:
                    clear_screen()
                    print_banner()
                    continue
            else:
                print("⚠️ Please open the browser manually")
                continue
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("🔄 Please try again")
            continue

def quick_join(server_ip):
    """Quick join function for command line usage"""
    print(f"🚀 Quick joining meeting at {server_ip}...")
    
    if not validate_ip(server_ip):
        print("❌ Invalid IP address")
        return False
    
    if not test_connection(server_ip):
        print(f"❌ Cannot connect to {server_ip}")
        return False
    
    return open_meeting_browser(server_ip)

if __name__ == "__main__":
    # Check for command line argument
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
        if quick_join(server_ip):
            print("✅ Browser opened! Enjoy your meeting!")
        else:
            print("❌ Failed to join meeting")
    else:
        main()