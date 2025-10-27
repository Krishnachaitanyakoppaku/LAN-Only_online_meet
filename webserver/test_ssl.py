#!/usr/bin/env python3
"""
Quick test for SSL certificate generation
"""

from ssl_helper import create_simple_cert, get_local_ip
import os

def test_ssl():
    print("Testing SSL certificate generation...")
    
    # Get server IP
    server_ip = get_local_ip()
    print(f"Server IP: {server_ip}")
    
    # Try to create certificate using Python method
    cert_file, key_file = create_simple_cert()
    
    if cert_file and key_file:
        print(f"✅ SSL Certificate generated successfully!")
        print(f"   Certificate: {cert_file}")
        print(f"   Private Key: {key_file}")
        
        # Check if files exist
        if os.path.exists(cert_file) and os.path.exists(key_file):
            print(f"✅ Certificate files exist and are ready to use")
            return cert_file, key_file
        else:
            print(f"❌ Certificate files not found")
            return None, None
    else:
        print(f"❌ Failed to generate SSL certificate")
        return None, None

if __name__ == "__main__":
    test_ssl()