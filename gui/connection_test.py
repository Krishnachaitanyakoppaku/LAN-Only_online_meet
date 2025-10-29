#!/usr/bin/env python3
"""
Connection Test Tool for GUI LAN Communication
Tests network connectivity between client and server
"""

import socket
import sys
import time
import threading

def test_tcp_connection(host, port, timeout=5):
    """Test TCP connection to server."""
    print(f"Testing TCP connection to {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ TCP connection successful to {host}:{port}")
            return True
        else:
            print(f"❌ TCP connection failed to {host}:{port} (Error: {result})")
            return False
            
    except Exception as e:
        print(f"❌ TCP connection error: {e}")
        return False

def test_udp_connection(host, video_port, audio_port):
    """Test UDP connection for video/audio."""
    print(f"Testing UDP connections to {host}...")
    
    # Test video port
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        sock.sendto(b"test", (host, video_port))
        sock.close()
        print(f"✅ UDP video port {video_port} reachable")
        video_ok = True
    except Exception as e:
        print(f"❌ UDP video port {video_port} failed: {e}")
        video_ok = False
    
    # Test audio port
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        sock.sendto(b"test", (host, audio_port))
        sock.close()
        print(f"✅ UDP audio port {audio_port} reachable")
        audio_ok = True
    except Exception as e:
        print(f"❌ UDP audio port {audio_port} failed: {e}")
        audio_ok = False
    
    return video_ok and audio_ok

def scan_for_servers(base_ip="192.168.1", tcp_port=9000):
    """Scan local network for servers."""
    print(f"Scanning for servers on {base_ip}.x:{tcp_port}...")
    
    found_servers = []
    
    def check_ip(ip):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, tcp_port))
            sock.close()
            if result == 0:
                found_servers.append(ip)
                print(f"✅ Found server at {ip}:{tcp_port}")
        except:
            pass
    
    # Test common IPs
    threads = []
    for i in range(1, 255):
        ip = f"{base_ip}.{i}"
        thread = threading.Thread(target=check_ip, args=(ip,))
        thread.start()
        threads.append(thread)
        
        # Limit concurrent threads
        if len(threads) >= 50:
            for t in threads:
                t.join()
            threads = []
    
    # Wait for remaining threads
    for t in threads:
        t.join()
    
    return found_servers

def get_local_ip():
    """Get local machine IP."""
    try:
        # Connect to external server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

def main():
    print("🔍 LAN Communication Connection Test")
    print("=" * 50)
    
    # Get local IP
    local_ip = get_local_ip()
    print(f"Your IP: {local_ip}")
    print()
    
    # Get server details
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    else:
        server_ip = input("Enter server IP (or press Enter to scan): ").strip()
    
    if not server_ip:
        print("Scanning for servers...")
        base_ip = ".".join(local_ip.split(".")[:-1])
        found_servers = scan_for_servers(base_ip)
        
        if found_servers:
            print(f"\nFound {len(found_servers)} server(s):")
            for i, ip in enumerate(found_servers, 1):
                print(f"  {i}. {ip}")
            
            choice = input("\nSelect server (1-{}) or enter IP: ".format(len(found_servers))).strip()
            
            try:
                server_ip = found_servers[int(choice) - 1]
            except:
                server_ip = choice
        else:
            print("No servers found. Please enter IP manually.")
            server_ip = input("Server IP: ").strip()
    
    if not server_ip:
        print("No server IP provided. Exiting.")
        return
    
    print(f"\nTesting connection to {server_ip}...")
    print("-" * 30)
    
    # Test TCP (main control)
    tcp_ok = test_tcp_connection(server_ip, 9000)
    
    # Test UDP (video/audio)
    udp_ok = test_udp_connection(server_ip, 10000, 11000)
    
    print("\n" + "=" * 50)
    print("CONNECTION TEST RESULTS")
    print("=" * 50)
    
    if tcp_ok:
        print("✅ TCP Control Connection: OK")
    else:
        print("❌ TCP Control Connection: FAILED")
        print("   - Check if server is running")
        print("   - Check firewall settings")
        print("   - Verify server IP address")
    
    if udp_ok:
        print("✅ UDP Media Connections: OK")
    else:
        print("❌ UDP Media Connections: FAILED")
        print("   - Video/audio may not work properly")
        print("   - Check firewall UDP settings")
    
    if tcp_ok and udp_ok:
        print("\n🎉 All connections successful!")
        print(f"You can connect to server at: {server_ip}")
    elif tcp_ok:
        print("\n⚠️  Basic connection works, but media may have issues")
    else:
        print("\n❌ Connection failed. Check server and network settings.")
    
    print("\n💡 Troubleshooting tips:")
    print("   1. Make sure server is running: python main_server.py")
    print("   2. Check firewall allows ports 9000, 10000, 11000")
    print("   3. Verify you're on the same network")
    print("   4. Try 'localhost' if server is on same machine")

if __name__ == "__main__":
    main()