# LAN Communication Hub

A comprehensive web-based communication platform for local area networks with video, audio, and screen sharing capabilities.

## 🚀 Quick Start

### Server Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Start server: `python server.py`
3. Server runs on `http://0.0.0.0:5000`

### Client Connection
**Windows:** Double-click `client_connect.bat`
**Linux/Mac:** Run `./client_connect.sh`
**Python:** Run `python connect_client.py`

## 📱 Features

- ✅ Real-time video and audio communication
- ✅ Screen sharing capabilities
- ✅ Text chat with file sharing
- ✅ Session-based rooms
- ✅ Cross-platform support
- ✅ Multiple connection methods for camera/microphone access

## 🔧 Connection Methods

### 1. Browser Override (Recommended)
- Enables camera/microphone over HTTP
- Uses Chrome with special flags
- No additional setup required

### 2. Direct Connection
- Simple HTTP connection
- Works for viewing only
- Camera/microphone may not work

### 3. SSH Tunnel
- Secure connection via localhost
- Enables camera/microphone access
- Requires SSH client

### 4. Auto-Discovery
- Automatically finds servers on network
- Scans local network range
- Connects to first available server

## 📋 Requirements

- Python 3.7+
- Modern web browser (Chrome recommended)
- Local network connectivity
- Optional: SSH client for tunnel method

## 🛠️ Installation

```bash
# Clone or download the project
cd webserver

# Install required packages
pip install -r requirements.txt

# Optional packages for enhanced features
pip install -r requirements-optional.txt

# Start the server
python server.py
```

## 🌐 Usage

1. **Start Server:** Run `python server.py` on host machine
2. **Connect Clients:** Use connection scripts or run `python connect_client.py`
3. **Join Session:** Enter session ID to join existing room
4. **Enable Media:** Allow camera/microphone permissions when prompted

## 🔍 Troubleshooting

### Camera/Microphone Issues
- Use **Browser Override** method (option 1)
- Try **SSH Tunnel** method (option 3)
- Ensure HTTPS or localhost access

### Connection Issues
- Check if devices are on same network
- Verify server IP address
- Test with **Auto-Discovery** (option 4)
- Check firewall settings

### Common Solutions
```bash
# Test server connectivity
ping [SERVER_IP]

# Check if port is open
telnet [SERVER_IP] 5000

# Scan for servers
python connect_client.py  # Choose option 4
```

## 📁 Project Structure

```
webserver/
├── server.py              # Main server application
├── connect_client.py      # Unified client connection manager
├── client_connect.bat     # Windows connection script
├── client_connect.sh      # Linux/Mac connection script
├── requirements.txt       # Core dependencies
├── requirements-optional.txt  # Optional features
├── static/               # Web assets
├── templates/            # HTML templates
└── README.md            # This file
```

## 🚀 Deployment Ready

This project is optimized for easy deployment:
- Consolidated connection methods
- Cross-platform compatibility
- Minimal dependencies
- Clear error messages and troubleshooting
- Automated server discovery

## Browser Security Notes

Modern browsers enforce security restrictions:
- Camera/microphone access requires HTTPS or localhost
- HTTP on remote IPs blocks media access
- **Solution**: Use Browser Override or SSH Tunnel methods

## License

MIT License - Free to use and modify