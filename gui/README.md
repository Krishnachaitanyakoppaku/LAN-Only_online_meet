# 🚀 LAN Collaboration System - GUI Version

A complete real-time collaboration system with video conferencing, audio chat, screen sharing, file transfer, and messaging.

## 📁 File Structure

### **Essential Files:**
- **`main_server.py`** - Complete collaboration server (~1200+ lines)
- **`main_client.py`** - Complete PyQt6 GUI client (~3000+ lines)
- **`simple_connection.py`** - Connection dialog for client

### **Convenience Scripts:**
- **`start_server.py`** - Easy server startup with dependency checks
- **`start_client.py`** - Easy client startup with connection help
- **`install.py`** - Dependency installer and system checker

### **Configuration:**
- **`requirements.txt`** - Python dependencies list

### **Directories:**
- **`uploads/`** - File upload storage
- **`downloads/`** - File download storage

## 🚀 Quick Start

### **1. Install Dependencies:**
```bash
python install.py
# OR manually:
pip install -r requirements.txt
```

### **2. Start Server:**
```bash
python start_server.py
# OR directly:
python main_server.py
```

### **3. Start Client(s):**
```bash
python start_client.py
# OR directly:
python main_client.py
```

## ✨ Features

- **🎥 Video Conferencing** - Multi-participant video calls
- **🎤 Audio Chat** - High-quality audio communication  
- **🖥️ Screen Sharing** - Real-time screen sharing with viewer
- **💬 Text Chat** - Group and private messaging
- **📁 File Transfer** - Upload/download with progress tracking
- **👥 Participant Management** - See who's online
- **🎨 Modern UI** - Dark theme PyQt6 interface

## 🔧 Usage

1. **Server shows connection info** when started
2. **Clients connect** using server IP and port 9000
3. **Join meeting** with username
4. **Use controls** for video/audio/screen sharing
5. **Chat and share files** with other participants
6. **Leave cleanly** using the Leave button

## 🌐 Network Ports

- **TCP 9000** - Main control and chat
- **UDP 10000** - Video streaming
- **UDP 11000** - Audio streaming  
- **TCP 12000** - Screen sharing
- **TCP 13000** - File uploads
- **TCP 14000** - File downloads

## 🎯 Perfect for:

- Team meetings and collaboration
- Remote presentations
- File sharing sessions
- LAN parties and events
- Educational environments