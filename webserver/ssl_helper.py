#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSL Certificate Helper for HTTPS server
Generates self-signed certificates dynamically
"""

import os
import socket
import subprocess
import sys
from datetime import datetime, timedelta
import datetime as dt

def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

def create_ssl_certificate(server_ip="localhost"):
    """Create a self-signed SSL certificate for the server IP"""
    cert_dir = os.path.join(os.path.dirname(__file__), 'ssl_certs')
    cert_file = os.path.join(cert_dir, 'server.crt')
    key_file = os.path.join(cert_dir, 'server.key')
    
    # Create directory if it doesn't exist
    os.makedirs(cert_dir, exist_ok=True)
    
    # Check if certificates already exist and are valid
    if os.path.exists(cert_file) and os.path.exists(key_file):
        try:
            # Check if certificate is still valid (not expired)
            result = subprocess.run([
                'openssl', 'x509', '-in', cert_file, '-noout', '-dates'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"SSL: Using existing certificate for {server_ip}")
                return cert_file, key_file
        except:
            pass
    
    print(f"SSL: Generating new certificate for {server_ip}...")
    
    try:
        # Generate private key
        subprocess.run([
            'openssl', 'genrsa', '-out', key_file, '2048'
        ], check=True, capture_output=True, timeout=30)
        
        # Create certificate signing request config
        config_content = f"""[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = Local
L = Local
O = LAN Meeting Server
CN = {server_ip}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = {server_ip}
IP.1 = 127.0.0.1
IP.2 = {server_ip}
"""
        
        config_file = os.path.join(cert_dir, 'cert.conf')
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        # Generate certificate
        subprocess.run([
            'openssl', 'req', '-new', '-x509', '-key', key_file,
            '-out', cert_file, '-days', '365', '-config', config_file,
            '-extensions', 'v3_req'
        ], check=True, capture_output=True, timeout=30)
        
        print(f"SSL: Certificate generated successfully")
        return cert_file, key_file
        
    except subprocess.CalledProcessError as e:
        print(f"SSL: OpenSSL command failed: {e}")
        return None, None
    except subprocess.TimeoutExpired:
        print("SSL: Certificate generation timed out")
        return None, None
    except Exception as e:
        print(f"SSL: Certificate generation error: {e}")
        return None, None

def check_openssl():
    """Check if OpenSSL is available"""
    try:
        result = subprocess.run(['openssl', 'version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"SSL: OpenSSL found - {result.stdout.strip()}")
            return True
    except:
        pass
    
    print("SSL: OpenSSL not found")
    return False

def install_openssl_windows():
    """Try to install OpenSSL on Windows"""
    print("SSL: Attempting to install OpenSSL...")
    
    # Try chocolatey first
    try:
        result = subprocess.run(['choco', 'install', 'openssl', '-y'], 
                              capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("SSL: OpenSSL installed via Chocolatey")
            return True
    except:
        pass
    
    # Try winget
    try:
        result = subprocess.run(['winget', 'install', 'OpenSSL.Light'], 
                              capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("SSL: OpenSSL installed via winget")
            return True
    except:
        pass
    
    print("SSL: Could not install OpenSSL automatically")
    print("SSL: Please install OpenSSL manually:")
    print("SSL: 1. Install Chocolatey: https://chocolatey.org/install")
    print("SSL: 2. Run: choco install openssl")
    print("SSL: Or download from: https://slproweb.com/products/Win32OpenSSL.html")
    
    return False

def get_ssl_context(server_ip=None):
    """Get SSL context for Flask-SocketIO"""
    if server_ip is None:
        server_ip = get_local_ip()
    
    # Try OpenSSL first if available
    if check_openssl():
        print("SSL: Using OpenSSL for certificate generation")
        cert_file, key_file = create_ssl_certificate(server_ip)
        if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
            return (cert_file, key_file)
    
    # Fall back to Python cryptography method
    print("SSL: Using Python cryptography for certificate generation")
    cert_file, key_file = create_simple_cert()
    
    if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
        return (cert_file, key_file)
    else:
        print("SSL: All certificate generation methods failed")
        return None

def create_simple_cert():
    """Create a simple certificate using Python's built-in ssl module"""
    try:
        import ssl
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import ipaddress
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Get server IP
        server_ip = get_local_ip()
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "LAN Meeting Server"),
            x509.NameAttribute(NameOID.COMMON_NAME, server_ip),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(dt.timezone.utc)
        ).not_valid_after(
            datetime.now(dt.timezone.utc) + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName(server_ip),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv4Address(server_ip)),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Save to files
        cert_dir = os.path.join(os.path.dirname(__file__), 'ssl_certs')
        os.makedirs(cert_dir, exist_ok=True)
        
        cert_file = os.path.join(cert_dir, 'server.crt')
        key_file = os.path.join(cert_dir, 'server.key')
        
        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"SSL: Certificate created using Python cryptography for {server_ip}")
        return cert_file, key_file
        
    except ImportError:
        print("SSL: cryptography module not available")
        return None, None
    except Exception as e:
        print(f"SSL: Python certificate generation failed: {e}")
        return None, None

if __name__ == "__main__":
    # Test certificate generation
    server_ip = get_local_ip()
    print(f"Testing SSL certificate generation for {server_ip}")
    
    ssl_context = get_ssl_context(server_ip)
    if ssl_context:
        print(f"SSL: Success! Certificate files: {ssl_context}")
    else:
        print("SSL: Failed to generate certificate")
        
        # Try Python method
        cert_file, key_file = create_simple_cert()
        if cert_file and key_file:
            print(f"SSL: Python method success! Files: {cert_file}, {key_file}")
        else:
            print("SSL: All methods failed")