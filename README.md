# LAN Communication System

A comprehensive, standalone multi-user communication application designed for Local Area Network (LAN) environments. This system provides real-time collaboration tools including video conferencing, audio communication, screen sharing, group chat, and file sharing - all without requiring internet connectivity.

## 🚀 Features

### Core Modules

1. **Multi-User Video Conferencing**
   - Real-time video capture and transmission via UDP
   - Multiple participant video streams
   - Dynamic video layout with main speaker view
   - Video quality optimization for LAN bandwidth

2. **Multi-User Audio Conferencing**
   - Real-time audio capture and streaming via UDP
   - Server-side audio mixing
   - Low-latency audio transmission
   - Automatic audio level management

3. **Screen & Slide Sharing**
   - Presenter role management
   - Real-time screen capture and transmission via TCP
   - High-quality image compression
   - Presenter controls (start/stop sharing)

4. **Group Text Chat**
   - Real-time messaging via TCP
   - Chat history persistence
   - Timestamp and sender identification
   - System notifications

5. **File Sharing**
   - Secure file transfer via TCP
   - Progress tracking for uploads/downloads
   - File metadata management
   - Multi-user file distribution

## 🏗️ System Architecture

### Network Architecture
- **Client-Server Model**: Centralized server manages all communications
- **TCP/IP Sockets**: Reliable communication for control, chat, and files
- **UDP Sockets**: Low-latency streaming for video and audio
- **LAN Only**: No internet connectivity required

### Communication Protocols

#### TCP Communications (Port 8888)
- Client authentication and session management
- Group chat messages
- File transfers
- Presenter role management
- System control messages

#### UDP Video Streaming (Port 8889)
- Real-time video frame transmission
- Compressed video data packets
- Client-to-server-to-clients broadcasting

#### UDP Audio Streaming (Port 8890)
- Real-time audio data transmission
- Audio mixing and distribution
- Low-latency audio streaming

## 📋 Requirements

### System Requirements
- **Operating System**: Windows 10/11, Linux, or macOS
- **Python**: 3.8 or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Network**: LAN connectivity (Ethernet or WiFi)
- **Hardware**: Webcam and microphone for full functionality

### Python Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `opencv-python` - Video capture and processing
- `pillow` - Image processing
- `numpy` - Numerical operations
- `pyaudio` - Audio capture and playback
- `tkinter` - GUI framework (included with Python)

## 🚀 Quick Start

### 1. Installation
```bash
# Clone or download the project
git clone <repository-url>
cd lan-communication-system

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python server.py
```
- Click "Start Server" in the GUI
- Server joins as "Host" participant automatically
- Use Host controls to enable video/audio/presentation
- Note the displayed IP address for clients to connect

### 3. Connect Clients
```bash
python client.py
```
- Enter the server's IP address
- Enter your name
- Click "Connect"

### 4. Start Communicating
- **Video**: Click "Start Video" to enable camera
- **Audio**: Click "Start Audio" to enable microphone
- **Chat**: Type messages in the chat area
- **Present**: Click "Start Presenting" to share your screen
- **Files**: Use the File Sharing tab to share files

## 🎯 Usage Guide

### Server Operations
1. **Starting the Server**
   - Launch `server.py`
   - Click "Start Server"
   - Share the displayed IP address with participants
   - Server automatically joins as "Host" participant

2. **Host Participation**
   - Enable/disable video with "Start/Stop Video"
   - Enable/disable audio with "Start/Stop Audio"
   - Request presenter role with "Start Presenting"
   - Participate in group chat
   - Host appears first in all participant lists

3. **Monitoring Sessions**
   - View all participants (including Host) in real-time
   - Monitor activity logs and chat messages
   - Manage server resources

4. **Stopping the Server**
   - Click "Stop Server" to gracefully disconnect all clients
   - Host automatically leaves the session
   - Close the application

### Client Operations
1. **Connecting**
   - Enter server IP address
   - Provide your display name
   - Click "Connect"

