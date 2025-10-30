# 🚀 LAN Collaboration System - Complete Setup Guide

A comprehensive setup guide for the GUI-based real-time collaboration system with video conferencing, audio chat, screen sharing, file transfer, and messaging capabilities.

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Dependency Details](#dependency-details)
4. [Network Configuration](#network-configuration)
5. [Quick Start Guide](#quick-start-guide)
6. [Advanced Configuration](#advanced-configuration)
7. [Troubleshooting](#troubleshooting)
8. [Performance Optimization](#performance-optimization)

## 🖥️ System Requirements

### **Minimum Requirements:**
- **Operating System:** Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python:** 3.8 or higher
- **RAM:** 4GB minimum
- **Storage:** 500MB free space
- **Network:** LAN connection (Wi-Fi or Ethernet)
- **CPU:** Dual-core processor

### **Recommended Requirements:**
- **Operating System:** Windows 11, macOS 12+, or Linux (Ubuntu 20.04+)
- **Python:** 3.10 or higher
- **RAM:** 8GB or more
- **Storage:** 2GB free space
- **Network:** Gigabit Ethernet for best performance
- **CPU:** Quad-core processor or better
- **Camera:** HD webcam (for video features)
- **Microphone:** Quality microphone (for audio features)

## 📦 Installation Methods

### **Method 1: Automated Installation (Recommended)**

```bash
# 1. Navigate to the gui directory
cd path/to/CN_Project/gui

# 2. Run the automated installer
python install.py

# 3. Follow the prompts to install missing dependencies
```

### **Method 2: Manual Installation**

```bash
# Install from requirements file
pip install -r requirements.txt

# Verify installation
python -c "import PyQt6, cv2, numpy, PIL, pyaudio, mss; print('Success!')"
```

### **Method 3: Individual Package Installation**

```bash
# Core dependencies
pip install PyQt6>=6.5.0
pip install opencv-python>=4.8.0
pip install numpy>=1.24.0
pip install Pillow>=10.0.0
pip install pyaudio>=0.2.11
pip install mss>=9.0.1
```

## 🔧 Dependency Details

### **Core Dependencies (Required)**

- **PyQt6 (>=6.5.0)** - Modern GUI framework
- **OpenCV (>=4.8.0)** - Video processing and camera access
- **NumPy (>=1.24.0)** - Array operations for media data
- **Pillow (>=10.0.0)** - Image processing and formats
- **PyAudio (>=0.2.11)** - Audio capture and playback
- **MSS (>=9.0.1)** - Fast screen capture

### **Platform-Specific Installation**

#### **Windows:**
```bash
# 1. Install Visual C++ Build Tools (required)
# Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install PyQt6 (use compatible versions for Windows)
pip install "PyQt6>=6.4.0,<6.7.0" "PyQt6-Qt6>=6.4.0,<6.7.0"

# 5. Install other dependencies
pip install opencv-python numpy Pillow mss

# 6. For PyAudio (try methods in order):
# Method 1: Using pipwin (recommended)
pip install pipwin
pipwin install pyaudio

# Method 2: Download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
# Method 3: Use conda if available
conda install pyaudio

# 7. Test PyQt6 installation
python test_pyqt6.py

# 8. Alternative: Use Windows-specific requirements
pip install -r requirements-windows.txt
```

#### **macOS:**
```bash
# Install Xcode Command Line Tools
xcode-select --install

# For PyAudio:
brew install portaudio
pip install pyaudio
```

#### **Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3-dev python3-pip portaudio19-dev
pip3 install -r requirements.txt
```

## 🌐 Network Configuration

### **Port Requirements**

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Main Control | 9000 | TCP | Chat, commands, file transfer |
| Video Stream | 10000 | UDP | Real-time video streaming |
| Audio Stream | 11000 | UDP | Real-time audio streaming |
| Screen Share | 12000 | TCP | Screen sharing data |
| File Upload | 13000 | TCP | File upload server |
| File Download | 14000 | TCP | File download server |

### **Firewall Configuration**

Ensure these ports are open in your firewall for the server machine.

## 🚀 Quick Start Guide

### **Step 1: Install Dependencies**
```bash
cd gui
python install.py
```

### **Step 2: Start Server**
```bash
python start_server.py
# OR directly:
python main_server.py
```

### **Step 3: Start Client(s)**
```bash
python start_client.py
# OR directly:
python main_client.py
```

### **Step 4: Connect**
1. Enter server IP address (shown in server output)
2. Use port 9000
3. Enter your username
4. Click Connect

## ⚙️ Advanced Configuration

### **Server Configuration**
Edit `main_server.py` to modify:
- Port numbers
- Maximum participants
- File upload limits
- Video quality settings

### **Client Configuration**
Edit `main_client.py` to modify:
- Video resolution
- Audio quality
- UI themes
- Connection timeouts

## 🔧 Troubleshooting

### **Common Issues**

#### **"PyQt6 not found"**
```bash
pip install PyQt6
# If fails, try:
pip install PyQt6-Qt6
```

#### **"No module named cv2"**
```bash
pip install opencv-python
```

#### **"PyAudio installation failed"**
- **Windows:** Install Visual C++ Build Tools
- **macOS:** `brew install portaudio`
- **Linux:** `sudo apt install portaudio19-dev`

#### **"Connection refused"**
- Check server is running
- Verify IP address and port
- Check firewall settings
- Ensure same network

#### **"Video not working"**
- Check camera permissions
- Verify camera is not used by other apps
- Try different camera index in code

#### **"Audio not working"**
- Check microphone permissions
- Verify audio device availability
- Test with system audio settings

### **Performance Issues**

#### **High CPU Usage**
- Reduce video resolution
- Lower frame rate
- Close unnecessary applications

#### **Network Lag**
- Use wired connection instead of Wi-Fi
- Reduce video quality
- Check network bandwidth

#### **Memory Usage**
- Restart application periodically
- Close unused video windows
- Monitor with Task Manager/Activity Monitor

## 🎯 Performance Optimization

### **Video Settings**
- **Resolution:** 640x480 for good performance, 1280x720 for quality
- **Frame Rate:** 15-30 FPS depending on network
- **Compression:** Adjust quality vs. bandwidth

### **Audio Settings**
- **Sample Rate:** 44100 Hz for quality, 22050 Hz for bandwidth
- **Channels:** Mono for bandwidth, Stereo for quality
- **Buffer Size:** Larger for stability, smaller for low latency

### **Network Optimization**
- Use Gigabit Ethernet when possible
- Minimize network traffic from other applications
- Consider QoS settings on router

## 🔒 Security Considerations

### **Network Security**
- Use on trusted LAN networks only
- Consider VPN for remote access
- Monitor network traffic

### **File Transfer Security**
- Scan uploaded files for malware
- Limit file types and sizes
- Use dedicated upload/download directories

### **Access Control**
- Implement user authentication if needed
- Monitor participant list
- Use strong usernames

## 🛠️ Development Setup

### **Code Structure**
- `main_server.py` - Server implementation
- `main_client.py` - Client GUI application
- `simple_connection.py` - Connection dialog
- `start_*.py` - Convenience launchers
- `install.py` - Dependency installer

### **Debugging**
Enable debug output by setting environment variable:
```bash
export DEBUG=1
python main_server.py
```

### **Testing**
Test with multiple clients on same machine:
```bash
# Terminal 1: Server
python main_server.py

# Terminal 2: Client 1
python main_client.py

# Terminal 3: Client 2
python main_client.py
```

## 📞 Support

For issues and questions:
1. Check this setup guide
2. Review the troubleshooting section
3. Check the documentation.md file
4. Verify all dependencies are installed
5. Test with minimal configuration

## 🎉 Success Indicators

You'll know setup is successful when:
- ✅ All dependencies install without errors
- ✅ Server starts and shows connection info
- ✅ Client connects to server successfully
- ✅ Video/audio streams work between clients
- ✅ Chat messages are exchanged
- ✅ File transfers complete successfully

Happy collaborating! 🚀