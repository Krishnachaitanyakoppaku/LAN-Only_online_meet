#!/usr/bin/env python3
"""
Install only essential dependencies for HTTPS functionality
"""

import subprocess
import sys
import os

def install_essential_packages():
    """Install only the essential packages needed for HTTPS"""
    print("📦 Installing Essential Packages for HTTPS Support")
    print("=" * 60)
    
    essential_packages = [
        "Flask>=2.0.0",
        "Flask-SocketIO>=5.0.0", 
        "python-socketio>=5.0.0",
        "python-engineio>=4.0.0",
        "pyOpenSSL>=23.0.0",
        "requests>=2.25.0"
    ]
    
    print("Installing packages:")
    for package in essential_packages:
        print(f"  • {package}")
    print()
    
    try:
        # Upgrade pip first
        print("🔄 Upgrading pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True, capture_output=True)
        
        # Install essential packages one by one
        for package in essential_packages:
            print(f"📥 Installing {package.split('>=')[0]}...")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Failed to install {package}")
                print(f"Error: {result.stderr}")
                return False
            else:
                print(f"✅ {package.split('>=')[0]} installed successfully")
        
        print("\n✅ All essential packages installed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def verify_installation():
    """Verify essential packages are working"""
    print("\n🔍 Verifying Installation...")
    
    packages = [
        ('flask', 'Flask'),
        ('flask_socketio', 'Flask-SocketIO'),
        ('OpenSSL', 'pyOpenSSL'),
        ('socketio', 'python-socketio'),
        ('requests', 'requests')
    ]
    
    all_good = True
    for package, name in packages:
        try:
            __import__(package)
            print(f"✅ {name}: OK")
        except ImportError:
            print(f"❌ {name}: Not found")
            all_good = False
    
    return all_good

def main():
    """Main installation function"""
    print("🚀 LAN Communication Hub - Essential Installation")
    print("=" * 60)
    
    if not install_essential_packages():
        print("\n❌ Installation failed")
        return 1
    
    if not verify_installation():
        print("\n❌ Verification failed")
        return 1
    
    print("\n🎉 Installation Complete!")
    print("=" * 60)
    print("✅ HTTPS server functionality ready")
    print("✅ Camera/microphone access will work")
    print()
    print("📋 Next Steps:")
    print("1. Start server: python3 start_server.py")
    print("2. Host: https://localhost:5000")
    print("3. Clients: https://[server-ip]:5000")
    print()
    print("💡 Optional: Install media processing packages")
    print("   pip install opencv-python Pillow numpy")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())