2. **Video Conferencing**
   - Enable/disable video with "Start/Stop Video"
   - View other participants in the video grid
   - Main speaker appears in the large video area

3. **Audio Communication**
   - Enable/disable audio with "Start/Stop Audio"
   - Audio is automatically mixed by the server
   - Adjust system volume as needed

4. **Screen Sharing**
   - Request presenter role with "Start Presenting"
   - Share your screen with "Share Screen"
   - Only one presenter at a time

5. **Group Chat**
   - Type messages in the chat input
   - Press Enter or click "Send"
   - View conversation history

6. **File Sharing**
   - Go to "File Sharing" tab
   - Select files to share with the group
   - Download files shared by others

## 🔧 Configuration

### Network Configuration
- **Default Ports**:
  - TCP Control: 8888
  - UDP Video: 8889
  - UDP Audio: 8890

- **Firewall Settings**:
  - Ensure the above ports are open on the server machine
  - Allow Python applications through firewall

### Performance Tuning
- **Video Quality**: Adjust resolution in video capture settings
- **Audio Quality**: Modify sample rate and bit depth in audio settings
- **Network Optimization**: Configure buffer sizes for your LAN speed

## 🛠️ Technical Details

### Video Processing
- **Capture**: OpenCV for camera access
- **Compression**: Real-time frame compression
- **Transmission**: UDP packets with sequence numbers
- **Display**: Multi-stream rendering with PIL/Tkinter

### Audio Processing
- **Capture**: PyAudio for microphone access
- **Format**: 16-bit PCM, 44.1kHz, mono
- **Mixing**: Server-side audio stream combination
- **Playback**: Real-time audio output

### File Transfer
- **Protocol**: TCP for reliability
- **Chunking**: Large files split into manageable chunks
- **Progress**: Real-time transfer progress tracking
- **Integrity**: Checksum verification

### Security Considerations
- **LAN Only**: No external network access required
- **Authentication**: Basic client identification
- **Data Integrity**: TCP ensures reliable data transfer
- **Privacy**: All communication stays within LAN

## 🐛 Troubleshooting

### Common Issues

1. **Camera Not Working**
   - Check camera permissions
   - Ensure no other applications are using the camera
   - Try different camera indices in the code

2. **Audio Issues**
   - Verify microphone permissions
   - Check audio device availability
   - Adjust audio buffer settings

3. **Connection Problems**
   - Verify server IP address
   - Check firewall settings
   - Ensure all devices are on the same LAN

4. **Performance Issues**
   - Reduce video resolution
   - Lower frame rate
   - Check network bandwidth

### Error Messages
- **"Cannot access camera"**: Camera permission or hardware issue
- **"Connection refused"**: Server not running or wrong IP
- **"Audio device error"**: Microphone permission or hardware issue

## 📈 Performance Optimization

### Server Optimization
- Run on a machine with adequate CPU and RAM
- Use wired Ethernet connection for stability
- Monitor resource usage during sessions

### Client Optimization
- Close unnecessary applications
- Use wired connection when possible
- Adjust video quality based on network conditions

### Network Optimization
- Use Gigabit Ethernet for best performance
- Minimize network congestion
- Consider Quality of Service (QoS) settings

## 🔮 Future Enhancements

### Planned Features
- End-to-end encryption for secure communications
- Recording and playback functionality
- Advanced audio processing (noise cancellation)
- Mobile client applications
- Whiteboard collaboration tools
- Advanced file management with folders

### Scalability Improvements
- Support for larger groups (50+ participants)
- Load balancing for multiple servers
- Bandwidth adaptive streaming
- Cloud deployment options

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

## 📞 Support

For technical support or questions:
- Check the troubleshooting section
- Review the technical documentation
- Submit issues on the project repository

## 🏆 Acknowledgments

- OpenCV community for video processing capabilities
- PyAudio developers for audio handling
- Python tkinter team for GUI framework
- Contributors and testers

---

**Note**: This system is designed for LAN environments and does not require internet connectivity. All communications remain within your local network for privacy and security.