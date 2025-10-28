# LAN Communication Hub

A local network communication application for video/audio conferencing, screen sharing, and file transfers.

## Features

- **Video Conferencing**: Real-time webcam streaming
- **Audio Conferencing**: Microphone audio broadcasting
- **Screen Sharing**: Share your screen with participants
- **Text Chat**: Real-time messaging
- **File Sharing**: Upload and download files
- **Host Controls**: Mute/unmute participants, manage permissions

## Quick Start

### For Server (Host)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   python server.py
   # Or use the convenience script:
   python start_server.py
   ```

3. Note the server IP address displayed (e.g., `192.168.1.100`)

### For Clients (Participants)

**Important**: Browsers block camera/microphone access on HTTP remote IPs for security.

**Solution**: Use SSH tunnel to access via `localhost`:

1. Run the client connection script:
   ```bash
   python client_connect.py
   # Or use scripts:
   # client_connect.sh (Linux/Mac)
   # client_connect.bat (Windows)
   ```

2. Enter the server IP when prompted

3. Open browser to: `http://localhost:5000`

4. Join with session ID = server IP address

## File Structure

```
webserver/
├── server.py                 # Main Flask server
├── start_server.py          # Convenience startup script
├── client_connect.py        # SSH tunnel setup for clients
├── requirements.txt         # Python dependencies
├── templates/               # HTML templates
│   ├── index.html
│   ├── host.html
│   ├── join.html
│   └── session.html
├── static/                  # CSS, JS files
│   ├── css/
│   └── js/
└── README.md                # This file
```

## How It Works

1. **Server**: Runs on port 5000 (or auto-selected port if 5000 is busy)
2. **Session ID**: Uses server IP address as default session identifier
3. **SSH Tunnel**: Clients connect via SSH to tunnel port 5000 to their localhost
4. **WebSocket**: Real-time communication via Socket.IO
5. **Media Access**: Browsers allow camera/microphone via `localhost` but not remote IPs

## Browser Security

Modern browsers enforce security restrictions:
- Camera/microphone access requires HTTPS or localhost
- HTTP on remote IPs blocks media access
- This is by design, not a bug

**Workaround**: SSH tunnel maps remote server to localhost, enabling media access.

## Troubleshooting

### Port 5000 already in use
The server will automatically try ports 5050, 5080, 5500, or allocate a free port.

### Connection timeout
- Check firewall settings
- Ensure SSH is installed
- Verify server IP address

### Camera/microphone not working
- Must access via `localhost` (use SSH tunnel)
- Grant browser permissions when prompted
- Check browser console for errors

## Requirements

- Python 3.8+
- Flask, Flask-SocketIO
- SSH client (for clients)
- Modern browser with WebRTC support

## License

MIT License - Free to use and modify
