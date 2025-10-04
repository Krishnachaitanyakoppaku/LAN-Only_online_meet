# LAN Video Calling Application - Usage Guide

## Quick Start

### 1. Setup
```bash
# Install dependencies
python setup.py

# Or manually install requirements
pip install -r requirements.txt
```

### 2. Start Server
```bash
# GUI version (recommended)
python run_server_gui.py

# Command line version
python run_server.py --host 0.0.0.0 --port 8888
```

### 3. Start Client
```bash
# GUI version (recommended)
python run_client_gui.py

# Command line version
python run_client.py --host 127.0.0.1 --port 8888 --username YourName
```

## Features

### Core Video Calling
- **Real-time Video**: HD video calling with multiple participants
- **Audio Calling**: Crystal clear audio with noise reduction
- **Screen Sharing**: Share your screen with other participants
- **Meeting Rooms**: Create and join private/public rooms

### Communication
- **Chat Messaging**: Real-time text chat during calls
- **File Sharing**: Upload and download files up to 100MB
- **User Management**: See who's online and their status

### Advanced Features
- **Meeting Controls**: Mute/unmute, video on/off, kick users
- **Recording**: Record meetings (server-side)
- **Bandwidth Optimization**: Adaptive quality based on connection
- **Connection Quality**: Real-time connection status indicators

## Server GUI Features

### Server Management
- Start/stop server with custom host and port
- Real-time server statistics
- Connected users monitoring
- Active rooms management
- Server log viewer

### Statistics Display
- Uptime and connection counts
- User and room statistics
- File transfer statistics
- Media streaming statistics

## Client GUI Features

### Connection
- Connect to server with username
- Create or join meeting rooms
- Real-time connection status

### Video Calling
- Start/stop video camera
- Multiple participant video grid
- Screen sharing capabilities
- Video quality controls

### Audio
- Microphone controls
- Speaker volume adjustment
- Audio quality settings
- Noise reduction

### Chat & Files
- Real-time chat messaging
- File upload/download
- Chat history export
- File transfer progress

## Command Line Usage

### Server Commands
```bash
python run_server.py --help
python run_server.py --host 0.0.0.0 --port 8888
```

### Client Commands
```bash
python run_client.py --help
python run_client.py --host 192.168.1.100 --port 8888 --username John
```

### Client CLI Commands
Once connected, use these commands:
- `help` - Show available commands
- `create <room_name>` - Create a new room
- `join <room_id>` - Join a room
- `leave` - Leave current room
- `chat <message>` - Send chat message
- `start_video` - Start video streaming
- `stop_video` - Stop video streaming
- `quit` - Disconnect and exit

## Network Configuration

### LAN Setup
1. Ensure all devices are on the same network
2. Find server IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
3. Use server IP in client connection settings
4. Configure firewall to allow connections on chosen port

### Port Configuration
- Default server port: 8888
- Video streaming port: 8889
- Audio streaming port: 8890
- File transfer port: 8891
- Chat port: 8892

## Troubleshooting

### Common Issues

#### Connection Failed
- Check server is running
- Verify IP address and port
- Check firewall settings
- Ensure devices are on same network

#### Video/Audio Issues
- Check camera/microphone permissions
- Verify device drivers are installed
- Try different camera/microphone
- Check network bandwidth

#### File Transfer Issues
- Check file size (max 100MB)
- Verify sufficient disk space
- Check network stability
- Try smaller files first

### Performance Optimization

#### Server
- Use wired connection for better stability
- Close unnecessary applications
- Monitor CPU and memory usage
- Adjust video quality settings

#### Client
- Use good quality camera and microphone
- Ensure stable network connection
- Close other video applications
- Adjust video resolution if needed

## Security Considerations

### Network Security
- Use on trusted networks only
- Consider VPN for remote access
- Regularly update the application
- Monitor server logs for suspicious activity

### Privacy
- No data is stored permanently
- All communication is local to your network
- Files are stored temporarily on server
- Chat history is not persistent

## Advanced Configuration

### Server Configuration
Edit `shared/constants.py` to modify:
- Default ports
- Buffer sizes
- Video/audio settings
- File size limits
- Timeout values

### Client Configuration
Modify video/audio settings in client GUI:
- Video resolution and quality
- Audio sample rate and channels
- Compression settings
- Display preferences

## Development

### Project Structure
```
LAN-Video-Call/
├── server/          # Server components
├── client/          # Client components  
├── shared/          # Shared utilities
├── gui/             # GUI components
├── run_*.py         # Entry points
└── setup.py         # Setup script
```

### Adding Features
1. Modify shared protocol for new message types
2. Update server handlers in `main_server.py`
3. Add client functionality in respective modules
4. Update GUI components as needed
5. Test thoroughly before deployment

## Support

For issues and questions:
1. Check this usage guide
2. Review server logs for errors
3. Test with minimal configuration
4. Verify network connectivity
5. Check system requirements

## System Requirements

### Minimum Requirements
- Python 3.8+
- 4GB RAM
- 1GB free disk space
- Network connection
- Camera and microphone (for video calling)

### Recommended Requirements
- Python 3.9+
- 8GB RAM
- 5GB free disk space
- Gigabit network connection
- HD camera and quality microphone
