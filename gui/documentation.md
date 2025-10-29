# 📚 LAN Collaboration System - Complete Technical Documentation

A comprehensive technical documentation for the GUI-based real-time collaboration system covering architecture, implementation details, protocols, and internal workings.

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [File Structure Analysis](#file-structure-analysis)
4. [Server Implementation](#server-implementation)
5. [Client Implementation](#client-implementation)
6. [Network Protocols](#network-protocols)
7. [GUI Components](#gui-components)
8. [Media Processing](#media-processing)
9. [File Transfer System](#file-transfer-system)
10. [Screen Sharing System](#screen-sharing-system)
11. [Chat System](#chat-system)
12. [Connection Management](#connection-management)
13. [Threading Architecture](#threading-architecture)
14. [Error Handling](#error-handling)
15. [Performance Considerations](#performance-considerations)
16. [Security Implementation](#security-implementation)
17. [Extension Points](#extension-points)
18. [API Reference](#api-reference)

## 🎯 Project Overview

### **System Purpose**
The LAN Collaboration System is a comprehensive real-time communication platform designed for local area networks. It provides enterprise-grade features including multi-participant video conferencing, high-quality audio communication, screen sharing, file transfer, and text messaging through a modern PyQt6 interface.

### **Key Features**
- **Multi-User Video Conferencing:** Support for multiple participants with real-time video streaming
- **High-Quality Audio Communication:** Low-latency audio streaming with noise reduction
- **Screen Sharing:** Real-time screen sharing with dedicated viewer windows
- **File Transfer System:** Robust file upload/download with progress tracking
- **Text Chat:** Group and private messaging with rich formatting
- **Modern GUI:** Dark-themed PyQt6 interface with responsive design
- **Cross-Platform:** Windows, macOS, and Linux support
- **Network Optimized:** Efficient protocols for LAN environments

### **Technical Specifications**
- **Language:** Python 3.8+
- **GUI Framework:** PyQt6
- **Video Processing:** OpenCV
- **Audio Processing:** PyAudio
- **Screen Capture:** MSS (Multi-Screen Shot)
- **Image Processing:** Pillow/PIL
- **Networking:** Native Python sockets with asyncio
- **Architecture:** Client-Server with UDP streaming and TCP control## 🏗️ 
Architecture Overview

### **System Architecture**
The system follows a client-server architecture with specialized components for different media types:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client A      │    │   Server        │    │   Client B      │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ GUI Thread  │ │    │ │ TCP Control │ │    │ │ GUI Thread  │ │
│ └─────────────┘ │    │ │ Server      │ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ └─────────────┘ │    │ ┌─────────────┐ │
│ │ Network     │◄┼────┼►┌─────────────┐ │    │ │ Network     │ │
│ │ Thread      │ │    │ │ UDP Video   │ │    │ │ Thread      │ │
│ └─────────────┘ │    │ │ Server      │ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ └─────────────┘ │    │ ┌─────────────┐ │
│ │ Video       │ │    │ ┌─────────────┐ │    │ │ Video       │ │
│ │ Client      │◄┼────┼►│ UDP Audio   │◄┼────┼►│ Client      │ │
│ └─────────────┘ │    │ │ Server      │ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ └─────────────┘ │    │ ┌─────────────┐ │
│ │ Audio       │ │    │ ┌─────────────┐ │    │ │ Audio       │ │
│ │ Client      │◄┼────┼►│ Screen      │◄┼────┼►│ Client      │ │
│ └─────────────┘ │    │ │ Share       │ │    │ └─────────────┘ │
│                 │    │ │ Server      │ │    │                 │
└─────────────────┘    │ └─────────────┘ │    └─────────────────┘
                       │ ┌─────────────┐ │
                       │ │ File        │ │
                       │ │ Transfer    │ │
                       │ │ Servers     │ │
                       │ └─────────────┘ │
                       └─────────────────┘
```

### **Communication Protocols**
1. **TCP Control Channel (Port 9000):** Main communication, chat, commands, participant management
2. **UDP Video Stream (Port 10000):** Real-time video data transmission
3. **UDP Audio Stream (Port 11000):** Real-time audio data transmission
4. **TCP Screen Share (Port 12000):** Screen sharing data with reliability
5. **TCP File Upload (Port 13000):** File upload server with progress tracking
6. **TCP File Download (Port 14000):** File download server with resume support

### **Threading Model**
Each client runs multiple threads for optimal performance:
- **Main GUI Thread:** User interface and event handling
- **Network Thread:** TCP communication with server
- **Video Client Thread:** Video capture and UDP streaming
- **Audio Client Thread:** Audio capture and UDP streaming
- **Screen Capture Thread:** Screen capture for sharing
- **File Transfer Threads:** Upload/download operations

## 📁 File Structure Analysis

### **Core Implementation Files**

#### **main_server.py (~1200+ lines)**
The complete server implementation handling all backend operations:

**Key Classes:**
- `Participant`: Represents a connected user with state management
- `CollaborationServer`: Main server class with async TCP handling
- `UDPVideoServer`: Handles video stream distribution
- `UDPAudioServer`: Handles audio stream distribution
- `ScreenShareServer`: Manages screen sharing sessions
- `FileUploadServer`: Handles file upload operations
- `FileDownloadServer`: Manages file download requests

**Core Functions:**
- `handle_client()`: Main client connection handler
- `handle_message()`: Message routing and processing
- `broadcast_message()`: Message distribution to all clients
- `handle_login()`: User authentication and session setup
- `handle_logout()`: Clean disconnection and cleanup

#### **main_client.py (~3000+ lines)**
The comprehensive PyQt6 GUI client implementation:

**Key Classes:**
- `CollaborationClient`: Main window and application controller
- `NetworkThread`: Async TCP communication with server
- `VideoClient`: Video capture and UDP streaming
- `AudioClient`: Audio capture and UDP streaming
- `VideoGridWidget`: Multi-participant video display
- `ChatWidget`: Text messaging interface
- `ParticipantsWidget`: User list management
- `MediaControlsWidget`: Audio/video/screen controls
- `FileUploadThread`: File upload with progress
- `FileDownloadThread`: File download with progress
- `ScreenCaptureClient`: Screen sharing capture
- `ScreenShareViewer`: Screen sharing display window

**GUI Components:**
- Modern dark theme interface
- Responsive video grid layout
- Rich text chat with emoji support
- File drag-and-drop functionality
- Real-time participant management
- Media control buttons with visual feedback#### **simpl
e_connection.py (~150 lines)**
Connection dialog for server details:

**Key Classes:**
- `SimpleConnectionDialog`: PyQt6 dialog for connection setup

**Features:**
- Server host/port input validation
- Username validation and formatting
- Dark theme styling consistent with main application
- Input field focus management and keyboard navigation

#### **Support Files**

**install.py (~200+ lines)**
Comprehensive dependency installer and system checker:
- Python version validation (3.8+ required)
- Dependency checking with detailed reporting
- Automatic package installation with pip
- System requirements verification
- Cross-platform compatibility checks

**start_server.py (~150+ lines)**
Server launcher with environment setup:
- Dependency validation before startup
- Network configuration display
- Port availability checking
- Connection information display
- Graceful error handling and user guidance

**start_client.py (~100+ lines)**
Client launcher with connection assistance:
- GUI dependency verification
- Connection help and troubleshooting
- Automatic client startup with error handling

**requirements.txt**
Comprehensive dependency specification:
- Core GUI framework (PyQt6)
- Video/image processing (OpenCV, NumPy, Pillow)
- Audio processing (PyAudio)
- Screen capture (MSS)
- Optional enhancements (pydub, psutil)

## 🖥️ Server Implementation

### **CollaborationServer Class**
The main server class implements an asyncio-based TCP server for handling multiple client connections concurrently.

#### **Initialization and Setup**
```python
class CollaborationServer:
    def __init__(self, host='0.0.0.0', port=9000):
        self.host = host
        self.port = port
        self.participants = {}  # uid -> Participant
        self.username_to_uid = {}  # username -> uid
        self.message_handlers = {}  # message_type -> handler_function
        self.setup_message_handlers()
```

#### **Message Handling System**
The server uses a message routing system for different types of communications:

**Message Types:**
- `LOGIN`: User authentication and session establishment
- `LOGOUT`: Clean disconnection handling
- `CHAT_MESSAGE`: Text message broadcasting
- `UNICAST`: Private message delivery
- `VIDEO_FRAME`: Video data routing (UDP)
- `AUDIO_FRAME`: Audio data routing (UDP)
- `PRESENT_START`: Screen sharing initiation
- `PRESENT_STOP`: Screen sharing termination
- `FILE_UPLOAD_REQUEST`: File upload initialization
- `FILE_DOWNLOAD_REQUEST`: File download request

#### **Participant Management**
```python
class Participant:
    def __init__(self, uid, username, reader, writer):
        self.uid = uid
        self.username = username
        self.reader = reader
        self.writer = writer
        self.is_presenting = False
        self.last_seen = datetime.now()
        self.video_enabled = False
        self.audio_enabled = False
```

### **UDP Media Servers**

#### **UDPVideoServer**
Handles real-time video streaming with frame distribution:
- Receives video frames from clients
- Broadcasts frames to all other participants
- Implements frame buffering for network stability
- Handles client disconnections gracefully

#### **UDPAudioServer**
Manages audio streaming with low-latency requirements:
- Processes audio packets from multiple sources
- Implements audio mixing for multiple participants
- Handles audio format conversion
- Manages audio quality adaptation

### **File Transfer Servers**

#### **FileUploadServer**
Handles file uploads with progress tracking:
- Multi-threaded upload handling
- Progress reporting to clients
- File validation and security checks
- Temporary file management during upload

#### **FileDownloadServer**
Manages file downloads with resume capability:
- Range request support for large files
- Download progress tracking
- Concurrent download handling
- File integrity verification

## 💻 Client Implementation

### **CollaborationClient Class**
The main client window inherits from QMainWindow and coordinates all client-side operations.

#### **Initialization Process**
1. **GUI Setup:** Creates all UI components and layouts
2. **Thread Creation:** Initializes worker threads for networking and media
3. **Signal Connections:** Connects Qt signals for inter-thread communication
4. **Media Initialization:** Sets up video/audio capture devices
5. **Connection Dialog:** Shows server connection interface

#### **GUI Architecture**
The client uses a sophisticated layout system:

```
┌─────────────────────────────────────────────────────────────┐
│ Menu Bar (File, View, Help)                                 │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────────────────┐ │
│ │ Left Panel (75%)    │ │ Right Panel (25%)               │ │
│ │                     │ │                                 │ │
│ │ ┌─────────────────┐ │ │ ┌─────────────────────────────┐ │ │
│ │ │ Media Controls  │ │ │ │ Chat Widget                 │ │ │
│ │ └─────────────────┘ │ │ │                             │ │ │
│ │                     │ │ │                             │ │ │
│ │ ┌─────────────────┐ │ │ ├─────────────────────────────┤ │ │
│ │ │                 │ │ │ │ Participants Widget         │ │ │
│ │ │ Video Grid      │ │ │ │                             │ │ │
│ │ │                 │ │ │ │                             │ │ │
│ │ │                 │ │ │ │                             │ │ │
│ │ └─────────────────┘ │ │ └─────────────────────────────┘ │ │
│ └─────────────────────┘ └─────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Status Bar (Connection Status, Statistics)                  │
└─────────────────────────────────────────────────────────────┘
```### **N
etworkThread Class**
Handles all TCP communication with the server using asyncio:

#### **Connection Management**
```python
class NetworkThread(QThread):
    # Signals for GUI communication
    message_received = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(bool, str)
    
    async def connect_to_server(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            self.connected = True
            self.connection_status_changed.emit(True, "Connected")
        except Exception as e:
            self.connection_status_changed.emit(False, f"Connection failed: {e}")
```

#### **Message Processing**
The network thread implements a message queue system for reliable communication:
- **Outbound Queue:** Queues messages for sending to server
- **Inbound Processing:** Parses received messages and emits signals
- **Heartbeat System:** Maintains connection with periodic ping messages
- **Reconnection Logic:** Automatic reconnection on connection loss

### **Video System Architecture**

#### **VideoClient Class**
Manages video capture and streaming:

```python
class VideoClient(QThread):
    def __init__(self, server_host, server_port):
        super().__init__()
        self.camera = cv2.VideoCapture(0)  # Default camera
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = False
        self.uid = None
        
    def run(self):
        while self.running:
            ret, frame = self.camera.read()
            if ret and self.uid:
                # Encode frame
                encoded_frame = self.encode_frame(frame)
                # Send via UDP
                self.send_frame(encoded_frame)
```

#### **Video Processing Pipeline**
1. **Capture:** OpenCV captures frames from camera
2. **Resize:** Frames resized to optimal resolution (640x480 default)
3. **Encode:** JPEG compression for network transmission
4. **Packetize:** Large frames split into UDP packets
5. **Transmit:** UDP packets sent to server
6. **Receive:** Server broadcasts to other clients
7. **Decode:** Clients decode and display frames

#### **VideoGridWidget Class**
Displays multiple video streams in a responsive grid:

```python
class VideoGridWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.participant_frames = {}  # uid -> QLabel
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        
    def add_participant_frame(self, uid, username):
        frame_widget = ParticipantVideoFrame(uid, username)
        self.participant_frames[uid] = frame_widget
        self.update_grid_layout()
        
    def update_grid_layout(self):
        # Calculate optimal grid dimensions
        count = len(self.participant_frames)
        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)
        
        # Arrange frames in grid
        for i, (uid, frame) in enumerate(self.participant_frames.items()):
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(frame, row, col)
```

### **Audio System Architecture**

#### **AudioClient Class**
Handles audio capture and streaming with PyAudio:

```python
class AudioClient(QThread):
    def __init__(self, server_host, server_port):
        super().__init__()
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def setup_audio_stream(self):
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,  # Mono for bandwidth efficiency
            rate=44100,  # Standard sample rate
            input=True,
            frames_per_buffer=1024
        )
```

#### **Audio Processing Pipeline**
1. **Capture:** PyAudio captures audio from microphone
2. **Buffer:** Audio buffered in chunks for processing
3. **Compress:** Optional audio compression for bandwidth
4. **Packetize:** Audio data split into UDP packets
5. **Transmit:** UDP packets sent to server
6. **Mix:** Server mixes multiple audio streams
7. **Distribute:** Mixed audio sent to all clients
8. **Playback:** Clients play received audio

## 🌐 Network Protocols

### **Message Format**
All TCP messages use a length-prefixed JSON format:

```
┌─────────────┬─────────────────────────────────┐
│ Length (4B) │ JSON Message Data (Variable)    │
│ Big Endian  │ UTF-8 Encoded                   │
└─────────────┴─────────────────────────────────┘
```

#### **Message Structure**
```json
{
    "type": "MESSAGE_TYPE",
    "timestamp": "2024-01-01T12:00:00.000Z",
    "uid": "unique_user_id",
    "data": {
        // Message-specific data
    }
}
```

### **UDP Packet Format**
Video and audio use custom UDP packet formats:

#### **Video Packet**
```
┌─────┬─────┬─────┬─────┬─────────────────┐
│ UID │ SEQ │ TOT │ IDX │ Frame Data      │
│ 4B  │ 4B  │ 4B  │ 4B  │ Variable        │
└─────┴─────┴─────┴─────┴─────────────────┘
```

- **UID:** User identifier (4 bytes)
- **SEQ:** Sequence number for frame ordering (4 bytes)
- **TOT:** Total packets for this frame (4 bytes)
- **IDX:** Packet index in frame (4 bytes)
- **Frame Data:** JPEG-encoded video data

#### **Audio Packet**
```
┌─────┬─────┬─────────────────┐
│ UID │ SEQ │ Audio Data      │
│ 4B  │ 4B  │ Variable        │
└─────┴─────┴─────────────────┘
```

- **UID:** User identifier (4 bytes)
- **SEQ:** Sequence number for audio ordering (4 bytes)
- **Audio Data:** Raw PCM audio data

### **Protocol State Machine**

#### **Client Connection States**
1. **DISCONNECTED:** Initial state, no connection
2. **CONNECTING:** Attempting TCP connection to server
3. **CONNECTED:** TCP connection established
4. **AUTHENTICATING:** Sending login credentials
5. **AUTHENTICATED:** Login successful, session active
6. **MEDIA_READY:** Audio/video streams initialized
7. **ACTIVE:** Full participation in session
8. **DISCONNECTING:** Graceful shutdown in progress

#### **Server Session States**
1. **WAITING:** Listening for client connections
2. **HANDSHAKE:** Processing client authentication
3. **ACTIVE:** Client fully connected and participating
4. **CLEANUP:** Removing disconnected client resources## 🎨 GUI Co
mponents

### **Main Window Layout**
The CollaborationClient uses a sophisticated layout system built with PyQt6:

#### **Layout Hierarchy**
```
QMainWindow (CollaborationClient)
├── QMenuBar
│   ├── File Menu (Connect, Exit)
│   ├── View Menu (Fullscreen, Themes)
│   └── Help Menu (About, Documentation)
├── QWidget (Central Widget)
│   └── QHBoxLayout (Main Layout)
│       ├── QWidget (Left Panel - 75% width)
│       │   └── QVBoxLayout
│       │       ├── MediaControlsWidget
│       │       └── VideoGridWidget
│       └── QWidget (Right Panel - 25% width)
│           └── QVBoxLayout
│               ├── ChatWidget
│               └── ParticipantsWidget
└── QStatusBar
    ├── Connection Status
    ├── Participant Count
    └── Network Statistics
```

### **MediaControlsWidget**
Provides intuitive controls for media functions:

#### **Button Layout**
```python
class MediaControlsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        
        # Video toggle button
        self.video_btn = QPushButton("📹 Video")
        self.video_btn.setCheckable(True)
        
        # Audio toggle button  
        self.audio_btn = QPushButton("🎤 Audio")
        self.audio_btn.setCheckable(True)
        
        # Screen share button
        self.screen_btn = QPushButton("🖥️ Share")
        self.screen_btn.setCheckable(True)
        
        # Leave button
        self.disconnect_btn = QPushButton("🚪 Leave")
```

#### **Visual States**
Each button has multiple visual states:
- **Inactive:** Grayed out when feature is disabled
- **Active:** Highlighted when feature is enabled
- **Hover:** Visual feedback on mouse hover
- **Pressed:** Animation during button press

### **ChatWidget Implementation**
Advanced text messaging interface with rich features:

#### **Message Display**
```python
class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Message display area
        self.message_display = QTextBrowser()
        self.message_display.setOpenExternalLinks(False)
        
        # Message input area
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        
        # Send button
        self.send_button = QPushButton("Send")
```

#### **Message Formatting**
The chat system supports rich text formatting:
- **System Messages:** Gray italic text for system notifications
- **Regular Messages:** Standard formatting with username and timestamp
- **Private Messages:** Special highlighting and "Private" indicator
- **Emoji Support:** Unicode emoji rendering
- **URL Detection:** Automatic link detection and formatting
- **Timestamp Display:** Relative time formatting (e.g., "2 minutes ago")

#### **Message Types**
```python
def add_message(self, username, message, is_system=False, is_private=False):
    timestamp = datetime.now().strftime("%H:%M")
    
    if is_system:
        formatted_message = f'<span style="color: #888; font-style: italic;">[{timestamp}] {message}</span>'
    elif is_private:
        formatted_message = f'<span style="color: #ff6b6b; font-weight: bold;">[{timestamp}] Private from {username}:</span> {message}'
    else:
        formatted_message = f'<span style="color: #4CAF50; font-weight: bold;">[{timestamp}] {username}:</span> {message}'
    
    self.message_display.append(formatted_message)
```

### **ParticipantsWidget**
Real-time participant management interface:

#### **Participant List**
```python
class ParticipantsWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Title label
        self.title_label = QLabel("👥 People")
        
        # Participant list
        self.participant_list = QListWidget()
        
        # Participant count
        self.count_label = QLabel("0 participants")
```

#### **Participant Item**
Each participant is displayed with:
- **Username:** Display name
- **Status Indicators:** Video/audio/screen sharing status
- **Connection Quality:** Network status indicator
- **Action Menu:** Right-click context menu for private messaging

### **VideoGridWidget**
Dynamic video layout system:

#### **Grid Calculation**
```python
def update_grid_layout(self):
    count = len(self.participant_frames)
    if count == 0:
        return
    
    # Calculate optimal grid dimensions
    if count == 1:
        cols, rows = 1, 1
    elif count <= 4:
        cols, rows = 2, 2
    elif count <= 9:
        cols, rows = 3, 3
    else:
        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)
    
    # Clear existing layout
    self.clear_layout()
    
    # Add frames to grid
    for i, (uid, frame) in enumerate(self.participant_frames.items()):
        row = i // cols
        col = i % cols
        self.grid_layout.addWidget(frame, row, col)
```

#### **ParticipantVideoFrame**
Individual video display widget:
```python
class ParticipantVideoFrame(QWidget):
    def __init__(self, uid, username):
        super().__init__()
        self.uid = uid
        self.username = username
        
        # Video display label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("border: 2px solid #555; background: #333;")
        
        # Username overlay
        self.name_label = QLabel(username)
        self.name_label.setStyleSheet("background: rgba(0,0,0,0.7); color: white; padding: 5px;")
        
        # Status indicators
        self.status_label = QLabel()
        self.update_status_indicators()
```

## 📁 File Transfer System

### **File Upload Architecture**

#### **FileUploadThread**
Handles file uploads with progress tracking:

```python
class FileUploadThread(QThread):
    progress_updated = pyqtSignal(int)  # Progress percentage
    upload_completed = pyqtSignal(str)  # Success message
    upload_failed = pyqtSignal(str)     # Error message
    
    def __init__(self, file_path, server_host, upload_port):
        super().__init__()
        self.file_path = file_path
        self.server_host = server_host
        self.upload_port = upload_port
        
    def run(self):
        try:
            file_size = os.path.getsize(self.file_path)
            filename = os.path.basename(self.file_path)
            
            # Connect to upload server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server_host, self.upload_port))
            
            # Send file metadata
            metadata = {
                'filename': filename,
                'size': file_size,
                'checksum': self.calculate_checksum()
            }
            self.send_json(sock, metadata)
            
            # Upload file in chunks
            with open(self.file_path, 'rb') as f:
                uploaded = 0
                while uploaded < file_size:
                    chunk = f.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    
                    sock.send(chunk)
                    uploaded += len(chunk)
                    
                    # Update progress
                    progress = int((uploaded / file_size) * 100)
                    self.progress_updated.emit(progress)
            
            sock.close()
            self.upload_completed.emit(f"Successfully uploaded {filename}")
            
        except Exception as e:
            self.upload_failed.emit(f"Upload failed: {str(e)}")
```

### **File Download Architecture**

#### **FileDownloadThread**
Manages file downloads with resume capability:

```python
class FileDownloadThread(QThread):
    def __init__(self, filename, server_host, download_port, save_path):
        super().__init__()
        self.filename = filename
        self.server_host = server_host
        self.download_port = download_port
        self.save_path = save_path
        
    def run(self):
        try:
            # Check if partial file exists
            partial_path = self.save_path + '.partial'
            resume_pos = 0
            if os.path.exists(partial_path):
                resume_pos = os.path.getsize(partial_path)
            
            # Connect to download server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server_host, self.download_port))
            
            # Send download request
            request = {
                'filename': self.filename,
                'resume_position': resume_pos
            }
            self.send_json(sock, request)
            
            # Receive file data
            with open(partial_path, 'ab') as f:
                while True:
                    data = sock.recv(8192)
                    if not data:
                        break
                    f.write(data)
                    
                    # Update progress
                    current_size = os.path.getsize(partial_path)
                    # Progress calculation based on expected file size
            
            # Rename completed file
            os.rename(partial_path, self.save_path)
            
        except Exception as e:
            self.download_failed.emit(f"Download failed: {str(e)}")
```

### **Drag and Drop Support**
The GUI supports drag-and-drop file uploads:

```python
def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
        event.accept()
    else:
        event.ignore()

def dropEvent(self, event):
    files = [u.toLocalFile() for u in event.mimeData().urls()]
    for file_path in files:
        if os.path.isfile(file_path):
            self.upload_file(file_path)
```#
# 🖥️ Screen Sharing System

### **Screen Capture Architecture**

#### **ScreenCaptureClient**
Captures and streams screen content:

```python
class ScreenCaptureClient(QThread):
    def __init__(self, server_host, server_port):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.running = False
        self.socket = None
        
    def run(self):
        try:
            # Connect to screen share server
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            
            # Initialize screen capture
            if HAS_SCREEN_CAPTURE:
                sct = mss.mss()
                monitor = sct.monitors[1]  # Primary monitor
            
            while self.running:
                try:
                    # Capture screen
                    if HAS_SCREEN_CAPTURE:
                        screenshot = sct.grab(monitor)
                        img = PILImage.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                    else:
                        # Fallback to PIL ImageGrab
                        img = ImageGrab.grab()
                    
                    # Convert to OpenCV format
                    img_array = np.array(img)
                    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    
                    # Resize for network efficiency
                    height, width = img_bgr.shape[:2]
                    if width > 1920:  # Limit to 1080p
                        scale = 1920 / width
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        img_bgr = cv2.resize(img_bgr, (new_width, new_height))
                    
                    # Encode as JPEG
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                    result, encoded_img = cv2.imencode('.jpg', img_bgr, encode_param)
                    
                    if result:
                        # Send image size first
                        img_size = len(encoded_img)
                        self.socket.send(struct.pack('!I', img_size))
                        
                        # Send image data
                        self.socket.send(encoded_img.tobytes())
                    
                    # Control frame rate (10 FPS for screen sharing)
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"[ERROR] Screen capture error: {e}")
                    break
                    
        except Exception as e:
            print(f"[ERROR] Screen share connection error: {e}")
        finally:
            if self.socket:
                self.socket.close()
```

### **Screen Share Viewer**

#### **ScreenShareViewer**
Displays received screen sharing content:

```python
class ScreenShareViewer(QMainWindow):
    def __init__(self, presenter_name):
        super().__init__()
        self.presenter_name = presenter_name
        self.setWindowTitle(f"Screen Share - {presenter_name}")
        self.setMinimumSize(800, 600)
        
        # Central widget for image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #000000;")
        self.setCentralWidget(self.image_label)
        
        # Receiver thread
        self.receiver = ScreenShareReceiver()
        self.receiver.image_received.connect(self.update_image)
        self.receiver.start()
        
    def update_image(self, image_data):
        try:
            # Decode image data
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                # Convert BGR to RGB
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Convert to QImage
                height, width, channel = img_rgb.shape
                bytes_per_line = 3 * width
                q_image = QImage(img_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                
                # Scale to fit window while maintaining aspect ratio
                pixmap = QPixmap.fromImage(q_image)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                self.image_label.setPixmap(scaled_pixmap)
                
        except Exception as e:
            print(f"[ERROR] Image display error: {e}")
```

#### **ScreenShareReceiver**
Receives screen sharing data from server:

```python
class ScreenShareReceiver(QThread):
    image_received = pyqtSignal(bytes)
    
    def __init__(self, server_host, server_port):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.running = False
        
    def run(self):
        try:
            # Connect to server
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            
            while self.running:
                try:
                    # Receive image size
                    size_data = self.socket.recv(4)
                    if len(size_data) != 4:
                        break
                    
                    img_size = struct.unpack('!I', size_data)[0]
                    
                    # Receive image data
                    img_data = b''
                    while len(img_data) < img_size:
                        chunk = self.socket.recv(min(img_size - len(img_data), 8192))
                        if not chunk:
                            break
                        img_data += chunk
                    
                    if len(img_data) == img_size:
                        self.image_received.emit(img_data)
                    
                except Exception as e:
                    print(f"[ERROR] Screen share receive error: {e}")
                    break
                    
        except Exception as e:
            print(f"[ERROR] Screen share connection error: {e}")
        finally:
            if hasattr(self, 'socket'):
                self.socket.close()
```

## 💬 Chat System

### **Message Processing Pipeline**

#### **Message Input Handling**
```python
def send_message(self):
    message_text = self.message_input.text().strip()
    if not message_text:
        return
    
    # Check for private message syntax: @username message
    if message_text.startswith('@'):
        parts = message_text.split(' ', 1)
        if len(parts) == 2:
            target_username = parts[0][1:]  # Remove @
            private_message = parts[1]
            self.send_private_message(target_username, private_message)
        else:
            self.add_message("System", "Invalid private message format. Use: @username message", is_system=True)
    else:
        # Regular broadcast message
        self.send_broadcast_message(message_text)
    
    self.message_input.clear()
```

#### **Message Types and Routing**

**Broadcast Messages:**
```python
def send_broadcast_message(self, message):
    chat_message = {
        'type': MessageTypes.CHAT_MESSAGE,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    self.network_thread.send_message(chat_message)
```

**Private Messages:**
```python
def send_private_message(self, target_username, message):
    private_message = {
        'type': MessageTypes.UNICAST,
        'target_username': target_username,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    self.network_thread.send_message(private_message)
```

### **Message Display System**

#### **Rich Text Formatting**
The chat widget uses HTML formatting for rich text display:

```python
def format_message(self, username, message, message_type='normal'):
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if message_type == 'system':
        return f'''
        <div style="margin: 5px 0; padding: 5px; background-color: rgba(128,128,128,0.2); border-radius: 5px;">
            <span style="color: #888; font-style: italic; font-size: 12px;">
                [{timestamp}] {message}
            </span>
        </div>
        '''
    elif message_type == 'private':
        return f'''
        <div style="margin: 5px 0; padding: 8px; background-color: rgba(255,107,107,0.2); border-left: 4px solid #ff6b6b; border-radius: 5px;">
            <span style="color: #ff6b6b; font-weight: bold; font-size: 12px;">
                [{timestamp}] Private from {username}:
            </span><br>
            <span style="color: #ffffff; margin-left: 10px;">
                {self.escape_html(message)}
            </span>
        </div>
        '''
    else:
        return f'''
        <div style="margin: 5px 0; padding: 5px;">
            <span style="color: #4CAF50; font-weight: bold; font-size: 12px;">
                [{timestamp}] {username}:
            </span>
            <span style="color: #ffffff; margin-left: 10px;">
                {self.escape_html(message)}
            </span>
        </div>
        '''
```

#### **Auto-Scroll and Message Limits**
```python
def add_message(self, username, message, is_system=False, is_private=False):
    # Determine message type
    message_type = 'system' if is_system else ('private' if is_private else 'normal')
    
    # Format and add message
    formatted_message = self.format_message(username, message, message_type)
    self.message_display.append(formatted_message)
    
    # Limit message history (keep last 1000 messages)
    document = self.message_display.document()
    if document.blockCount() > 1000:
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor, 100)
        cursor.removeSelectedText()
    
    # Auto-scroll to bottom
    scrollbar = self.message_display.verticalScrollBar()
    scrollbar.setValue(scrollbar.maximum())
```

## 🔗 Connection Management

### **Connection Dialog System**

#### **SimpleConnectionDialog**
Provides user-friendly server connection interface:

```python
class SimpleConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to Server")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        self.setup_ui()
        self.apply_styles()
        
    def accept_connection(self):
        # Validate input fields
        host = self.host_input.text().strip()
        port_text = self.port_input.text().strip()
        username = self.username_input.text().strip()
        
        # Validation logic
        if not self.validate_inputs(host, port_text, username):
            return
        
        # Store connection info
        self.connection_info = {
            'host': host,
            'port': int(port_text),
            'username': username
        }
        
        self.accept()
```

### **Connection State Management**

#### **Connection Lifecycle**
```python
def connect_to_server(self, conn_info):
    self.host = conn_info['host']
    self.port = conn_info['port']
    self.username = conn_info['username']
    
    # Test basic connectivity
    if not self.test_connection():
        return
    
    # Initialize network thread
    self.network_thread = NetworkThread(self.host, self.port, self.username)
    self.network_thread.message_received.connect(self.handle_message)
    self.network_thread.connection_status_changed.connect(self.on_connection_status_changed)
    
    # Start connection
    self.network_thread.start()
```

#### **Reconnection Logic**
```python
def handle_connection_lost(self):
    if self.auto_reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
        self.reconnect_attempts += 1
        print(f"[INFO] Attempting reconnection {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        # Wait before reconnecting
        QTimer.singleShot(5000, self.attempt_reconnection)
    else:
        self.show_reconnect_dialog()
```

### **Graceful Disconnection**

#### **Leave Button Implementation**
```python
def disconnect_from_server(self):
    print("[DEBUG] Leave button clicked - starting disconnect process")
    
    # Mark as intentional disconnect
    self._intentional_disconnect = True
    
    if self.network_thread and self.connected:
        # Send logout message to server
        logout_message = {
            'type': MessageTypes.LOGOUT,
            'timestamp': datetime.now().isoformat()
        }
        self.network_thread.send_message_sync(logout_message)
        
        # Wait for server to process
        time.sleep(0.5)
    
    # Stop all threads and cleanup
    self.cleanup_connections()
    
    # Show reconnection options
    self.show_reconnect_options()
```

#### **Cleanup Process**
```python
def cleanup_connections(self):
    # Stop network thread
    if self.network_thread:
        self.network_thread.stop()
        self.network_thread.wait()
        self.network_thread = None
    
    # Stop media clients
    if self.video_client:
        self.video_client.stop()
        self.video_client.wait()
        self.video_client = None
    
    if self.audio_client:
        self.audio_client.stop()
        self.audio_client.wait()
        self.audio_client = None
    
    # Stop screen sharing
    if hasattr(self, 'screen_capture_client') and self.screen_capture_client:
        self.screen_capture_client.stop()
        self.screen_capture_client = None
    
    # Close screen viewer
    if hasattr(self, 'screen_viewer') and self.screen_viewer:
        self.screen_viewer.close()
        self.screen_viewer = None
    
    # Reset state
    self.connected = False
    self.uid = None
    self.participants.clear()
    
    # Update UI
    self.participants_widget.update_participants({})
    self.chat_widget.clear_chat()
    self.setWindowTitle("LAN Collaboration Client")
```## 🧵 T
hreading Architecture

### **Thread Hierarchy and Communication**

The application uses a sophisticated multi-threading architecture to ensure responsive UI and efficient media processing:

```
Main GUI Thread (Qt Event Loop)
├── NetworkThread (TCP Communication)
│   ├── Async Event Loop
│   ├── Message Queue Processing
│   └── Connection Management
├── VideoClient Thread (Video Capture/Streaming)
│   ├── Camera Access
│   ├── Frame Processing
│   └── UDP Transmission
├── AudioClient Thread (Audio Capture/Streaming)
│   ├── Microphone Access
│   ├── Audio Processing
│   └── UDP Transmission
├── ScreenCaptureClient Thread (Screen Sharing)
│   ├── Screen Capture
│   ├── Image Compression
│   └── TCP Transmission
├── FileUploadThread (Per Upload)
│   ├── File Reading
│   ├── Progress Tracking
│   └── TCP Upload
└── FileDownloadThread (Per Download)
    ├── File Writing
    ├── Progress Tracking
    └── TCP Download
```

### **Inter-Thread Communication**

#### **Qt Signals and Slots**
All thread communication uses Qt's signal-slot mechanism for thread safety:

```python
class NetworkThread(QThread):
    # Signals for communicating with GUI thread
    message_received = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(bool, str)
    participant_joined = pyqtSignal(dict)
    participant_left = pyqtSignal(str)
    
    def emit_message_received(self, message):
        # This is thread-safe
        self.message_received.emit(message)

class CollaborationClient(QMainWindow):
    def __init__(self):
        super().__init__()
        # Connect signals to slots
        self.network_thread.message_received.connect(self.handle_message)
        self.network_thread.connection_status_changed.connect(self.on_connection_status_changed)
```

#### **Thread-Safe Message Queues**
```python
class NetworkThread(QThread):
    def __init__(self):
        super().__init__()
        self.message_queue = queue.Queue()
        self.queue_lock = threading.Lock()
        
    def send_message(self, message):
        with self.queue_lock:
            self.message_queue.put(message)
    
    async def process_message_queue(self):
        while self.running:
            try:
                if not self.message_queue.empty():
                    with self.queue_lock:
                        message = self.message_queue.get_nowait()
                    await self.send_to_server(message)
            except queue.Empty:
                pass
            await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
```

### **Thread Lifecycle Management**

#### **Thread Startup Sequence**
```python
def start_all_threads(self):
    # 1. Start network thread first
    self.network_thread = NetworkThread(self.host, self.port, self.username)
    self.network_thread.start()
    
    # 2. Wait for connection establishment
    while not self.network_thread.connected:
        QApplication.processEvents()
        time.sleep(0.1)
    
    # 3. Start media threads after successful connection
    if self.network_thread.connected:
        self.start_media_threads()

def start_media_threads(self):
    # Start video client
    if HAS_OPENCV:
        self.video_client = VideoClient(self.host, 10000)
        self.video_client.set_uid(self.uid)
        self.video_client.start()
    
    # Start audio client
    if HAS_PYAUDIO:
        self.audio_client = AudioClient(self.host, 11000)
        self.audio_client.set_uid(self.uid)
        self.audio_client.start()
```

#### **Thread Shutdown Sequence**
```python
def stop_all_threads(self):
    threads_to_stop = []
    
    # Collect all active threads
    if self.video_client and self.video_client.isRunning():
        threads_to_stop.append(self.video_client)
    
    if self.audio_client and self.audio_client.isRunning():
        threads_to_stop.append(self.audio_client)
    
    if self.network_thread and self.network_thread.isRunning():
        threads_to_stop.append(self.network_thread)
    
    # Stop all threads
    for thread in threads_to_stop:
        thread.stop()
    
    # Wait for all threads to finish
    for thread in threads_to_stop:
        if not thread.wait(5000):  # 5 second timeout
            print(f"[WARNING] Thread {thread.__class__.__name__} did not stop gracefully")
            thread.terminate()
```

### **Thread Synchronization**

#### **Shared Resource Protection**
```python
class VideoClient(QThread):
    def __init__(self):
        super().__init__()
        self.frame_lock = threading.Lock()
        self.current_frame = None
        self.frame_ready = threading.Event()
    
    def capture_frame(self):
        ret, frame = self.camera.read()
        if ret:
            with self.frame_lock:
                self.current_frame = frame.copy()
                self.frame_ready.set()
    
    def get_latest_frame(self):
        if self.frame_ready.wait(timeout=0.1):
            with self.frame_lock:
                frame = self.current_frame.copy() if self.current_frame is not None else None
                self.frame_ready.clear()
                return frame
        return None
```

## ⚠️ Error Handling

### **Exception Hierarchy**

#### **Custom Exception Classes**
```python
class CollaborationError(Exception):
    """Base exception for collaboration system"""
    pass

class NetworkError(CollaborationError):
    """Network-related errors"""
    pass

class MediaError(CollaborationError):
    """Media processing errors"""
    pass

class AuthenticationError(CollaborationError):
    """Authentication and authorization errors"""
    pass

class FileTransferError(CollaborationError):
    """File transfer related errors"""
    pass
```

### **Error Recovery Strategies**

#### **Network Error Recovery**
```python
class NetworkThread(QThread):
    def handle_network_error(self, error):
        error_type = type(error).__name__
        
        if isinstance(error, ConnectionResetError):
            # Server disconnected unexpectedly
            self.attempt_reconnection()
        elif isinstance(error, socket.timeout):
            # Network timeout - try to reconnect
            self.connection_status_changed.emit(False, "Connection timeout")
            self.attempt_reconnection()
        elif isinstance(error, ConnectionRefusedError):
            # Server not available
            self.connection_status_changed.emit(False, "Server unavailable")
            self.stop_reconnection_attempts()
        else:
            # Unknown network error
            self.connection_status_changed.emit(False, f"Network error: {error}")
            self.attempt_reconnection()
```

#### **Media Error Recovery**
```python
class VideoClient(QThread):
    def handle_camera_error(self, error):
        print(f"[ERROR] Camera error: {error}")
        
        # Try to reinitialize camera
        if self.camera:
            self.camera.release()
        
        # Try different camera indices
        for camera_index in range(3):
            try:
                self.camera = cv2.VideoCapture(camera_index)
                if self.camera.isOpened():
                    print(f"[INFO] Switched to camera {camera_index}")
                    return True
            except Exception as e:
                print(f"[ERROR] Camera {camera_index} failed: {e}")
        
        # No cameras available
        self.video_available = False
        self.camera_error.emit("No cameras available")
        return False
```

### **Graceful Degradation**

#### **Feature Availability Detection**
```python
def check_feature_availability(self):
    features = {
        'video': False,
        'audio': False,
        'screen_capture': False
    }
    
    # Check video capability
    try:
        import cv2
        test_camera = cv2.VideoCapture(0)
        if test_camera.isOpened():
            features['video'] = True
        test_camera.release()
    except Exception:
        pass
    
    # Check audio capability
    try:
        import pyaudio
        audio = pyaudio.PyAudio()
        # Test audio device availability
        if audio.get_device_count() > 0:
            features['audio'] = True
        audio.terminate()
    except Exception:
        pass
    
    # Check screen capture capability
    try:
        import mss
        sct = mss.mss()
        if len(sct.monitors) > 1:
            features['screen_capture'] = True
    except Exception:
        pass
    
    return features
```

#### **UI Adaptation Based on Available Features**
```python
def adapt_ui_to_features(self, features):
    # Disable video button if no camera
    if not features['video']:
        self.media_controls.video_btn.setEnabled(False)
        self.media_controls.video_btn.setToolTip("No camera available")
    
    # Disable audio button if no microphone
    if not features['audio']:
        self.media_controls.audio_btn.setEnabled(False)
        self.media_controls.audio_btn.setToolTip("No microphone available")
    
    # Disable screen share if not supported
    if not features['screen_capture']:
        self.media_controls.screen_btn.setEnabled(False)
        self.media_controls.screen_btn.setToolTip("Screen capture not available")
```

## 🚀 Performance Considerations

### **Memory Management**

#### **Video Frame Buffering**
```python
class VideoClient(QThread):
    def __init__(self):
        super().__init__()
        self.frame_buffer = collections.deque(maxlen=30)  # Keep last 30 frames
        self.buffer_lock = threading.Lock()
    
    def add_frame_to_buffer(self, frame):
        with self.buffer_lock:
            # Automatically removes oldest frame when buffer is full
            self.frame_buffer.append(frame)
    
    def cleanup_old_frames(self):
        # Explicit cleanup for memory management
        with self.buffer_lock:
            while len(self.frame_buffer) > 10:
                self.frame_buffer.popleft()
```

#### **Message History Management**
```python
class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.max_messages = 1000
        self.cleanup_threshold = 1200
    
    def add_message(self, username, message, is_system=False):
        # Add new message
        formatted_message = self.format_message(username, message, is_system)
        self.message_display.append(formatted_message)
        
        # Cleanup old messages when threshold is reached
        document = self.message_display.document()
        if document.blockCount() > self.cleanup_threshold:
            self.cleanup_old_messages()
    
    def cleanup_old_messages(self):
        document = self.message_display.document()
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        
        # Remove oldest 200 messages
        for _ in range(200):
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # Remove the newline
```

### **Network Optimization**

#### **Adaptive Video Quality**
```python
class VideoClient(QThread):
    def __init__(self):
        super().__init__()
        self.quality_levels = {
            'high': {'resolution': (1280, 720), 'quality': 90, 'fps': 30},
            'medium': {'resolution': (640, 480), 'quality': 75, 'fps': 20},
            'low': {'resolution': (320, 240), 'quality': 60, 'fps': 15}
        }
        self.current_quality = 'medium'
        self.network_stats = {'packet_loss': 0, 'latency': 0}
    
    def adapt_quality_based_on_network(self):
        if self.network_stats['packet_loss'] > 5:  # 5% packet loss
            if self.current_quality == 'high':
                self.current_quality = 'medium'
            elif self.current_quality == 'medium':
                self.current_quality = 'low'
        elif self.network_stats['packet_loss'] < 1:  # Good network
            if self.current_quality == 'low':
                self.current_quality = 'medium'
            elif self.current_quality == 'medium' and self.network_stats['latency'] < 50:
                self.current_quality = 'high'
    
    def encode_frame_with_quality(self, frame):
        quality_config = self.quality_levels[self.current_quality]
        
        # Resize frame
        resized_frame = cv2.resize(frame, quality_config['resolution'])
        
        # Encode with quality setting
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality_config['quality']]
        result, encoded_frame = cv2.imencode('.jpg', resized_frame, encode_param)
        
        return encoded_frame if result else None
```

#### **Connection Pooling for File Transfers**
```python
class FileTransferManager:
    def __init__(self, max_connections=5):
        self.connection_pool = queue.Queue(maxsize=max_connections)
        self.max_connections = max_connections
        self.active_transfers = {}
        
    def get_connection(self, host, port):
        try:
            # Try to get existing connection
            conn = self.connection_pool.get_nowait()
            if self.is_connection_valid(conn):
                return conn
        except queue.Empty:
            pass
        
        # Create new connection
        return self.create_new_connection(host, port)
    
    def return_connection(self, conn):
        if self.is_connection_valid(conn):
            try:
                self.connection_pool.put_nowait(conn)
            except queue.Full:
                # Pool is full, close connection
                conn.close()
        else:
            conn.close()
```

### **CPU Optimization**

#### **Frame Rate Control**
```python
class VideoClient(QThread):
    def __init__(self):
        super().__init__()
        self.target_fps = 20
        self.frame_interval = 1.0 / self.target_fps
        self.last_frame_time = 0
    
    def run(self):
        while self.running:
            current_time = time.time()
            
            # Check if enough time has passed for next frame
            if current_time - self.last_frame_time >= self.frame_interval:
                self.capture_and_send_frame()
                self.last_frame_time = current_time
            else:
                # Sleep for remaining time
                sleep_time = self.frame_interval - (current_time - self.last_frame_time)
                time.sleep(max(0, sleep_time))
```

## 🔒 Security Implementation

### **Input Validation**

#### **Message Sanitization**
```python
def sanitize_message(self, message):
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&']
    sanitized = message
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, f'&#{ord(char)};')
    
    # Limit message length
    max_length = 1000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized

def validate_username(self, username):
    # Username validation rules
    if not username or len(username.strip()) == 0:
        return False, "Username cannot be empty"
    
    if len(username) > 50:
        return False, "Username too long (max 50 characters)"
    
    # Allow only alphanumeric, spaces, and basic punctuation
    allowed_chars = set(string.ascii_letters + string.digits + ' .-_')
    if not all(c in allowed_chars for c in username):
        return False, "Username contains invalid characters"
    
    return True, "Valid username"
```

#### **File Upload Security**
```python
def validate_file_upload(self, file_path):
    # Check file size
    max_size = 100 * 1024 * 1024  # 100MB limit
    file_size = os.path.getsize(file_path)
    if file_size > max_size:
        raise FileTransferError(f"File too large: {file_size} bytes (max: {max_size})")
    
    # Check file extension
    allowed_extensions = {'.txt', '.pdf', '.doc', '.docx', '.jpg', '.png', '.gif', '.zip'}
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in allowed_extensions:
        raise FileTransferError(f"File type not allowed: {file_ext}")
    
    # Check filename
    filename = os.path.basename(file_path)
    if len(filename) > 255:
        raise FileTransferError("Filename too long")
    
    # Prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise FileTransferError("Invalid filename")
    
    return True
```

### **Network Security**

#### **Connection Validation**
```python
def validate_connection_request(self, client_address):
    # Rate limiting
    current_time = time.time()
    if client_address in self.connection_attempts:
        attempts = self.connection_attempts[client_address]
        # Remove old attempts (older than 1 minute)
        attempts = [t for t in attempts if current_time - t < 60]
        
        if len(attempts) >= 10:  # Max 10 attempts per minute
            return False, "Too many connection attempts"
    
    # Add current attempt
    if client_address not in self.connection_attempts:
        self.connection_attempts[client_address] = []
    self.connection_attempts[client_address].append(current_time)
    
    return True, "Connection allowed"
```

## 🔧 Extension Points

### **Plugin Architecture**

#### **Message Handler Registration**
```python
class CollaborationServer:
    def __init__(self):
        self.message_handlers = {}
        self.setup_default_handlers()
    
    def register_message_handler(self, message_type, handler_func):
        """Allow plugins to register custom message handlers"""
        self.message_handlers[message_type] = handler_func
    
    def setup_default_handlers(self):
        self.register_message_handler(MessageTypes.LOGIN, self.handle_login)
        self.register_message_handler(MessageTypes.LOGOUT, self.handle_logout)
        self.register_message_handler(MessageTypes.CHAT_MESSAGE, self.handle_chat_message)
        # ... other default handlers
```

#### **Custom Widget Integration**
```python
class CollaborationClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.plugin_widgets = {}
        self.setup_plugin_system()
    
    def register_plugin_widget(self, name, widget_class, position='right'):
        """Allow plugins to add custom widgets"""
        widget = widget_class(self)
        self.plugin_widgets[name] = widget
        
        if position == 'right':
            self.right_layout.addWidget(widget)
        elif position == 'left':
            self.left_layout.addWidget(widget)
        elif position == 'bottom':
            self.bottom_layout.addWidget(widget)
```

### **Configuration System**

#### **Settings Management**
```python
class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.default_config = {
            'video': {
                'resolution': [640, 480],
                'fps': 20,
                'quality': 75
            },
            'audio': {
                'sample_rate': 44100,
                'channels': 1,
                'buffer_size': 1024
            },
            'network': {
                'timeout': 30,
                'retry_attempts': 3,
                'buffer_size': 8192
            },
            'ui': {
                'theme': 'dark',
                'font_size': 12,
                'auto_scroll': True
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            return self.merge_configs(self.default_config, config)
        except FileNotFoundError:
            return self.default_config.copy()
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key_path, default=None):
        """Get config value using dot notation (e.g., 'video.resolution')"""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path, value):
        """Set config value using dot notation"""
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save_config()
```

## 📖 API Reference

### **Core Classes**

#### **CollaborationServer**
Main server class for handling client connections and media distribution.

**Methods:**
- `start_server()` - Start the server and begin listening for connections
- `stop_server()` - Gracefully shutdown the server
- `broadcast_message(message)` - Send message to all connected clients
- `handle_client(reader, writer)` - Handle individual client connection
- `register_message_handler(type, handler)` - Register custom message handler

#### **CollaborationClient**
Main client GUI application class.

**Methods:**
- `connect_to_server(conn_info)` - Connect to collaboration server
- `disconnect_from_server()` - Disconnect and cleanup resources
- `send_message(message)` - Send chat message
- `toggle_video(enabled)` - Enable/disable video streaming
- `toggle_audio(enabled)` - Enable/disable audio streaming
- `toggle_screen_share(enabled)` - Start/stop screen sharing

#### **NetworkThread**
Handles TCP communication with server.

**Signals:**
- `message_received(dict)` - Emitted when message received from server
- `connection_status_changed(bool, str)` - Connection status updates
- `participant_joined(dict)` - New participant notification
- `participant_left(str)` - Participant left notification

**Methods:**
- `send_message(message)` - Queue message for sending
- `send_message_sync(message)` - Send message synchronously
- `connect()` - Establish connection to server
- `disconnect()` - Close connection to server

### **Message Types**

#### **MessageTypes Enumeration**
```python
class MessageTypes:
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    CHAT_MESSAGE = "chat_message"
    UNICAST = "unicast"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    PARTICIPANT_LIST = "participant_list"
    VIDEO_FRAME = "video_frame"
    AUDIO_FRAME = "audio_frame"
    PRESENT_START = "present_start"
    PRESENT_STOP = "present_stop"
    PRESENT_START_BROADCAST = "present_start_broadcast"
    PRESENT_STOP_BROADCAST = "present_stop_broadcast"
    FILE_UPLOAD_REQUEST = "file_upload_request"
    FILE_UPLOAD_RESPONSE = "file_upload_response"
    FILE_DOWNLOAD_REQUEST = "file_download_request"
    FILE_LIST_REQUEST = "file_list_request"
    FILE_LIST_RESPONSE = "file_list_response"
```

### **Configuration Options**

#### **Server Configuration**
- `host` - Server bind address (default: '0.0.0.0')
- `port` - Main TCP port (default: 9000)
- `max_participants` - Maximum concurrent users (default: 50)
- `video_port` - UDP video streaming port (default: 10000)
- `audio_port` - UDP audio streaming port (default: 11000)
- `screen_port` - TCP screen sharing port (default: 12000)
- `upload_port` - TCP file upload port (default: 13000)
- `download_port` - TCP file download port (default: 14000)

#### **Client Configuration**
- `video_resolution` - Video capture resolution (default: [640, 480])
- `video_fps` - Video frame rate (default: 20)
- `video_quality` - JPEG compression quality (default: 75)
- `audio_sample_rate` - Audio sample rate (default: 44100)
- `audio_channels` - Audio channels (default: 1)
- `connection_timeout` - Network timeout in seconds (default: 30)
- `auto_reconnect` - Enable automatic reconnection (default: True)
- `max_reconnect_attempts` - Maximum reconnection attempts (default: 5)

This comprehensive documentation covers all aspects of the LAN Collaboration System's GUI implementation, from high-level architecture to detailed code examples and API references. The system provides a robust foundation for real-time collaboration with extensive customization and extension capabilities.