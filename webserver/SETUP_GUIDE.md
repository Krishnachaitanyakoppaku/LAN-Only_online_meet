# LAN Communication Hub - Setup Guide

## Overview

The LAN Communication Hub is a comprehensive multi-user communication application designed to operate exclusively over Local Area Networks (LAN). It provides real-time video conferencing, audio communication, screen sharing, group chat, and file sharing capabilities without requiring internet connectivity.

## System Requirements

### Server Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: 500MB free space
- **Network**: Ethernet or Wi-Fi connection to LAN

### Client Requirements
- **Web Browser**: Chrome 80+, Firefox 75+, Safari 13+, or Edge 80+
- **Camera**: USB webcam or built-in camera (for video conferencing)
- **Microphone**: USB microphone or built-in microphone (for audio)
- **Network**: Connection to the same LAN as the server

## Installation

### Method 1: Automated Setup (Recommended)

1. **Download the project files** to your server machine
2. **Run the startup script**:
   ```bash
   python start_server.py
   ```
   The script will automatically:
   - Check Python version compatibility
   - Install required dependencies
   - Start the server
   - Open your web browser

### Method 2: Manual Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server**:
   ```bash
   python server.py
   ```

3. **Access the application**:
   - Open your web browser
   - Navigate to `http://localhost:5000` (local access)
   - Or use the network IP shown in the terminal

## Network Configuration

### Finding Your Server IP Address

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" under your network adapter.

**macOS/Linux:**
```bash
ifconfig
```
Look for "inet" address under your network interface.

### Firewall Configuration

**Windows:**
1. Open Windows Defender Firewall
2. Click "Allow an app or feature through Windows Defender Firewall"
3. Add Python or allow port 5000

**macOS:**
1. System Preferences → Security & Privacy → Firewall
2. Click "Firewall Options"
3. Allow incoming connections for Python

**Linux (Ubuntu):**
```bash
sudo ufw allow 5000
```

## Usage Guide

### Starting a Session

1. **Host a Session**:
   - Click "Host Session" on the main page
   - Enter your username
   - Optionally specify a session ID
   - Click "Start Session"

2. **Join a Session**:
   - Click "Join Session" on the main page
   - Enter your username
   - Enter the session ID provided by the host
   - Click "Join Session"

### Features Overview

#### Video Conferencing
- **Enable/Disable Video**: Click the video button in the control bar
- **Multiple Participants**: All participants' videos are displayed in a grid
- **Video Quality**: Adjustable quality settings in the settings menu

#### Audio Conferencing
- **Enable/Disable Audio**: Click the microphone button in the control bar
- **Audio Mixing**: Server automatically mixes all audio streams
- **Echo Cancellation**: Built-in echo cancellation for better audio quality

#### Screen Sharing
- **Start Sharing**: Click "Share Screen" in the control bar
- **Presenter Mode**: Only one user can share screen at a time
- **Fullscreen View**: Click the expand button to view in fullscreen
- **Stop Sharing**: Click "Stop Sharing" or close the sharing window

#### Group Chat
- **Send Messages**: Type in the chat input and press Enter
- **Message History**: All messages are displayed chronologically
- **User Identification**: Messages show sender's username and timestamp

#### File Sharing
- **Upload Files**: Click the upload button in the files section
- **Drag & Drop**: Drag files directly to the upload area
- **Download Files**: Click the download button next to any file
- **Progress Tracking**: Upload/download progress is shown

### Keyboard Shortcuts

- **Enter**: Send chat message or submit forms
- **Escape**: Close modals and dialogs
- **Ctrl+C**: Stop the server (in terminal)

## Troubleshooting

### Common Issues

#### "Connection Failed" Error
- **Check server status**: Ensure the server is running
- **Verify IP address**: Use the correct server IP address
- **Check firewall**: Ensure port 5000 is not blocked
- **Network connectivity**: Verify all devices are on the same LAN

