# LAN Video Calling Application

A comprehensive LAN-based video calling application with all Zoom-like features including:

## Features

### Core Video Calling
- Real-time video calling with multiple participants
- Audio calling with noise cancellation
- Screen sharing capabilities
- Video recording and playback
- Meeting controls (mute, video on/off, etc.)

### Communication
- Real-time chat messaging
- File sharing (upload/download)
- User presence indicators
- Meeting rooms and user management

### Advanced Features
- Bandwidth optimization
- Connection quality indicators
- Meeting recording
- Participant management
- Customizable UI themes

## Architecture

```
LAN-Video-Call/
├── server/                 # Server-side components
│   ├── main_server.py     # Main server application
│   ├── room_manager.py    # Meeting room management
│   ├── user_manager.py    # User authentication & management
│   ├── file_server.py     # File upload/download handling
│   └── media_server.py    # Video/audio streaming server
├── client/                 # Client-side components
│   ├── main_client.py     # Main client application
│   ├── video_client.py    # Video calling functionality
│   ├── audio_client.py    # Audio handling
│   ├── chat_client.py     # Chat messaging
│   └── file_client.py     # File sharing
├── shared/                 # Shared utilities
│   ├── protocol.py        # Communication protocol
│   ├── utils.py           # Common utilities
│   └── constants.py       # Application constants
└── gui/                    # GUI components
    ├── server_gui.py      # Server management interface
    ├── client_gui.py      # Client interface
    └── widgets/           # Custom GUI widgets
```

## Installation

1. Clone the repository
2. Install dependencies: `python3 setup.py`
3. Start host server: `python3 run_host_server.py --username "Host"`
4. Connect participants: `python3 run_client.py --host <server-ip> --username YourName`

## Usage

### Host Mode (Recommended)
1. Start the host server: `python3 run_host_gui.py`
2. Configure meeting settings and controls
3. Participants join using the server IP
4. Host can control the meeting (mute all, kick participants, etc.)

### Regular Server Mode
1. Start regular server: `python3 run_server_gui.py`
2. Connect clients to the server IP
3. Create or join meeting rooms
4. Enjoy video calling with all features!

### Meeting Controls (Host Mode)
- **Mute All**: Mute all participants at once
- **Disable Video**: Turn off video for all participants
- **Recording**: Start/stop meeting recording
- **Chat Control**: Enable/disable chat for participants
- **File Sharing**: Control file upload/download permissions
- **Participant Management**: Kick participants, view statistics

## Technical Details

- Built with Python socket programming
- Real-time communication using TCP/UDP
- Video processing with OpenCV
- Audio handling with PyAudio
- Modern GUI with CustomTkinter
- File transfer with chunked upload/download
