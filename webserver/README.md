# LAN Multi-User Communication Application

A robust, standalone, server-based multi-user communication application that operates exclusively over Local Area Network (LAN).

## Features

- **Multi-User Video Conferencing**: Real-time video streaming with webcam capture
- **Multi-User Audio Conferencing**: Audio mixing and broadcasting
- **Screen/Slide Sharing**: Presenter mode with screen capture
- **Group Text Chat**: Real-time messaging system
- **File Sharing**: Upload/download files with progress tracking

## Technology Stack

- **Backend**: Python Flask with SocketIO
- **Frontend**: HTML5, CSS3, JavaScript
- **Networking**: Socket programming for all communications
- **Video/Audio**: OpenCV for video processing
- **Real-time Communication**: WebSocket connections

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Server
```bash
python server.py
```

### Accessing the Application
1. Open web browser
2. Navigate to `http://localhost:5000` (or server IP)
3. Enter username and join the session

## Architecture

The application uses a client-server architecture with:
- Central server managing all communications
- Web-based client interface
- Socket programming for real-time data transfer
- UDP for video/audio streaming (low latency)
- TCP for file transfers and chat (reliability)

## Network Requirements

- All devices must be on the same LAN
- No internet connection required
- Firewall should allow connections on port 5000
