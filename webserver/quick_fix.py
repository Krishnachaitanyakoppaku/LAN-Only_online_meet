#!/usr/bin/env python3
"""
Quick fix: Install only pyOpenSSL for HTTPS support
"""

import subprocess
import sys

def quick_install():
    print("🔧 Quick Fix: Installing pyOpenSSL for HTTPS")
    print("=" * 50)
    
    try:
        print("📥 Installing pyOpenSSL...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'pyOpenSSL'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ pyOpenSSL installed successfully!")
            
            # Test import
            try:
                import OpenSSL
                print("✅ pyOpenSSL import test: OK")
                print("\n🎉 HTTPS support is now available!")
                print("\n📋 Next steps:")
                print("1. Run: python3 start_server.py")
                print("2. Server will start with HTTPS")
                print("3. Clients can access via https://[server-ip]:5000")
                return True
            except ImportError as e:
                print(f"❌ Import test failed: {e}")
                return False
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if quick_install():
        sys.exit(0)
    else:
        print("\n💡 Alternative: Try manual installation")
        print("   pip install pyOpenSSL")
        sys.exit(1)