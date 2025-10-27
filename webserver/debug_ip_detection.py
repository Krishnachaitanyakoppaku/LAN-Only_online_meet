#!/usr/bin/env python3
"""
Debug IP detection issue
"""

import requests
import socket
import subprocess

def debug_ip_detection():
    print("🔍 Debugging IP Detection Issue")
    print("=" * 50)
    
    # Test what the server reports as its IP
    print("1️⃣ Checking what server reports as its IP...")
    try:
        response = requests.get('http://172.17.213.107:5000/api/server-info')
        server_info = response.json()
        reported_ip = server_info['server_ip']
        print(f"   Server reports IP: {reported_ip}")
        
        if reported_ip == "172.17.213.107":
            print("   ✅ Server correctly reports its IP")
        elif reported_ip == "172.17.222.34":
            print("   ❌ BUG: Server is reporting client IP instead of server IP!")
        else:
            print(f"   ⚠️  Server reports unexpected IP: {reported_ip}")
            
    except Exception as e:
        print(f"   ❌ Failed to get server info: {e}")
        return
    
    # Test the get_host_ip function locally
    print("\n2️⃣ Testing get_host_ip function locally...")
    
    def get_host_ip():
        try:
            # First try to get the IP that other computers can access
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            print(f"   Socket method detected: {local_ip}")
            
            # Check if this is a local/private IP that other computers can access
            if local_ip.startswith(('192.168.', '10.', '172.')):
                print(f"   ✅ Network IP detected: {local_ip}")
                return local_ip
            else:
                print(f"   ⚠️  Public IP detected, trying to find local network IP...")
                # Try to get the actual network interface IP
                try:
                    # Try hostname -I (Linux/Mac)
                    result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        ips = result.stdout.strip().split()
                        print(f"   hostname -I returned: {ips}")
                        for ip in ips:
                            if ip.startswith(('192.168.', '10.', '172.')):
                                print(f"   ✅ Network IP from hostname: {ip}")
                                return ip
                                
                except Exception as e:
                    print(f"   ❌ Error running network commands: {e}")
                
                print(f"   Using detected IP: {local_ip}")
                return local_ip
                
        except Exception as e:
            print(f"   ❌ Failed to detect IP, using localhost: {e}")
            return "localhost"
    
    local_detected_ip = get_host_ip()
    print(f"   Local detection result: {local_detected_ip}")
    
    # Compare results
    print(f"\n3️⃣ Comparison:")
    print(f"   Expected server IP: 172.17.213.107")
    print(f"   Server reports: {reported_ip}")
    print(f"   Local detection: {local_detected_ip}")
    
    if reported_ip != "172.17.213.107":
        print(f"\n🐛 BUG IDENTIFIED:")
        print(f"   The server is not correctly detecting its own IP address!")
        print(f"   It should be: 172.17.213.107")
        print(f"   But it reports: {reported_ip}")
        print(f"\n💡 SOLUTION:")
        print(f"   The server needs to be configured with the correct IP address")
        print(f"   Or the IP detection logic needs to be fixed")

if __name__ == "__main__":
    debug_ip_detection()