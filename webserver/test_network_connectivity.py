#!/usr/bin/env python3
"""
Test network connectivity between specific IP addresses
"""

import socket
import requests
import subprocess
import time

def test_connectivity():
    client_ip = "172.17.222.34"
    server_ip = "172.17.213.107"
    server_port = 5000
    
    print("🌐 Network Connectivity Test")
    print("=" * 50)
    print(f"Client IP: {client_ip}")
    print(f"Server IP: {server_ip}")
    print(f"Server Port: {server_port}")
    print()
    
    # Test 1: Basic ping connectivity
    print("1️⃣ Testing ping connectivity...")
    try:
        result = subprocess.run(['ping', '-c', '3', server_ip], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Ping successful - IPs can reach each other")
            # Extract ping time
            lines = result.stdout.split('\n')
            for line in lines:
                if 'time=' in line:
                    print(f"   Sample ping time: {line.split('time=')[1].split()[0]}")
                    break
        else:
            print("❌ Ping failed - network connectivity issue")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Ping timeout - server may be unreachable")
        return False
    except Exception as e:
        print(f"❌ Ping test failed: {e}")
        return False
    
    # Test 2: Port connectivity
    print(f"\n2️⃣ Testing port {server_port} connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((server_ip, server_port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {server_port} is open and accessible")
        else:
            print(f"❌ Port {server_port} is not accessible")
            print("   Possible causes:")
            print("   - Server is not running")
            print("   - Firewall blocking the port")
            print("   - Server not listening on all interfaces")
            return False
    except Exception as e:
        print(f"❌ Port test failed: {e}")
        return False
    
    # Test 3: HTTP connectivity
    print(f"\n3️⃣ Testing HTTP connectivity...")
    try:
        response = requests.get(f'http://{server_ip}:{server_port}', timeout=10)
        print(f"✅ HTTP connection successful (Status: {response.status_code})")
    except requests.exceptions.ConnectTimeout:
        print("❌ HTTP connection timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ HTTP connection refused")
        return False
    except Exception as e:
        print(f"❌ HTTP test failed: {e}")
        return False
    
    # Test 4: Server API connectivity
    print(f"\n4️⃣ Testing server API...")
    try:
        response = requests.get(f'http://{server_ip}:{server_port}/api/server-info', timeout=10)
        server_info = response.json()
        print(f"✅ Server API accessible")
        print(f"   Server reports IP: {server_info['server_ip']}")
        print(f"   Server port: {server_info['server_port']}")
        print(f"   UDP port: {server_info['udp_port']}")
    except Exception as e:
        print(f"❌ Server API test failed: {e}")
        return False
    
    # Test 5: Session debug endpoint
    print(f"\n5️⃣ Testing session management...")
    try:
        response = requests.get(f'http://{server_ip}:{server_port}/api/debug/sessions', timeout=10)
        debug_info = response.json()
        print(f"✅ Session management accessible")
        print(f"   Active sessions: {debug_info['total_sessions']}")
        print(f"   Connected users: {debug_info['total_users']}")
        
        if debug_info['active_sessions']:
            print("   📋 Available sessions:")
            for session_id, session_data in debug_info['active_sessions'].items():
                print(f"      • {session_id}: Host={session_data['host']}, Users={session_data['user_count']}")
        else:
            print("   ⚠️  No active sessions (host needs to create one)")
            
    except Exception as e:
        print(f"❌ Session management test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 CONNECTIVITY SUMMARY")
    print("=" * 50)
    print("✅ All connectivity tests passed!")
    print(f"✅ Client {client_ip} CAN connect to server {server_ip}:{server_port}")
    print()
    print("📝 Next steps:")
    print(f"1. Host: Go to http://{server_ip}:{server_port} and create a session")
    print(f"2. Client: Go to http://{server_ip}:{server_port} and join with session ID")
    print(f"3. Session ID will likely be: {server_ip}")
    
    return True

def check_network_class():
    """Check if IPs are in the same network class"""
    client_ip = "172.17.222.34"
    server_ip = "172.17.213.107"
    
    print("\n🔍 Network Analysis:")
    print("-" * 30)
    
    # Parse IPs
    client_parts = client_ip.split('.')
    server_parts = server_ip.split('.')
    
    print(f"Client: {client_ip}")
    print(f"Server: {server_ip}")
    print()
    
    # Check network classes
    if client_parts[0] == server_parts[0] and client_parts[1] == server_parts[1]:
        print("✅ Same /16 network (172.17.0.0/16)")
        if client_parts[2] == server_parts[2]:
            print("✅ Same /24 subnet")
        else:
            print("ℹ️  Different /24 subnets but same /16 network")
            print("   Should still be routable if network is configured properly")
    else:
        print("⚠️  Different networks - may need routing")
    
    print(f"\nNetwork details:")
    print(f"  Client subnet: 172.17.{client_parts[2]}.0/24")
    print(f"  Server subnet: 172.17.{server_parts[2]}.0/24")

if __name__ == "__main__":
    check_network_class()
    print()
    test_connectivity()