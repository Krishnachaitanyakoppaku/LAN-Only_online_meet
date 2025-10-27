#!/usr/bin/env python3
"""
Test the HTTPS solution for camera/microphone access
"""

import requests
import urllib3
import socket

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_https_solution():
    print("🔒 Testing HTTPS Solution for Camera/Microphone Access")
    print("=" * 60)
    
    # Get server IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        server_ip = s.getsockname()[0]
        s.close()
    except:
        server_ip = "localhost"
    
    print(f"🌐 Server IP: {server_ip}")
    print()
    
    # Test HTTPS connectivity
    print("1️⃣ Testing HTTPS connectivity...")
    https_urls = [
        f"https://{server_ip}:5000",
        "https://localhost:5000"
    ]
    
    https_working = False
    for url in https_urls:
        try:
            response = requests.get(url, verify=False, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ HTTPS working: {url}")
                https_working = True
                break
            else:
                print(f"   ❌ HTTPS failed: {url} (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ HTTPS connection refused: {url}")
        except requests.exceptions.Timeout:
            print(f"   ❌ HTTPS timeout: {url}")
        except Exception as e:
            print(f"   ❌ HTTPS error: {url} ({e})")
    
    # Test HTTP fallback
    print("\n2️⃣ Testing HTTP fallback...")
    http_urls = [
        f"http://{server_ip}:5000",
        "http://localhost:5000"
    ]
    
    http_working = False
    for url in http_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ HTTP working: {url}")
                http_working = True
                break
            else:
                print(f"   ❌ HTTP failed: {url} (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ HTTP connection refused: {url}")
        except requests.exceptions.Timeout:
            print(f"   ❌ HTTP timeout: {url}")
        except Exception as e:
            print(f"   ❌ HTTP error: {url} ({e})")
    
    # Check SSL dependencies
    print("\n3️⃣ Checking SSL dependencies...")
    try:
        import ssl
        print("   ✅ SSL module available")
    except ImportError:
        print("   ❌ SSL module not available")
    
    try:
        import OpenSSL
        print("   ✅ pyOpenSSL available")
    except ImportError:
        print("   ❌ pyOpenSSL not available")
        print("   💡 Install with: pip install pyOpenSSL")
    
    # Summary and recommendations
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    if https_working:
        print("✅ HTTPS Solution: WORKING")
        print(f"   Clients should use: https://{server_ip}:5000")
        print("   Camera/microphone will work on all machines!")
        print("   Note: Browser will show security warning (click 'Proceed')")
    elif http_working:
        print("⚠️  HTTPS Solution: NOT WORKING")
        print("   HTTP fallback is available")
        print("   Camera/microphone may not work on remote clients")
        print("   Consider SSH tunnel solution for clients")
    else:
        print("❌ Both HTTPS and HTTP: NOT WORKING")
        print("   Server may not be running")
        print("   Start server with: python3 start_server.py")
    
    print(f"\n🎯 RECOMMENDED URLS:")
    if https_working:
        print(f"   Host: https://localhost:5000")
        print(f"   Clients: https://{server_ip}:5000")
    else:
        print(f"   Host: http://localhost:5000")
        print(f"   Clients: SSH tunnel → http://localhost:5000")

def show_https_benefits():
    print("\n" + "=" * 60)
    print("🔒 HTTPS SOLUTION BENEFITS")
    print("=" * 60)
    
    print("✅ ADVANTAGES:")
    print("• No SSH tunnel setup needed")
    print("• Direct connection from any machine")
    print("• Camera/microphone works immediately")
    print("• Same URL for all users")
    print("• No network configuration")
    print("• Works across different networks")
    print()
    
    print("⚠️  CONSIDERATIONS:")
    print("• Browser shows security warning (self-signed cert)")
    print("• Users need to click 'Advanced' → 'Proceed'")
    print("• One-time setup per browser")
    print()
    
    print("🆚 HTTPS vs SSH Tunnel:")
    print("HTTPS:")
    print("  ✅ Simpler for users")
    print("  ✅ No command line needed")
    print("  ⚠️  Browser security warning")
    print()
    print("SSH Tunnel:")
    print("  ✅ No browser warnings")
    print("  ✅ More secure")
    print("  ❌ Requires command line")
    print("  ❌ More complex setup")

if __name__ == "__main__":
    test_https_solution()
    show_https_benefits()