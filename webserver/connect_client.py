#!/usr/bin/env python3
"""
Simple client connection script with SSH tunnel
"""

import subprocess
import sys
import os
import socket

def scan_network_for_servers():
    """Scan local network for potential servers"""
    try:
        # Get local network IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Get network base (e.g., 192.168.1.0/24)
        ip_parts = local_ip.split('.')
        network_base = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
        
        print(f"💻 Your IP: {local_ip}")
        print(f"🔍 Scanning network {network_base}.0/24 for servers...")
        
        # Quick scan for common server ports
        potential_servers = []
        
        # Check a few common IPs in the network
        for last_octet in [1, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]:
            test_ip = f"{network_base}.{last_octet}"
            if test_ip != local_ip:  # Don't test our own IP
                if test_server_connection(test_ip):
                    potential_servers.append(test_ip)
        
        return local_ip, potential_servers
        
    except Exception as e:
        print(f"Network scan failed: {e}")
        return None, []

def test_server_connection(ip, port=5000, timeout=1):
    """Test if a server is running on given IP:port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def get_server_ip():
    """Get server IP from user or detect"""
    print("🔍 LAN Communication Hub - Client Connection")
    print("=" * 50)
    
    # Scan network for servers
    local_ip, potential_servers = scan_network_for_servers()
    
    if potential_servers:
        print(f"✅ Found potential servers:")
        for i, server_ip in enumerate(potential_servers, 1):
            print(f"   {i}. {server_ip}")
        print()
        
        if len(potential_servers) == 1:
            suggested_ip = potential_servers[0]
            print(f"🎯 Auto-detected server: {suggested_ip}")
        else:
            print("Multiple servers found. Please select one:")
            try:
                choice = int(input(f"Enter choice (1-{len(potential_servers)}): ")) - 1
                if 0 <= choice < len(potential_servers):
                    suggested_ip = potential_servers[choice]
                else:
                    suggested_ip = potential_servers[0]
            except:
                suggested_ip = potential_servers[0]
    else:
        # Fallback: ask user to enter manually
        if local_ip:
            ip_parts = local_ip.split('.')
            suggested_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"  # Try gateway
            print(f"❌ No servers auto-detected")
            print(f"🎯 Suggested (gateway): {suggested_ip}")
        else:
            suggested_ip = "192.168.1.1"
            print(f"❌ Network detection failed")
            print(f"🎯 Default suggestion: {suggested_ip}")
    
    print()
    server_ip = input(f"Enter server IP address (default: {suggested_ip}): ").strip()
    
    if not server_ip:
        server_ip = suggested_ip
    
    return server_ip

def get_username(server_ip):
    """Get username for SSH connection"""
    print(f"\n🔐 SSH Connection to {server_ip}")
    
    # Try to get current username as default
    import getpass
    current_user = getpass.getuser()
    
    username = input(f"Enter SSH username (default: {current_user}): ").strip()
    
    if not username:
        username = current_user
    
    return username

def test_ssh_connection(username, server_ip):
    """Test SSH connection before setting up tunnel"""
    print(f"\n🧪 Testing SSH connection to {username}@{server_ip}...")
    
    try:
        # Test SSH connection with a simple command
        result = subprocess.run([
            'ssh', '-o', 'ConnectTimeout=5', '-o', 'BatchMode=yes',
            f'{username}@{server_ip}', 'echo "SSH connection test successful"'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ SSH connection test successful")
            return True
        else:
            print("❌ SSH connection test failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ SSH connection timeout")
        return False
    except Exception as e:
        print(f"❌ SSH test error: {e}")
        return False

def setup_ssh_tunnel(username, server_ip):
    """Setup SSH tunnel for client access"""
    print(f"\n🔗 Setting up SSH tunnel...")
    print(f"   Server: {server_ip}")
    print(f"   Username: {username}")
    print(f"   Local access: http://localhost:5000")
    print()
    print("📋 Instructions after tunnel is established:")
    print("   1. Keep this terminal window open")
    print("   2. Open browser and go to: http://localhost:5000")
    print("   3. Join session with session ID: " + server_ip)
    print("   4. You should now have camera/microphone access!")
    print()
    print("🔌 Press Ctrl+C to close tunnel when done")
    print("=" * 50)
    
    try:
        # Setup SSH tunnel
        cmd = ['ssh', '-L', f'5000:{server_ip}:5000', f'{username}@{server_ip}']
        print(f"Running: {' '.join(cmd)}")
        print()
        
        # Run SSH tunnel
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🔌 SSH tunnel closed by user")
    except Exception as e:
        print(f"\n❌ SSH tunnel error: {e}")
        print()
        print("💡 Troubleshooting:")
        print("   - Make sure SSH is installed")
        print(f"   - Test manual connection: ssh {username}@{server_ip}")
        print("   - Check if server is reachable")
        print("   - Verify username and server IP are correct")

def show_alternative_methods(server_ip):
    """Show alternative connection methods"""
    print("\n🔧 Alternative Connection Methods:")
    print("=" * 50)
    
    print("Method 1: Direct Connection (may not work for camera/microphone)")
    print(f"   URL: http://{server_ip}:5000")
    print()
    
    print("Method 2: Manual SSH Tunnel")
    print(f"   Command: ssh -L 5000:{server_ip}:5000 username@{server_ip}")
    print("   Then access: http://localhost:5000")
    print()
    
    print("Method 3: HTTPS (if available)")
    print(f"   URL: https://{server_ip}:5000")
    print()

def main():
    """Main client connection function"""
    try:
        # Get server details
        server_ip = get_server_ip()
        username = get_username(server_ip)
        
        # Test SSH connection
        if not test_ssh_connection(username, server_ip):
            print("\n⚠️  SSH connection test failed")
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response != 'y':
                print("❌ Connection cancelled")
                show_alternative_methods(server_ip)
                return 1
        
        # Setup SSH tunnel
        setup_ssh_tunnel(username, server_ip)
        
    except KeyboardInterrupt:
        print("\n👋 Connection cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())