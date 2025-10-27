#!/usr/bin/env python3
"""
Installation script for LAN Communication Hub
"""

import subprocess
import sys
import os

def print_banner():
    print("🚀 LAN Communication Hub - Installation")
    print("=" * 50)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python {version.major}.{version.minor} detected")
        print("💡 Python 3.7 or higher is required")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def install_requirements():
    """Install requirements from requirements.txt"""
    print("\n📦 Installing dependencies...")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    try:
        # Upgrade pip first
        print("🔄 Upgrading pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True, capture_output=True)
        
        # Install requirements
        print("📥 Installing packages...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All dependencies installed successfully!")
            return True
        else:
            print("❌ Installation failed:")
            print(result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_installation():
    """Verify that all packages are installed correctly"""
    print("\n🔍 Verifying installation...")
    
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

def show_next_steps():
    """Show what to do after installation"""
    print("\n🎉 Installation Complete!")
    print("=" * 50)
    
    print("📋 Next Steps:")
    print()
    
    print("1️⃣ Start the server:")
    print("   python3 start_server.py")
    print()
    
    print("2️⃣ Host creates session:")
    print("   • Go to: https://localhost:5000")
    print("   • Click 'Host Session'")
    print("   • Note the session ID (server IP)")
    print()
    
    print("3️⃣ Clients join session:")
    print("   • Go to: https://[server-ip]:5000")
    print("   • Accept browser security warning")
    print("   • Join with session ID")
    print("   • Camera/microphone will work!")
    print()
    
    print("🔧 Troubleshooting:")
    print("   • Media test: https://[server-ip]:5000/media-test")
    print("   • Server info: https://[server-ip]:5000/api/server-info")
    print()
    
    print("💡 Alternative (SSH tunnel):")
    print("   python3 connect_client.py")

def main():
    """Main installation function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Installation failed. Please check the errors above.")
        return 1
    
    # Verify installation
    if not verify_installation():
        print("\n⚠️  Some packages may not have installed correctly.")
        print("💡 Try running: pip install -r requirements.txt")
        return 1
    
    # Show next steps
    show_next_steps()
    return 0

if __name__ == "__main__":
    sys.exit(main())