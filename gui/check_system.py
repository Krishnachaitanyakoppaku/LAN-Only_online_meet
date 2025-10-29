#!/usr/bin/env python3
"""
System and PyQt6 compatibility checker for LAN Collaboration Client
"""

import sys
import platform

def check_system():
    """Check system compatibility."""
    print("=" * 60)
    print("LAN COLLABORATION CLIENT - SYSTEM CHECK")
    print("=" * 60)
    
    # Python version
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    
    # Platform info
    print(f"Platform: {platform.platform()}")
    print(f"System: {platform.system()}")
    print(f"Release: {platform.release()}")
    print(f"Machine: {platform.machine()}")
    
    # PyQt6 check
    try:
        import PyQt6
        print(f"✅ PyQt6 installed")
        
        try:
            from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
            print(f"   PyQt6 Version: {PYQT_VERSION_STR}")
            print(f"   Qt Version: {QT_VERSION_STR}")
            
            # Check version compatibility
            pyqt_version = tuple(map(int, PYQT_VERSION_STR.split('.')))
            if pyqt_version >= (6, 4, 0):
                print("   ✅ PyQt6 version is compatible")
            else:
                print("   ⚠️  PyQt6 version is older than recommended (6.4.0+)")
                print("   💡 Consider upgrading: pip install --upgrade PyQt6")
                
        except Exception as e:
            print(f"   ❌ Could not get version info: {e}")
            
    except ImportError:
        print("❌ PyQt6 not installed")
        print("💡 Install with: pip install PyQt6")
        return False
    
    # Check Qt style availability
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication([])
        
        print(f"Available Qt Styles:")
        available_styles = app.style().objectName()
        print(f"   Current: {available_styles}")
        
        # Test style setting
        try:
            if sys.platform == "darwin":
                app.setStyle("macOS")
                print("   ✅ macOS style available")
            elif sys.platform == "win32":
                app.setStyle("windowsvista")
                print("   ✅ Windows Vista style available")
            else:
                app.setStyle("Fusion")
                print("   ✅ Fusion style available")
        except Exception as e:
            print(f"   ⚠️  Style setting issue: {e}")
            
        app.quit()
        
    except Exception as e:
        print(f"❌ Qt application test failed: {e}")
        return False
    
    # Check optional dependencies
    print("\nOptional Dependencies:")
    
    # OpenCV
    try:
        import cv2
        print(f"   ✅ OpenCV: {cv2.__version__}")
    except ImportError:
        print("   ❌ OpenCV not available (video features disabled)")
        print("   💡 Install with: pip install opencv-python")
    
    # PyAudio
    try:
        import pyaudio
        print("   ✅ PyAudio available")
    except ImportError:
        print("   ❌ PyAudio not available (audio features disabled)")
        print("   💡 Install with: pip install pyaudio")
    
    # Opus
    try:
        import opuslib
        print("   ✅ Opus available")
    except ImportError:
        print("   ❌ Opus not available (audio encoding disabled)")
        print("   💡 Install with: pip install opuslib")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    if sys.platform == "darwin":
        print("🍎 macOS detected:")
        print("   - GUI should render with native macOS styling")
        print("   - If GUI looks bad, try: pip install --upgrade PyQt6")
    elif sys.platform == "win32":
        print("🪟 Windows detected:")
        print("   - GUI should render with Windows styling")
        print("   - If GUI looks bad, try: pip install --upgrade PyQt6")
    else:
        print("🐧 Linux detected:")
        print("   - GUI will use Fusion style")
        print("   - Install system Qt6 packages for better integration")
    
    print("\n💡 If GUI still looks bad:")
    print("   1. Update PyQt6: pip install --upgrade PyQt6")
    print("   2. Check system Qt6 installation")
    print("   3. Try different Python version (3.11 or 3.12)")
    print("   4. Check display scaling settings")
    
    return True

if __name__ == "__main__":
    check_system()