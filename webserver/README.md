# LAN Meeting Web Application

A simple web-based video conferencing application for local area networks.

## Features

- 🎥 **Video Calling** - Host and clients can see each other
- 🎤 **Audio Communication** - Bidirectional audio streaming
- 🖥️ **Screen Sharing** - Share your screen with participants
- 💬 **Chat System** - Text messaging during meetings
- 👥 **Multi-participant** - Support for multiple clients
- 🌐 **Web-based** - No software installation required

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_web.txt
```

### 2. Start Server (Host)
```bash
python server.py
```
This starts the server without opening any browser windows.

### 3. Connect Clients
```bash
python client.py
```
This opens the client interface in a browser and prompts for server IP.

### 4. Manual Access
- **Host**: http://localhost:5000/host
- **Client**: http://localhost:5000/client
- **LAN Access**: http://[YOUR_IP]:5000/

## File Structure

```
webserver/
├── app.py                    # Main Flask application
├── server.py                 # Server launcher (no browser)
├── client.py                 # Client launcher (opens browser)
├── start.py                  # Legacy launcher script
├── requirements_web.txt      # Python dependencies
├── templates/
│   ├── host_simple.html     # Host interface (WORKING)
│   └── client_simple.html   # Client interface
└── uploads/                 # File sharing directory
```

## Usage

### For Host (Server):
1. Run `python server.py` to start server
2. Open http://localhost:5000/host in browser
3. Click "📹 Start Video" to enable camera
4. Click "🎤 Start Audio" to enable microphone
5. Use "🖥️ Share Screen" to present
6. Manage participants with host controls

### For Clients:
1. Run `python client.py` and enter server IP
2. Or manually open http://[SERVER_IP]:5000/client
3. Enter your name and join meeting
4. Enable camera and microphone as needed
5. Participate in video calls and chat

## Browser Requirements

- **Recommended**: Chrome, Firefox, Edge
- **Required**: Modern browser with WebRTC support
- **Permissions**: Camera and microphone access
- **Connection**: HTTPS or localhost for media access

## Network Setup

The server runs on all network interfaces (0.0.0.0:5000) by default.
Clients on the same network can connect using the host's IP address.

## Troubleshooting

### Camera/Microphone Not Working
- Check browser permissions
- Ensure you're using HTTPS or localhost
- Try a different browser

### Connection Issues
- Check firewall settings
- Ensure port 5000 is available
- Verify network connectivity

### Performance Issues
- Close unnecessary browser tabs
- Check network bandwidth
- Reduce video quality if needed