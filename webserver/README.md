# 🌐 LAN Meeting - Web Server Version

## 📁 **Directory Contents**

This directory contains the **modern web-based** LAN meeting application that solves all GUI issues.

### **Core Files:**
- `web_server.py` - Main web server application
- `start_web_meeting.py` - Easy launcher script
- `requirements_web.txt` - Python dependencies for web version
- `WEB_SETUP_GUIDE.md` - Detailed setup and usage guide

### **Client Launchers:**
- `join_meeting.py` - Command-line client launcher
- `join_meeting_gui.py` - GUI client launcher
- `join_meeting.bat` - Windows batch file
- `join_meeting.sh` - Linux/Mac shell script

### **Web Templates:**
- `templates/base.html` - Base HTML template
- `templates/host.html` - Host control interface
- `templates/client.html` - Client meeting interface

## 🚀 **Quick Start**

### **1. Install Dependencies:**
```bash
cd webserver
pip install -r requirements_web.txt
```

### **2. Start Web Server:**
```bash
python start_web_meeting.py
```

### **3. Access Interfaces:**
- **Host Control**: http://localhost:5000/host
- **Client Interface**: http://localhost:5000/client
- **LAN Access**: http://[YOUR_IP]:5000/client

### **4. Clients Join Easily:**
```bash
# Command line launcher
python join_meeting.py

# GUI launcher
python join_meeting_gui.py

# Windows users
join_meeting.bat

# Direct browser access
http://[SERVER_IP]:5000/client
```

## ✅ **Advantages Over GUI Version**

- ✅ **No GUI issues** - stable, responsive web interface
- ✅ **Cross-platform** - works on any device with a browser
- ✅ **Mobile support** - access from phones/tablets
- ✅ **Better performance** - no threading conflicts
- ✅ **Modern design** - professional, user-friendly interface
- ✅ **Easy client access** - just enter IP address
- ✅ **Drag & drop files** - better file sharing experience

## 🔧 **Features**

### **Video Conferencing:**
- Multi-participant video calls
- Screen sharing with presenter controls
- Local video preview
- Real-time video streaming

### **Audio Communication:**
- Real-time audio streaming
- Mute/unmute controls
- Host can manage participant audio

### **File Sharing:**
- Drag & drop file uploads
- Download shared files
- File manager interface
- Real-time file notifications

### **Chat System:**
- Group chat with all participants
- Real-time message delivery
- Chat history for new joiners

### **Host Controls:**
- Mute all participants
- Disable video for all
- End meeting for everyone
- Manage participant permissions

## 🌍 **Network Setup**

### **Same Computer:**
- Host: http://localhost:5000/host
- Client: http://localhost:5000/client

### **LAN (Different Computers):**
- Find your IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
- Share: http://[YOUR_IP]:5000/client

### **Mobile Devices:**
- Connect to same WiFi
- Open browser: http://[HOST_IP]:5000/client

## 🔒 **Security & Privacy**

- ✅ **Completely offline** - no internet required
- ✅ **LAN only** - all data stays on local network
- ✅ **No external servers** - complete privacy
- ✅ **Self-contained** - no external dependencies

## 📱 **Client Access Methods**

| Method | Command | Best For |
|--------|---------|----------|
| **Command Line** | `python join_meeting.py` | Most users |
| **GUI Launcher** | `python join_meeting_gui.py` | GUI lovers |
| **Windows Batch** | `join_meeting.bat` | Windows users |
| **Direct Browser** | `http://[IP]:5000/client` | Tech-savvy |
| **Mobile Browser** | Browser on phone/tablet | Mobile users |

## 🎯 **Recommended Usage**

This web server version is **highly recommended** over the GUI version because:
- Solves all button visibility and GUI freezing issues
- Provides better user experience
- Works on any device with a browser
- Easier for clients to join (just enter IP)
- More stable and reliable

## 📋 **System Requirements**

- Python 3.7+
- Flask and Flask-SocketIO
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Network connection (LAN/WiFi)
- No additional GUI dependencies needed

For detailed setup instructions, see `WEB_SETUP_GUIDE.md`