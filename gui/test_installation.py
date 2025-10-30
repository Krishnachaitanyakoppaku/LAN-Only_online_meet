#!/usr/bin/env python3
"""
Quick Installation Test
Tests if all required packages can be imported
"""

def test_imports():
    """Test all required imports"""
    print("🔍 Testing package imports...")
    
    tests = [
        ("PyQt6.QtWidgets", "PyQt6 Widgets"),
        ("PyQt6.QtCore", "PyQt6 Core"),
        ("PyQt6.QtGui", "PyQt6 GUI"),
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("PIL", "Pillow"),
        ("mss", "MSS Screen Capture"),
    ]
    
    optional_tests = [
        ("pyaudio", "PyAudio (Audio)"),
    ]
    
    # Test required packages
    failed = []
    for module, name in tests:
        try:
            __import__(module)
            print(f"✅ {name}: OK")
        except ImportError as e:
            print(f"❌ {name}: FAILED - {e}")
            failed.append(name)
    
    # Test optional packages
    for module, name in optional_tests:
        try:
            __import__(module)
            print(f"✅ {name}: OK")
        except ImportError:
            print(f"⚠️  {name}: Missing (optional)")
    
    return len(failed) == 0

def main():
    print("🚀 LAN Collaboration System - Installation Test")
    print("=" * 50)
    
    if test_imports():
        print("\n🎉 All required packages are installed!")
        print("✅ You can run the collaboration system!")
        print("\nNext steps:")
        print("  1. Start server: python main_server.py")
        print("  2. Start client: python main_client.py")
        return 0
    else:
        print("\n❌ Some required packages are missing!")
        print("\n💡 Installation suggestions:")
        print("  1. Try: pip install -r requirements-minimal.txt")
        print("  2. Or: pip install PyQt6 opencv-python numpy Pillow mss")
        print("  3. For Windows: see WINDOWS_SETUP.md")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())