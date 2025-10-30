#!/usr/bin/env python3
"""
PyQt6 Installation Test Script
Tests if PyQt6 is properly installed and can create a basic window
"""

import sys

def test_pyqt6_import():
    """Test PyQt6 imports"""
    print("🔍 Testing PyQt6 imports...")
    
    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
        print("✅ PyQt6.QtWidgets: OK")
    except ImportError as e:
        print(f"❌ PyQt6.QtWidgets: FAILED - {e}")
        return False
    
    try:
        from PyQt6.QtCore import Qt, QTimer
        print("✅ PyQt6.QtCore: OK")
    except ImportError as e:
        print(f"❌ PyQt6.QtCore: FAILED - {e}")
        return False
    
    try:
        from PyQt6.QtGui import QFont, QPixmap
        print("✅ PyQt6.QtGui: OK")
    except ImportError as e:
        print(f"❌ PyQt6.QtGui: FAILED - {e}")
        return False
    
    return True

def test_pyqt6_window():
    """Test creating a PyQt6 window"""
    print("\n🔍 Testing PyQt6 window creation...")
    
    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
        from PyQt6.QtCore import QTimer
        
        # Create application
        app = QApplication(sys.argv)
        
        # Create main window
        window = QMainWindow()
        window.setWindowTitle("PyQt6 Test - LAN Collaboration System")
        window.setGeometry(100, 100, 400, 200)
        
        # Create central widget
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Add test label
        label = QLabel("✅ PyQt6 is working correctly!")
        label.setStyleSheet("font-size: 16px; color: green; padding: 20px;")
        layout.addWidget(label)
        
        info_label = QLabel("This window will close automatically in 3 seconds...")
        info_label.setStyleSheet("font-size: 12px; color: gray; padding: 10px;")
        layout.addWidget(info_label)
        
        central_widget.setLayout(layout)
        window.setCentralWidget(central_widget)
        
        # Show window
        window.show()
        
        # Auto-close after 3 seconds
        QTimer.singleShot(3000, app.quit)
        
        print("✅ PyQt6 window created successfully!")
        print("   Window should appear for 3 seconds...")
        
        # Run application
        app.exec()
        
        print("✅ PyQt6 window test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ PyQt6 window test FAILED - {e}")
        return False

def main():
    """Main test function"""
    print("🚀 PyQt6 Installation Test for LAN Collaboration System")
    print("=" * 60)
    
    # Test imports
    if not test_pyqt6_import():
        print("\n❌ PyQt6 import test failed!")
        print("\n💡 Installation suggestions:")
        print("   pip install PyQt6 PyQt6-Qt6 PyQt6-tools")
        print("   # OR for Windows:")
        print("   pip install -r requirements-windows.txt")
        return 1
    
    # Test window creation
    if not test_pyqt6_window():
        print("\n❌ PyQt6 window test failed!")
        return 1
    
    print("\n🎉 All PyQt6 tests passed!")
    print("✅ Your system is ready to run the LAN Collaboration Client!")
    return 0

if __name__ == "__main__":
    sys.exit(main())