#!/usr/bin/env python3
"""
Setup script for LAN Video Calling Application
"""

import os
import sys
import subprocess
import platform

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    
    try:
        # Install from requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("Creating directories...")
    
    directories = [
        "uploads",
        "downloads",
        "logs"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Created directory: {directory}")
        except Exception as e:
            print(f"✗ Failed to create directory {directory}: {e}")
            return False
    
    return True

def check_dependencies():
    """Check if required dependencies are available"""
    print("Checking dependencies...")
    
    required_packages = [
        "cv2",
        "numpy", 
        "PIL",
        "pyaudio",
        "tkinter"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "cv2":
                import cv2
            elif package == "PIL":
                from PIL import Image
            elif package == "tkinter":
                import tkinter
            else:
                __import__(package)
            print(f"✓ {package} is available")
        except ImportError:
            print(f"✗ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Please install them manually:")
        
        if "pyaudio" in missing_packages:
            system = platform.system().lower()
            if system == "linux":
                print("  sudo apt-get install python3-pyaudio portaudio19-dev")
            elif system == "darwin":  # macOS
                print("  brew install portaudio")
                print("  pip install pyaudio")
            elif system == "windows":
                print("  pip install pyaudio")
        
        return False
    
    return True

def main():
    """Main setup function"""
    print("LAN Video Calling Application Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Create directories
    if not create_directories():
        print("✗ Failed to create directories")
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("✗ Failed to install requirements")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("✗ Some dependencies are missing")
        print("\nPlease install missing dependencies and run setup again.")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("✓ Setup completed successfully!")
    print("\nYou can now run the application:")
    print("  Server GUI: python run_server_gui.py")
    print("  Client GUI: python run_client_gui.py")
    print("  Server CLI: python run_server.py")
    print("  Client CLI: python run_client.py")

if __name__ == "__main__":
    main()
