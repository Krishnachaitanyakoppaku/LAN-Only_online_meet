#!/usr/bin/env python3
"""
Installation and Setup Script for LAN Communication System
Checks dependencies and system requirements
"""

import sys
import subprocess
import importlib
import platform
import os

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    else:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} is installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is not installed")
        return False

def install_package(package_name):
    """Install a package using pip"""
    try:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package_name}")
        return False

def check_system_requirements():
    """Check system requirements"""
    print("\n🖥️  System Information:")
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    
    # Check for camera (basic check)
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Camera detected")
            cap.release()
        else:
            print("⚠️  No camera detected (optional for server)")
    except:
        print("⚠️  Cannot check camera (OpenCV not installed)")
    
    # Check for audio (basic check)
    try:
        import pyaudio
        audio = pyaudio.PyAudio()
        if audio.get_device_count() > 0:
            print("✅ Audio devices detected")
        audio.terminate()
    except:
        print("⚠️  Cannot check audio devices (PyAudio not installed)")

def main():
    """Main installation function"""
    print("🚀 LAN Communication System - Installation Check")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Required packages
    packages = [
        ("opencv-python", "cv2"),
        ("pillow", "PIL"),
        ("numpy", "numpy"),
        ("pyaudio", "pyaudio"),
        ("mss", "mss")  # For screen capture
    ]
    
    print("\n📦 Checking Dependencies:")
    missing_packages = []
    
    for package_name, import_name in packages:
        if not check_package(package_name, import_name):
            missing_packages.append(package_name)
    
    # Check tkinter (usually comes with Python)
    if not check_package("tkinter", "tkinter"):
        print("⚠️  tkinter not found - this usually comes with Python")
        print("   On Ubuntu/Debian: sudo apt-get install python3-tk")
        print("   On CentOS/RHEL: sudo yum install tkinter")
    
    # Install missing packages
    if missing_packages:
        print(f"\n📥 Installing {len(missing_packages)} missing packages...")
        
        for package in missing_packages:
            if not install_package(package):
                print(f"\n❌ Installation failed for {package}")
                print("Please install manually using:")
                print(f"   pip install {package}")
                sys.exit(1)
    
    # Check system requirements
    check_system_requirements()
    
    # Final verification
    print("\n🔍 Final Verification:")
    all_good = True
    for package_name, import_name in packages:
        if not check_package(package_name, import_name):
            all_good = False
    
    if all_good:
        print("\n🎉 Installation Complete!")
        print("\nYou can now run the applications:")
        print("  Server: python server.py")
        print("  Client: python client.py")
        print("\nFor detailed usage instructions, see README.md")
    else:
        print("\n❌ Some packages are still missing")
        print("Please check the error messages above and install manually")
        sys.exit(1)

if __name__ == "__main__":
    main()