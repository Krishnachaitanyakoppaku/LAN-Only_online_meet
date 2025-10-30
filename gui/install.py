#!/usr/bin/env python3
"""
Installation and Setup Script for LAN Collaboration System
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

def check_package(package_name, import_name=None, optional=False):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        status = "✅" if not optional else "✅"
        print(f"{status} {package_name}: OK")
        return True
    except ImportError as e:
        status = "❌" if not optional else "⚠️ "
        opt_text = " (optional)" if optional else ""
        print(f"{status} {package_name}: Missing{opt_text}")
        
        # Special handling for PyQt6 on Windows
        if package_name == "PyQt6" and platform.system() == "Windows":
            print("    💡 Windows PyQt6 installation tips:")
            print('       - Try: pip install "PyQt6>=6.4.0,<6.7.0" "PyQt6-Qt6>=6.4.0,<6.7.0"')
            print("       - Or use: pip install -r requirements-minimal.txt")
            print("       - Ensure Visual C++ Build Tools are installed")
        
        return False

def install_package(package_name):
    """Install a package using pip"""
    try:
        print(f"📦 Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package_name}")
        return False

def check_pyqt6_installation():
    """Specifically check PyQt6 and its components"""
    print("\n🔍 Detailed PyQt6 Check:")
    pyqt6_components = [
        ("PyQt6.QtCore", "QtCore"),
        ("PyQt6.QtWidgets", "QtWidgets"),
        ("PyQt6.QtGui", "QtGui"),
    ]
    
    all_good = True
    for module, component in pyqt6_components:
        try:
            importlib.import_module(module)
            print(f"  ✅ {component}: OK")
        except ImportError:
            print(f"  ❌ {component}: Missing")
            all_good = False
    
    if not all_good and platform.system() == "Windows":
        print("\n  💡 Windows PyQt6 Fix:")
        print("     pip uninstall PyQt6 PyQt6-Qt6")
        print("     pip install PyQt6==6.6.1 PyQt6-Qt6==6.6.1 PyQt6-tools==6.6.1")
    
    return all_good

def check_dependencies():
    """Check all required dependencies"""
    print("🔍 Checking dependencies...")
    print("=" * 50)
    
    # Required packages
    required_packages = [
        ("PyQt6", "PyQt6"),
        ("opencv-python", "cv2"),
        ("numpy", "numpy"),
        ("Pillow", "PIL"),
        ("pyaudio", "pyaudio"),
        ("mss", "mss"),
    ]
    
    # Optional packages
    optional_packages = [
        ("pydub", "pydub"),
        ("psutil", "psutil"),
    ]
    
    missing_required = []
    missing_optional = []
    
    print("\n📋 Required Dependencies:")
    for package_name, import_name in required_packages:
        if not check_package(package_name, import_name):
            missing_required.append(package_name)
    
    print("\n📋 Optional Dependencies:")
    for package_name, import_name in optional_packages:
        if not check_package(package_name, import_name, optional=True):
            missing_optional.append(package_name)
    
    return missing_required, missing_optional

def install_requirements():
    """Install from requirements.txt if it exists"""
    if os.path.exists("requirements.txt"):
        print("\n📦 Installing from requirements.txt...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Requirements installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install from requirements.txt")
            return False
    else:
        print("⚠️  requirements.txt not found")
        return False

def check_system_requirements():
    """Check system requirements"""
    print("\n🖥️  System Information:")
    print("=" * 50)
    
    print(f"✅ Operating System: {platform.system()} {platform.release()}")
    print(f"✅ Architecture: {platform.machine()}")
    print(f"✅ Processor: {platform.processor()}")
    
    # Check available memory (if psutil is available)
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        print(f"✅ RAM: {memory_gb:.1f} GB")
        
        if memory_gb < 4:
            print("⚠️  Warning: Less than 4GB RAM detected. Performance may be limited.")
        elif memory_gb >= 8:
            print("✅ Sufficient RAM for optimal performance")
    except ImportError:
        print("ℹ️  Install psutil for detailed memory information")

def main():
    """Main installation function"""
    print("🚀 LAN Collaboration System - Installation & Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Installation cannot continue with incompatible Python version")
        return 1
    
    # Check system requirements
    check_system_requirements()
    
    # Check dependencies
    missing_required, missing_optional = check_dependencies()
    
    # Special PyQt6 check for Windows users
    if "PyQt6" not in missing_required:
        check_pyqt6_installation()
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        
        # Ask user if they want to install
        response = input("\n🤔 Would you like to install missing packages? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            # Try installing from requirements.txt first
            if not install_requirements():
                # Install individual packages
                print("\n📦 Installing individual packages...")
                for package in missing_required:
                    install_package(package)
            
            # Re-check dependencies
            print("\n🔄 Re-checking dependencies...")
            missing_required, _ = check_dependencies()
            
            if missing_required:
                print(f"\n❌ Still missing: {', '.join(missing_required)}")
                print("💡 Try installing manually: pip install " + " ".join(missing_required))
                return 1
        else:
            print("\n💡 Install missing packages manually:")
            print(f"pip install {' '.join(missing_required)}")
            return 1
    
    if missing_optional:
        print(f"\nℹ️  Optional packages not installed: {', '.join(missing_optional)}")
        print("💡 For enhanced features, install with:")
        print(f"pip install {' '.join(missing_optional)}")
    
    print("\n🎉 Installation check complete!")
    print("\n🚀 Ready to run:")
    print("   • Server: python main_server.py")
    print("   • Client: python main_client.py")
    print("\n📖 See README.md for detailed usage instructions")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())