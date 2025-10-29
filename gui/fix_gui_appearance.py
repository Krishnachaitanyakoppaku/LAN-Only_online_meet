#!/usr/bin/env python3
"""
GUI Appearance Troubleshooting Script for LAN Collaboration Client
"""

import sys
import os

def fix_gui_appearance():
    """Provide solutions for GUI appearance issues."""
    print("=" * 60)
    print("GUI APPEARANCE TROUBLESHOOTING")
    print("=" * 60)
    
    print("\n🔧 COMMON FIXES FOR GUI APPEARANCE ISSUES:")
    print("-" * 40)
    
    print("\n1. 📦 UPDATE PYQT6:")
    print("   pip install --upgrade PyQt6")
    print("   # This often fixes styling and rendering issues")
    
    print("\n2. 🖥️  DISPLAY SCALING ISSUES:")
    print("   # If GUI elements are too small/large:")
    print("   export QT_AUTO_SCREEN_SCALE_FACTOR=1")
    print("   export QT_SCALE_FACTOR=1.0")
    print("   # Then run: python main_client.py")
    
    print("\n3. 🎨 FORCE SPECIFIC QT STYLE:")
    print("   # Try different styles:")
    print("   export QT_STYLE_OVERRIDE=Fusion")
    print("   # or")
    print("   export QT_STYLE_OVERRIDE=Windows")
    print("   # Then run: python main_client.py")
    
    print("\n4. 🔤 FONT RENDERING ISSUES:")
    print("   # If fonts look bad:")
    print("   export QT_FONT_DPI=96")
    print("   # or try:")
    print("   export QT_FONT_DPI=144")
    
    print("\n5. 🌈 COLOR/THEME ISSUES:")
    print("   # If colors look wrong, try disabling custom theme:")
    print("   # Edit main_client.py and comment out:")
    print("   # self.apply_dark_theme()")
    
    print("\n6. 🐍 PYTHON VERSION COMPATIBILITY:")
    print("   # Try with Python 3.11 if 3.12.5 has issues:")
    print("   pyenv install 3.11.9")
    print("   pyenv local 3.11.9")
    print("   pip install PyQt6 opencv-python pyaudio")
    
    print("\n7. 🍎 MACOS SPECIFIC FIXES:")
    if sys.platform == "darwin":
        print("   # Force native macOS styling:")
        print("   export QT_MAC_WANTS_LAYER=1")
        print("   # Disable dark mode if causing issues:")
        print("   export QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM=1")
    
    print("\n8. 🔄 RESET QT SETTINGS:")
    print("   # Clear Qt settings cache:")
    if sys.platform == "darwin":
        print("   rm -rf ~/Library/Preferences/com.lancollab.*")
    elif sys.platform == "win32":
        print("   # Delete registry entries under HKEY_CURRENT_USER\\Software\\LAN Collab")
    else:
        print("   rm -rf ~/.config/LAN\\ Collab/")
    
    print("\n" + "=" * 60)
    print("🚀 QUICK TEST COMMANDS:")
    print("=" * 60)
    
    print("\n# Test with minimal styling:")
    print("QT_STYLE_OVERRIDE=Fusion python main_client.py")
    
    print("\n# Test with scaling fix:")
    print("QT_AUTO_SCREEN_SCALE_FACTOR=1 python main_client.py")
    
    print("\n# Test with font fix:")
    print("QT_FONT_DPI=96 python main_client.py")
    
    print("\n# Test all fixes combined:")
    print("QT_STYLE_OVERRIDE=Fusion QT_AUTO_SCREEN_SCALE_FACTOR=1 QT_FONT_DPI=96 python main_client.py")
    
    print("\n" + "=" * 60)
    print("💡 IF NOTHING WORKS:")
    print("=" * 60)
    print("1. Try running check_system.py to see detailed system info")
    print("2. Compare PyQt6 versions between working (3.12.4) and non-working (3.12.5) machines")
    print("3. Consider using a virtual environment with the same PyQt6 version as the working machine")
    print("4. Check if there are any system-specific Qt6 packages that need updating")
    
    print(f"\n🔍 Current Python: {sys.version}")
    print(f"🔍 Current Platform: {sys.platform}")

if __name__ == "__main__":
    fix_gui_appearance()