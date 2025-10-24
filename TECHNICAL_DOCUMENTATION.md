# LAN Communication System - Technical Documentation

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Communication Protocols](#communication-protocols)
3. [Network Implementation](#network-implementation)
4. [Media Processing](#media-processing)
5. [File Transfer System](#file-transfer-system)
6. [Session Management](#session-management)
7. [Security Considerations](#security-considerations)
8. [Performance Optimization](#performance-optimization)
9. [API Reference](#api-reference)
10. [Troubleshooting Guide](#troubleshooting-guide)

## System Architecture

### Overview

The LAN Communication System follows a centralized client-server architecture designed for real-time multi-user communication within local area networks.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Client 1    │    │     Client 2    │    │     Client N    │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   Video     │ │    │ │   Video     │ │    │ │   Video     │ │
│ │   Audio     │ │    │ │   Audio     │ │    │ │   Audio     │ │
│ │   Chat      │ │    │ │   Chat      │ │    │ │   Chat      │ │
│ │   Files     │ │    │ │   Files     │ │    │ │   Files     │ │
│ │   Screen    │ │    │ │   Screen    │ │    │ │   Screen    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ TCP/UDP              │ TCP/UDP              │ TCP/UDP
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      Central Server       │
                    │                           │
                    │ ┌─────────────────────┐   │
                    │ │  Session Manager    │   │
                    │ │  Message Router     │   │
                    │ │  Media Relay        │   │
                    │ │  File Manager       │   │
                    │ │  Client Registry    │   │
                    │ └─────────────────────┘   │
                    └───────────────────────────┘
```

### Core Components

#### Server Components

1. **Session Manager**: Handles client connections and session state
2. **Message Router**: Routes messages between clients
3. **Media Relay**: Processes and forwards video/audio streams
4. **File Manager**: Manages file transfers and storage
5. **Client Registry**: Maintains client information and status

#### Client Components

1. **Connection Manager**: Handles server communication
2. **Media Capture**: Video and audio input processing
3. **Media Renderer**: Video and audio output processing
4. **UI Controller**: User interface management
5. **File Handler**: File sharing functionality

## Communication Protocols

### Protocol Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │    Chat     │ │    Files    │ │   Screen Share  │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                   Transport Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │     TCP     │ │     UDP     │ │      UDP        │   │
│  │  (Control)  │ │   (Video)   │ │    (Audio)      │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                    Network Layer                        │
│                      IP (IPv4)                          │
├─────────────────────────────────────────────────────────┤
│                   Data Link Layer                       │
│                   Ethernet/WiFi                         │
└─────────────────────────────────────────────────────────┘
```

### Message Format

#### TCP Messages (Control, Chat, Files)

```json
{
  "type": "message_type",
  "client_id": 12345,
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    // Message-specific data
  }
}
```

#### UDP Video Packets

```
┌─────────────┬─────────────┬─────────────┬─────────────────┐
│  Client ID  │  Sequence   │ Frame Size  │   Frame Data    │
│   (4 bytes) │  (4 bytes)  │  (4 bytes)  │   (variable)    │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

#### UDP Audio Packets

```
┌─────────────┬─────────────┬─────────────────────────────────┐
│  Client ID  │ Timestamp   │         Audio Data              │
│   (4 bytes) │  (4 bytes)  │         (variable)              │
└─────────────┴─────────────┴─────────────────────────────────┘
```

### Message Types

#### Control Messages

- `join`: Client joining session
- `leave`: Client leaving session
- `heartbeat`: Keep-alive message
- `status_update`: Client status change

#### Chat Messages

- `chat`: Text message
- `chat_history`: Historical messages
- `user_typing`: Typing indicator

#### Media Messages

- `video_status`: Video enable/disable
- `audio_status`: Audio enable/disable
- `video_frame`: Video frame data
- `audio_chunk`: Audio data chunk

#### Presentation Messages

- `request_presenter`: Request presenter role
- `presenter_granted`: Presenter role granted
- `presenter_denied`: Presenter role denied
- `screen_frame`: Screen sharing frame
- `stop_presenting`: Stop presentation

#### File Messages

- `file_offer`: Offer file for sharing
- `file_request`: Request file download
- `file_chunk`: File data chunk
- `file_complete`: File transfer complete

## Network Implementation

### Port Allocation

- **TCP Port 8888**: Control messages, chat, file transfers
- **UDP Port 8889**: Video streaming
- **UDP Port 8890**: Audio streaming

### Connection Management

#### Server Socket Initialization

```python
# TCP Control Socket
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_socket.bind(('0.0.0.0', 8888))
tcp_socket.listen(10)

# UDP Video Socket
udp_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_video_socket.bind(('0.0.0.0', 8889))

# UDP Audio Socket
udp_audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_audio_socket.bind(('0.0.0.0', 8890))
```

#### Client Connection Process

1. **TCP Connection**: Establish control channel
2. **Authentication**: Send client credentials
3. **Session Join**: Receive session state
4. **UDP Setup**: Configure media channels
5. **Ready State**: Begin communication

### Error Handling

#### Connection Errors

- **Timeout**: Implement connection timeouts
- **Retry Logic**: Automatic reconnection attempts
- **Graceful Degradation**: Continue with available features

#### Network Errors

- **Packet Loss**: UDP packet sequence tracking
- **Bandwidth Issues**: Adaptive quality adjustment
- **Latency Problems**: Buffer management

## Media Processing

### Video Processing Pipeline

#### Capture → Encode → Transmit → Decode → Display

```python
# Video Capture
cap = cv2.VideoCapture(0)
ret, frame = cap.read()

# Preprocessing
frame = cv2.resize(frame, (640, 480))
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

# Compression (simplified)
_, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

# Transmission
packet = struct.pack('!III', client_id, sequence, len(encoded)) + encoded.tobytes()
udp_socket.sendto(packet, server_address)
```

#### Video Quality Adaptation

- **Resolution Scaling**: Adjust based on bandwidth
- **Frame Rate Control**: Dynamic FPS adjustment
- **Compression Levels**: Quality vs. bandwidth trade-off

### Audio Processing Pipeline

#### Capture → Process → Transmit → Mix → Playback

```python
# Audio Capture
chunk = 1024
format = pyaudio.paInt16
channels = 1
rate = 44100

stream = audio.open(format=format, channels=channels,
                   rate=rate, input=True, frames_per_buffer=chunk)
data = stream.read(chunk)

# Transmission
packet = struct.pack('!II', client_id, timestamp) + data
udp_socket.sendto(packet, server_address)
```

#### Audio Processing Features

- **Noise Reduction**: Basic noise filtering
- **Echo Cancellation**: Prevent audio feedback
- **Volume Normalization**: Consistent audio levels
- **Mixing**: Server-side audio combination

### Screen Sharing

#### Screen Capture Process

```python
import mss

# Screen capture
with mss.mss() as sct:
    screenshot = sct.grab(sct.monitors[1])
    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

# Compression
img.thumbnail((1024, 768), Image.Resampling.LANCZOS)
buffer = io.BytesIO()
img.save(buffer, format='JPEG', quality=70)
```

## File Transfer System

### Transfer Protocol

#### File Sharing Process

1. **File Selection**: Client selects file to share
2. **Metadata Exchange**: Send file information
3. **Chunked Transfer**: Split file into chunks
4. **Progress Tracking**: Monitor transfer progress
5. **Integrity Check**: Verify file completeness

#### Chunk Format

```
┌─────────────┬─────────────┬─────────────┬─────────────────┐
│   File ID   │  Chunk ID   │ Chunk Size  │   Chunk Data    │
│   (4 bytes) │  (4 bytes)  │  (4 bytes)  │   (variable)    │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

### File Management

#### Server-Side Storage

- **Temporary Storage**: Files stored during session
- **Metadata Tracking**: File information database
- **Access Control**: Client permission management
- **Cleanup**: Automatic file removal after session

#### Client-Side Handling

- **Upload Queue**: Manage multiple uploads
- **Download Manager**: Handle concurrent downloads
- **Progress Display**: Real-time transfer status
- **Error Recovery**: Resume interrupted transfers

## Session Management

### Client Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Disconnected│───▶│ Connecting  │───▶│   Active    │───▶│Disconnecting│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ▲                                       │                   │
       │                                       ▼                   │
       └───────────────────────────────────────────────────────────┘
```

### State Management

#### Server State

- **Client Registry**: Active client list
- **Session State**: Current session information
- **Presenter Status**: Current presenter information
- **File Registry**: Available files list

#### Client State

- **Connection Status**: Network connection state
- **Media Status**: Video/audio enable state
- **UI State**: Current interface state
- **Session Data**: Cached session information

### Heartbeat System

#### Keep-Alive Mechanism

```python
# Client heartbeat
def send_heartbeat():
    while connected:
        heartbeat_msg = {'type': 'heartbeat', 'timestamp': time.time()}
        send_tcp_message(heartbeat_msg)
        time.sleep(30)  # Send every 30 seconds

# Server monitoring
def check_client_timeouts():
    current_time = time.time()
    for client_id, client_info in clients.items():
        if current_time - client_info['last_seen'] > 60:  # 60 second timeout
            disconnect_client(client_id)
```

## Security Considerations

### Network Security

#### LAN-Only Operation

- **No Internet Access**: All communication stays within LAN
- **Network Isolation**: Prevents external access
- **Firewall Configuration**: Proper port management

#### Data Integrity

- **TCP for Critical Data**: Reliable delivery for control messages
- **Checksum Verification**: File transfer integrity
- **Message Validation**: Input sanitization

### Authentication

#### Basic Client Authentication

```python
def authenticate_client(client_socket, credentials):
    # Basic name-based identification
    client_name = credentials.get('name')
    if not client_name or len(client_name) > 50:
        return False
    return True
```

#### Future Security Enhancements

- **Encryption**: End-to-end message encryption
- **Digital Signatures**: Message authenticity
- **Access Control**: Role-based permissions
- **Audit Logging**: Security event tracking

## Performance Optimization

### Network Optimization

#### Bandwidth Management

- **Adaptive Bitrate**: Adjust quality based on network conditions
- **Traffic Shaping**: Prioritize different data types
- **Compression**: Efficient data encoding

#### Latency Reduction

- **UDP for Media**: Low-latency streaming
- **Buffer Management**: Minimize buffering delays
- **Local Processing**: Reduce server load

### Memory Management

#### Client-Side Optimization

```python
# Efficient frame processing
def process_video_frame(frame):
    # Reuse buffers to reduce garbage collection
    if not hasattr(process_video_frame, 'buffer'):
        process_video_frame.buffer = np.empty((480, 640, 3), dtype=np.uint8)

    # Process frame in-place
    cv2.resize(frame, (640, 480), dst=process_video_frame.buffer)
    return process_video_frame.buffer
```

#### Server-Side Optimization

- **Connection Pooling**: Reuse network connections
- **Memory Pools**: Reduce allocation overhead
- **Garbage Collection**: Minimize GC pressure

### CPU Optimization

#### Multi-threading Strategy

- **I/O Threads**: Separate network operations
- **Processing Threads**: Dedicated media processing
- **UI Thread**: Responsive user interface

#### Resource Monitoring

```python
import psutil

def monitor_resources():
    cpu_percent = psutil.cpu_percent()
    memory_info = psutil.virtual_memory()

    if cpu_percent > 80:
        # Reduce video quality
        adjust_video_quality(0.8)

    if memory_info.percent > 85:
        # Trigger garbage collection
        gc.collect()
```

## API Reference

### Server API

#### Core Server Class

```python
class LANCommunicationServer:
    def __init__(self):
        """Initialize server with default configuration"""

    def start_server(self):
        """Start the communication server"""

    def stop_server(self):
        """Stop the server and disconnect all clients"""

    def broadcast_message(self, message, exclude=None):
        """Broadcast message to all connected clients"""

    def send_to_client(self, client_id, message):
        """Send message to specific client"""
```

#### Message Handling

```python
def process_client_message(self, client_id, message):
    """Process incoming message from client"""

def handle_tcp_client(self, client_id):
    """Handle TCP communication with client"""

def handle_udp_video(self):
    """Handle UDP video streaming"""

def handle_udp_audio(self):
    """Handle UDP audio streaming"""
```

### Client API

#### Core Client Class

```python
class LANCommunicationClient:
    def __init__(self):
        """Initialize client with default configuration"""

    def connect_to_server(self):
        """Connect to communication server"""

    def disconnect(self):
        """Disconnect from server"""

    def send_tcp_message(self, message):
        """Send TCP message to server"""
```

#### Media Control

```python
def toggle_video(self):
    """Toggle video on/off"""

def toggle_audio(self):
    """Toggle audio on/off"""

def toggle_presentation(self):
    """Toggle presentation mode"""

def send_chat_message(self, message):
    """Send chat message"""
```

## Troubleshooting Guide

### Common Issues

#### Connection Problems

**Issue**: Cannot connect to server

```
Symptoms: "Connection refused" error
Causes:
- Server not running
- Wrong IP address
- Firewall blocking ports
- Network connectivity issues

Solutions:
1. Verify server is running
2. Check IP address configuration
3. Test network connectivity: ping server_ip
4. Check firewall settings
5. Verify port availability: netstat -an | grep 8888
```

**Issue**: Frequent disconnections

```
Symptoms: Clients randomly disconnect
Causes:
- Network instability
- Firewall interference
- Resource exhaustion

Solutions:
1. Check network stability
2. Increase heartbeat timeout
3. Monitor server resources
4. Review firewall logs
```

#### Media Problems

**Issue**: No video display

```
Symptoms: Black video area or error messages
Causes:
- Camera permission denied
- Camera in use by another application
- Driver issues

Solutions:
1. Check camera permissions
2. Close other camera applications
3. Test camera with test_system.py
4. Update camera drivers
5. Try different camera index
```

**Issue**: Audio not working

```
Symptoms: No audio input/output
Causes:
- Microphone/speaker permissions
- Audio device conflicts
- Driver issues

Solutions:
1. Check audio permissions
2. Test audio devices
3. Verify default audio devices
4. Update audio drivers
5. Check system audio settings
```

#### Performance Issues

**Issue**: High CPU usage

```
Symptoms: System slowdown, high CPU in task manager
Causes:
- High video resolution/framerate
- Multiple video streams
- Inefficient processing

Solutions:
1. Reduce video resolution
2. Lower frame rate
3. Close unnecessary applications
4. Upgrade hardware
5. Optimize video settings
```

**Issue**: Network lag

```
Symptoms: Delayed video/audio, choppy playback
Causes:
- Network congestion
- Insufficient bandwidth
- High latency

Solutions:
1. Use wired connection
2. Reduce video quality
3. Check network utilization
4. Optimize network settings
5. Upgrade network infrastructure
```

### Diagnostic Tools

#### Built-in Diagnostics

```bash
# Test system components
python test_system.py

# Check installation
python install.py

# Monitor server logs
# Check server GUI activity log
```

#### Network Diagnostics

```bash
# Test connectivity
ping server_ip

# Check port availability
telnet server_ip 8888

# Monitor network traffic
netstat -an | grep 888

# Check bandwidth
iperf3 -c server_ip
```

#### System Diagnostics

```bash
# Check system resources
top
htop

# Monitor disk usage
df -h

# Check memory usage
free -m

# Monitor processes
ps aux | grep python
```

### Log Analysis

#### Server Logs

- Connection events
- Error messages
- Performance metrics
- Client activities

#### Client Logs

- Connection status
- Media events
- Error conditions
- Performance data

### Recovery Procedures

#### Server Recovery

1. Stop server gracefully
2. Check system resources
3. Review error logs
4. Restart server
5. Monitor stability

#### Client Recovery

1. Disconnect from server
2. Check local resources
3. Restart client application
4. Reconnect to server
5. Verify functionality

---

This technical documentation provides comprehensive information for developers, system administrators, and advanced users working with the LAN Communication System. For additional support, refer to the README.md file and the built-in diagnostic tools.
