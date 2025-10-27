#!/usr/bin/env python3
"""
Test the dynamic IP detection and setup
"""

import socket
import subprocess
import sys

def test_ip_detection():
    """Test IP detection methods"""
    print("🧪 Testing Dynamic IP Detection")
    print("=" * 50)
    
    # Test method 1: External connection
    print("1️⃣ Testing external connection method...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        external_ip = s.getsockname()[0]
        s.close()
        print(f"   ✅ External method: {external_ip}")
    except Exception as e:
        print(f"   ❌ External method failed: {e}")
        external_ip = None
    
    # Test method 2: Network interfaces
    print("\n2️⃣ Testing network interface detection...")
    detected_ips = []
    
    commands = [
        (['hostname', '-I'], 'hostname -I'),
        (['ifconfig'], 'ifconfig'),
        (['ipconfig'], 'ipconfig')
    ]
    
    for cmd, name in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Extract private IPs
                import re
                ip_pattern = r'\b(?:192\.168\.|10\.|172\.(?:1[6-9]|2[0-9]|3[01])\.)\d{1,3}\.\d{1,3}\b'
                ips = re.findall(ip_pattern, result.stdout)
                if ips:
                    detected_ips.extend(ips)
                    print(f"   ✅ {name}: {ips}")
                else:
                    print(f"   ⚠️  {name}: No private IPs found")
            else:
                print(f"   ❌ {name}: Command failed")
        except Exception as e:
            print(f"   ❌ {name}: {e}")
    
    # Test method 3: Hostname resolution
    print("\n3️⃣ Testing hostname resolution...")
    try:
        hostname = socket.gethostname()
        hostname_ip = socket.gethostbyname(hostname)
        print(f"   ✅ Hostname ({hostname}): {hostname_ip}")
    except Exception as e:
        print(f"   ❌ Hostname resolution failed: {e}")
        hostname_ip = None
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DETECTION SUMMARY")
    print("=" * 50)
    
    all_ips = set()
    if external_ip:
        all_ips.add(external_ip)
    all_ips.update(detected_ips)
    if hostname_ip and hostname_ip != '127.0.0.1':
        all_ips.add(hostname_ip)
    
    if all_ips:
        print("✅ Detected IP addresses:")
        for ip in sorted(all_ips):
            print(f"   • {ip}")
        
        # Recommend best IP
        private_ips = [ip for ip in all_ips if ip.startswith(('192.168.', '10.', '172.'))]
        if private_ips:
            recommended = private_ips[0]
            print(f"\n🎯 Recommended server IP: {recommended}")
        else:
            recommended = list(all_ips)[0]
            print(f"\n🎯 Best available IP: {recommended}")
            
        return recommended
    else:
        print("❌ No suitable IP addresses detected")
        print("💡 Will fallback to localhost")
        return "localhost"

def test_network_scan():
    """Test network scanning for servers"""
    print("\n🔍 Testing Network Scanning")
    print("=" * 50)
    
    # Get local IP first
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        print(f"Local IP: {local_ip}")
        
        # Get network base
        ip_parts = local_ip.split('.')
        network_base = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
        
        print(f"Scanning network: {network_base}.0/24")
        
        # Quick scan for port 5000
        active_hosts = []
        test_ips = [1, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        
        for last_octet in test_ips:
            test_ip = f"{network_base}.{last_octet}"
            if test_ip != local_ip:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((test_ip, 5000))
                    sock.close()
                    
                    if result == 0:
                        active_hosts.append(test_ip)
                        print(f"   ✅ Found server at: {test_ip}")
                except:
                    pass
        
        if active_hosts:
            print(f"\n✅ Found {len(active_hosts)} potential servers")
        else:
            print("\n⚠️  No servers found on port 5000")
            
        return active_hosts
        
    except Exception as e:
        print(f"❌ Network scan failed: {e}")
        return []

def main():
    """Main test function"""
    print("🧪 DYNAMIC SETUP TEST")
    print("=" * 60)
    
    # Test IP detection
    detected_ip = test_ip_detection()
    
    # Test network scanning
    servers = test_network_scan()
    
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS")
    print("=" * 60)
    
    print(f"✅ IP Detection: {detected_ip}")
    print(f"✅ Network Scan: {len(servers)} servers found")
    
    if detected_ip != "localhost":
        print("\n✅ Dynamic setup should work correctly!")
        print(f"   Server IP: {detected_ip}")
        print(f"   Clients can auto-detect and connect")
    else:
        print("\n⚠️  Limited IP detection")
        print("   Manual IP entry may be required")
    
    print(f"\n📋 Next Steps:")
    print(f"1. Run: python3 start_server.py")
    print(f"2. Check detected IP matches: {detected_ip}")
    print(f"3. Run: python3 connect_client.py (on other machines)")
    print(f"4. Verify auto-detection works")

if __name__ == "__main__":
    main()