#### Camera/Microphone Not Working
- **Browser permissions**: Allow camera and microphone access
- **Device availability**: Check if camera/microphone are connected
- **Other applications**: Close other applications using the camera
- **Browser compatibility**: Try a different browser

#### Poor Video/Audio Quality
- **Network bandwidth**: Check LAN bandwidth and latency
- **Device performance**: Close other resource-intensive applications
- **Quality settings**: Adjust video quality in settings
- **Network congestion**: Reduce number of participants

#### Screen Sharing Issues
- **Browser support**: Ensure browser supports screen sharing
- **Permissions**: Grant screen sharing permissions when prompted
- **Resolution**: Lower screen resolution for better performance
- **Multiple monitors**: Select specific monitor if using multiple displays

### Performance Optimization

#### Server Optimization
- **CPU**: Use a machine with good CPU performance
- **RAM**: Ensure sufficient RAM for multiple video streams
- **Network**: Use wired Ethernet connection for best performance
- **Background processes**: Close unnecessary applications

#### Client Optimization
- **Browser**: Use Chrome or Firefox for best performance
- **Hardware acceleration**: Enable hardware acceleration in browser
- **Extensions**: Disable unnecessary browser extensions
- **System resources**: Close other applications during sessions

## Security Considerations

### Network Security
- **LAN Only**: Application only works on local networks
- **No Internet**: No data is transmitted over the internet
- **Firewall**: Configure firewall to restrict access if needed

### Data Privacy
- **Local Storage**: All data remains on your local network
- **No Cloud**: No data is stored in external cloud services
- **Session Data**: Session data is cleared when server stops

### Access Control
- **Session IDs**: Use unique session IDs to prevent unauthorized access
- **User Management**: Monitor connected users in the participants list
- **File Sharing**: Be cautious with sensitive file sharing

## Advanced Configuration

### Custom Port Configuration
Edit `server.py` and change the port:
```python
socketio.run(app, host='0.0.0.0', port=YOUR_PORT, debug=False)
```

### Video Quality Settings
Modify video compression in `session.js`:
```javascript
const dataURL = canvas.toDataURL('image/jpeg', QUALITY); // 0.1 to 1.0
```

### Audio Settings
Adjust audio processing parameters in `session.js`:
```javascript
const processor = audioContext.createScriptProcessor(BUFFER_SIZE, 1, 1);
```

## Support and Maintenance

### Logs and Debugging
- **Server logs**: Check terminal output for error messages
- **Browser console**: Press F12 to view browser console for client errors
- **Network monitoring**: Use browser developer tools to monitor network traffic

### Updates and Maintenance
- **Dependencies**: Regularly update Python packages
- **Browser updates**: Keep browsers updated for best compatibility
- **System updates**: Maintain updated operating systems

### Backup and Recovery
- **Session data**: Session data is temporary and not persistent
- **User data**: No user data is permanently stored
- **Configuration**: Backup any custom configuration files

## Technical Architecture

### Server Architecture
- **Flask**: Web framework for HTTP requests
- **SocketIO**: WebSocket communication for real-time features
- **UDP Sockets**: Low-latency media streaming
- **Session Management**: In-memory session and user management

### Client Architecture
- **HTML5**: Modern web interface
- **JavaScript**: Client-side functionality
- **WebRTC-like**: Browser-based media capture and streaming
- **Canvas API**: Video frame processing and display

### Communication Protocols
- **HTTP/HTTPS**: Initial connection and file transfers
- **WebSocket**: Real-time chat and control messages
- **UDP**: Video and audio streaming (low latency)
- **TCP**: Reliable file transfers and critical data

## License and Credits

This project is developed for educational and research purposes. All components use open-source libraries and technologies.

### Dependencies
- Flask: Web framework
- Flask-SocketIO: WebSocket support
- OpenCV: Video processing
- NumPy: Numerical computing
- Pillow: Image processing
- Eventlet: Asynchronous networking

---

For additional support or questions, please refer to the project documentation or contact the development team.
