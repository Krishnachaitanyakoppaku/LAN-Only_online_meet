# 🪟 Windows Setup Guide - LAN Collaboration System

## 🚨 Common Windows Issues and Solutions

### **Issue 1: "No module named 'PyQt6.QtWidgets'"**

This is the most common issue on Windows. Here are the solutions:

#### **Solution A: Clean Installation (Recommended)**
```bash
# 1. Uninstall existing PyQt6
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-tools -y

# 2. Clear pip cache
pip cache purge

# 3. Install compatible working versions
pip install "PyQt6>=6.4.0,<6.7.0" "PyQt6-Qt6>=6.4.0,<6.7.0"

# 4. Test installation
python -c "from PyQt6.QtWidgets import QApplication; print('SUCCESS')"
```

#### **Solution B: Use Windows Requirements File**
```bash
pip install -r requirements-windows.txt
```

#### **Solution C: Manual Installation**
```bash
# Install each component separately
pip install --upgrade pip setuptools wheel
pip install "PyQt6>=6.4.0,<6.7.0"
pip install "PyQt6-Qt6>=6.4.0,<6.7.0"
```

### **Issue 2: "Microsoft Visual C++ 14.0 is required"**

#### **Solution: Install Visual C++ Build Tools**
1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "C++ build tools" workload
3. Restart command prompt
4. Try installation again

### **Issue 3: PyAudio Installation Fails**

#### **Solution A: Use pipwin (Easiest)**
```bash
pip install pipwin
pipwin install pyaudio
```

#### **Solution B: Download Precompiled Wheel**
1. Go to: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Download appropriate wheel for your Python version:
   - Python 3.11: `PyAudio-0.2.11-cp311-cp311-win_amd64.whl`
   - Python 3.10: `PyAudio-0.2.11-cp310-cp310-win_amd64.whl`
   - Python 3.9: `PyAudio-0.2.11-cp39-cp39-win_amd64.whl`
3. Install: `pip install PyAudio-0.2.11-cp311-cp311-win_amd64.whl`

#### **Solution C: Use Conda**
```bash
conda install pyaudio
```

### **Issue 4: "DLL load failed" or "ImportError"**

#### **Solution: Reinstall with Dependencies**
```bash
# Uninstall everything
pip uninstall PyQt6 PyQt6-Qt6 opencv-python numpy -y

# Reinstall with no-cache
pip install --no-cache-dir PyQt6==6.6.1 PyQt6-Qt6==6.6.1
pip install --no-cache-dir opencv-python numpy Pillow
```

## 🔧 Step-by-Step Windows Installation

### **Step 1: Prerequisites**
```bash
# Check Python version (3.8+ required)
python --version

# Install/upgrade pip
python -m pip install --upgrade pip
```

### **Step 2: Create Virtual Environment**
```bash
# Create virtual environment
python -m venv collaboration_env

# Activate virtual environment
collaboration_env\Scripts\activate

# Verify activation (should show (collaboration_env))
echo %VIRTUAL_ENV%
```

### **Step 3: Install Dependencies**
```bash
# Method 1: Use Windows requirements (recommended)
pip install -r requirements-windows.txt

# Method 2: Manual installation
pip install "PyQt6>=6.4.0,<6.7.0" "PyQt6-Qt6>=6.4.0,<6.7.0"
pip install opencv-python numpy Pillow mss
pip install pipwin
pipwin install pyaudio
```

### **Step 4: Test Installation**
```bash
# Test PyQt6
python test_pyqt6.py

# Test all components
python install.py

# Test main application
python main_client.py
```

## 🛠️ Troubleshooting Commands

### **Diagnostic Commands**
```bash
# Check Python and pip versions
python --version
pip --version

# Check installed packages
pip list | findstr PyQt6
pip list | findstr opencv
pip list | findstr numpy

# Check virtual environment
echo %VIRTUAL_ENV%
where python
where pip

# Test imports individually
python -c "import sys; print(sys.path)"
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
python -c "import cv2; print('OpenCV OK')"
python -c "import numpy; print('NumPy OK')"
python -c "import PIL; print('Pillow OK')"
python -c "import mss; print('MSS OK')"
```

### **Clean Reinstall Commands**
```bash
# Complete cleanup
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-tools opencv-python numpy Pillow mss pyaudio -y
pip cache purge
rmdir /s collaboration_env

# Fresh start
python -m venv collaboration_env
collaboration_env\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-windows.txt
```

## 🎯 Windows-Specific Tips

### **PowerShell vs Command Prompt**
- Use **Command Prompt** (cmd) for better compatibility
- If using PowerShell, you may need to enable script execution:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### **Antivirus Software**
- Some antivirus software may block pip installations
- Temporarily disable real-time protection during installation
- Add Python and pip to antivirus exclusions

### **Windows Defender**
- Windows Defender may quarantine some packages
- Check Windows Security > Virus & threat protection > Protection history
- Restore any quarantined Python packages

### **Path Issues**
- Ensure Python is in your PATH
- Use full paths if commands not found:
  ```bash
  C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe -m pip install PyQt6
  ```

## 📞 Still Having Issues?

### **Quick Test Script**
Save this as `quick_test.py` and run it:

```python
import sys
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")

try:
    from PyQt6.QtWidgets import QApplication
    print("✅ PyQt6.QtWidgets: OK")
except ImportError as e:
    print(f"❌ PyQt6.QtWidgets: {e}")

try:
    import cv2
    print("✅ OpenCV: OK")
except ImportError as e:
    print(f"❌ OpenCV: {e}")

try:
    import numpy
    print("✅ NumPy: OK")
except ImportError as e:
    print(f"❌ NumPy: {e}")
```

### **Get Help**
If you're still having issues:
1. Run `python quick_test.py` and share the output
2. Run `pip list` and share the installed packages
3. Share your Python version and Windows version
4. Check if you're using a virtual environment

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ `python test_pyqt6.py` shows a window for 3 seconds
- ✅ `python install.py` shows all green checkmarks
- ✅ `python main_client.py` opens the collaboration client
- ✅ No import errors in the console

Happy collaborating on Windows! 🚀