# 🎥 LAN Meeting System

A comprehensive offline video conferencing solution for local area networks (LAN). This system enables multi-user video calls, screen sharing, group chat, and file sharing without requiring an internet connection.

## 📁 **Project Structure**

This project contains **two versions** of the LAN meeting system:

### 🌐 **Web Server Version** (Recommended)

**Location**: `webserver/` directory

Modern web-based interface that solves all GUI issues:

- ✅ **Stable interface** - no button flickering or freezing
- ✅ **Cross-platform** - works on any device with a browser
- ✅ **Mobile support** - access from phones/tablets
- ✅ **Easy client access** - just enter IP address
- ✅ **Professional UI** - modern, responsive design

### 🖥️ **GUI Version** (Original)

**Location**: `gui/` directory

Traditional desktop application using Tkinter:

- ⚠️ **GUI limitations** - button visibility issues during screen sharing
- ⚠️ **Platform dependent** - requires Python GUI libraries
- ⚠️ **Desktop only** - no mobile support

## 🚀 **Quick Start**

### **Option 1: Web Server Version (Recommended)**

```bash
cd webserver
pip install -r requirements_web.txt
python start_web_meeting.py
```

**Access:**

- **Host Control**: http://localhost:5000/host
- **Client Interface**: http://localhost:5000/client
- **LAN Access**: http://[YOUR_IP]:5000/client

**Client Joining:**

```bash
# Easy launcher
python join_meeting.py

# Windows users
join_meeting.bat

# Direct browser
http://[SERVER_IP]:5000/client
```

### **Option 2: GUI Version**

```bash
cd gui
pip install -r requirements.txt

# Start server (host)
python server.py

# Start client (participants)
python client.py
```

## ✨ **Features**

### 🎬 **Video Conferencing**

- Multi-user video calls with up to 50 participants
- Real-time video streaming optimized for LAN
- Local video preview for participants
- Dynamic video grid that adapts to participant count

### 🖥️ **Screen Sharing**

- Presenter role management with permission system
- High-quality screen capture
- Multi-client screen viewing
- Host controls to manage screen sharing

### 🎤 **Audio Communication**

- Real-time audio streaming with low latency
- Individual microphone controls (mute/unmute)
- Speaker controls for audio output
- Host audio management

### 💬 **Group Chat**

- Real-time text messaging for all participants
- Message history preserved during session
- System notifications for user events

### 📁 **File Sharing**

- Upload and share any file type
- Download shared files
- File management interface
- Real-time notifications

### 👑 **Host Controls**

- Meeting management and participant controls
- Permission management
- Force commands (mute all, disable video, etc.)
- Meeting settings configuration

## 🌍 **Network Setup**

### **Same Computer:**

- Host: http://localhost:5000/host (web) or `python server.py` (GUI)
- Client: http://localhost:5000/client (web) or `python client.py` (GUI)

### **LAN (Different Computers):**

1. Find host IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Share with clients: http://[HOST_IP]:5000/client (web) or IP address (GUI)

### **Mobile Devices (Web Version Only):**

- Connect to same WiFi
- Open browser: http://[HOST_IP]:5000/client

## 🔒 **Security & Privacy**

- ✅ **Completely offline** - no internet required
- ✅ **LAN only** - all data stays on local network
- ✅ **No external servers** - complete privacy and control
- ✅ **Self-contained** - no external dependencies during meetings

## 📋 **System Requirements**

### **Web Version:**

- Python 3.7+
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Network connection (LAN/WiFi)

### **GUI Version:**

- Python 3.7+
- Tkinter (usually included with Python)
- OpenCV, PyAudio, PIL/Pillow
- Desktop environment

## 🎯 **Which Version to Choose?**

| Feature              | Web Version      | GUI Version          |
| -------------------- | ---------------- | -------------------- |
| **Stability**        | ✅ Excellent     | ⚠️ GUI issues        |
| **Cross-platform**   | ✅ Any browser   | ⚠️ Python required   |
| **Mobile Support**   | ✅ Full support  | ❌ Not available     |
| **Setup Complexity** | ✅ Simple        | ⚠️ More dependencies |
| **Client Access**    | ✅ Just enter IP | ⚠️ Need Python       |
| **Performance**      | ✅ Smooth        | ⚠️ Threading issues  |

**Recommendation**: Use the **Web Server Version** for the best experience!

## 🛠️ **Troubleshooting**

### **Common Issues:**

**Connection Problems:**

- Ensure all devices are on the same network
- Check firewall settings
- Verify IP addresses are correct

**Web Version Issues:**

- Allow browser camera/microphone permissions
- Use Chrome or Firefox for best compatibility
- Check if port 5000 is available

**GUI Version Issues:**

- Install all dependencies: `pip install -r requirements.txt`
- Check camera/microphone permissions
- Try running as administrator if needed

## 📚 **Documentation**

- **Web Version**: See `webserver/WEB_SETUP_GUIDE.md` for detailed setup
- **GUI Version**: See `gui/README.md` for GUI-specific instructions
- **Client Launchers**: Multiple easy ways to join meetings

## 🤝 **Contributing**

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📄 **License**

This project is licensed under the MIT License.

## 🙏 **Acknowledgments**

- Flask and SocketIO communities for web framework
- OpenCV community for video processing
- PyAudio developers for audio streaming
- Python community for excellent networking libraries

---

**Get started with the Web Server version for the best experience!** 🚀
