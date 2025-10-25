# 🖥️ LAN Meeting - GUI Version

## 📁 **Directory Contents**

This directory contains the **original GUI-based** LAN meeting application using Tkinter.

### **Files:**
- `server.py` - GUI server application (host interface)
- `client.py` - GUI client application (participant interface)
- `requirements.txt` - Python dependencies for GUI version
- `install.py` - Installation script for dependencies

## 🚀 **Quick Start**

### **1. Install Dependencies:**
```bash
cd gui
pip install -r requirements.txt
```

### **2. Start Server (Host):**
```bash
python server.py
```

### **3. Start Client (Participants):**
```bash
python client.py
```

## ⚠️ **Known Issues**

This GUI version has some limitations:
- Button visibility issues during screen sharing
- GUI freezing/flickering problems
- Threading conflicts with UI updates
- Platform-specific GUI dependencies

## 💡 **Recommendation**

For a better experience, consider using the **Web Server version** in the `../webserver/` directory, which solves all GUI-related issues and provides:
- ✅ Stable, responsive interface
- ✅ Cross-platform compatibility
- ✅ Mobile device support
- ✅ No GUI threading issues

## 🔧 **Features**

- Multi-user video conferencing
- Screen sharing capabilities
- Group chat functionality
- File sharing system
- Host controls and permissions
- Real-time audio/video streaming

## 📋 **System Requirements**

- Python 3.7+
- Tkinter (usually included with Python)
- OpenCV for video processing
- PyAudio for audio handling
- PIL/Pillow for image processing
- Additional dependencies in requirements.txt