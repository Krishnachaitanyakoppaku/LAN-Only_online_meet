# Multi-Client Video and Audio Features

## Overview
The LAN Communication System now supports full multi-client video and audio streaming between all participants (clients and host).

## Video Streaming Flow

### Client to Server to Clients
```
Client A Video → Server → Client B, Client C, Host
Client B Video → Server → Client A, Client C, Host  
Client C Video → Server → Client A, Client B, Host
Host Video → Server → Client A, Client B, Client C
```

### How It Works
1. **Client Sends Video**: Each client captures video and sends UDP packets to server
2. **Server Receives**: Server receives video from all clients and host
3. **Server Displays**: Server displays each client's video in participant grid
4. **Server Broadcasts**: Server forwards each client's video to all other clients
5. **Clients Receive**: Each client receives video from all other participants
6. **Clients Display**: Clients show remote video in main display area

## Audio Streaming Flow

### Client to Server to Clients
```
Client A Audio → Server → Client B, Client C, Host
Client B Audio → Server → Client A, Client C, Host
Client C Audio → Server → Client A, Client B, Host  
Host Audio → Server → Client A, Client B, Client C
```

### How It Works
1. **Client Sends Audio**: Each client captures microphone audio and sends UDP packets
2. **Server Receives**: Server receives audio from all clients and host
3. **Server Broadcasts**: Server forwards each client's audio to all other clients
4. **Clients Receive**: Each client receives audio from all other participants
5. **Clients Play**: Clients play received audio through speakers/headphones

## Technical Implementation

### Video Features
- ✅ **Client Video Capture**: OpenCV camera access
- ✅ **Client Video Sending**: UDP packets to server with client_id
- ✅ **Server Video Reception**: Receives and processes client video frames
- ✅ **Server Video Display**: Shows client video in participant grid
- ✅ **Server Video Broadcasting**: Forwards client video to other clients
- ✅ **Client Video Reception**: Receives video from other clients and host
- ✅ **Client Video Display**: Shows remote video in main display area
- ✅ **Local Video Preview**: Clients see their own video in preview area

### Audio Features
- ✅ **Client Audio Capture**: PyAudio microphone access
- ✅ **Client Audio Sending**: UDP packets to server with client_id
- ✅ **Server Audio Reception**: Receives and processes client audio
- ✅ **Server Audio Broadcasting**: Forwards client audio to other clients
- ✅ **Client Audio Reception**: Receives audio from other clients and host
- ✅ **Client Audio Playback**: Plays received audio through output stream
- ✅ **Dual Audio Streams**: Separate input (mic) and output (speakers) streams

### Network Protocol

#### Video Packet Format
```
┌─────────────┬─────────────┬─────────────┬─────────────────┐
│  Client ID  │  Sequence   │ Frame Size  │   Frame Data    │
│   (4 bytes) │  (4 bytes)  │  (4 bytes)  │   (variable)    │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

#### Audio Packet Format
```
┌─────────────┬─────────────┬─────────────────────────────────┐
│  Client ID  │ Timestamp   │         Audio Data              │
│   (4 bytes) │  (4 bytes)  │         (variable)              │
└─────────────┴─────────────┴─────────────────────────────────┘
```

### Port Usage
- **TCP 8888**: Control messages, chat, file sharing
- **UDP 8889**: Video streaming (all participants)
- **UDP 8890**: Audio streaming (all participants)

## User Experience

### What Users See
1. **Own Video**: In small preview area (bottom left)
2. **Remote Video**: In main display area (center)
3. **Participant List**: Shows all connected users with status
4. **Audio Indicators**: Visual feedback for who's speaking
5. **Video Controls**: Toggle video/audio on/off independently

### Multi-Participant Scenarios

#### 3 Clients + Host
- **Host sees**: Video from Client A, B, C in participant grid
- **Client A sees**: Host video in main area, own video in preview
- **Client B sees**: Host video in main area, own video in preview  
- **Client C sees**: Host video in main area, own video in preview
- **All hear**: Mixed audio from all other participants

#### Client-to-Client Communication
- When Host is not broadcasting video, clients see each other's video
- Audio is always mixed from all active participants
- Server acts as relay for all media streams

## Quality and Performance

### Video Quality
- **Resolution**: 320x240 for transmission, scaled for display
- **Compression**: JPEG with 70% quality for bandwidth efficiency
- **Frame Rate**: ~20 FPS for smooth video
- **Adaptive**: Can be adjusted based on network conditions

### Audio Quality  
- **Format**: 16-bit PCM, 44.1kHz, mono
- **Latency**: Low-latency UDP transmission
- **Mixing**: Server-side audio combination
- **Buffering**: Minimal buffering for real-time feel

### Network Efficiency
- **UDP Streaming**: Low-latency for media
- **TCP Control**: Reliable for chat/files
- **Bandwidth**: Optimized compression and frame rates
- **Scalability**: Supports multiple simultaneous streams

## Troubleshooting

### Common Issues
1. **No Video**: Check camera permissions and availability
2. **No Audio**: Check microphone/speaker permissions
3. **Choppy Video**: Reduce quality or check network bandwidth
4. **Audio Echo**: Use headphones instead of speakers
5. **Connection Issues**: Verify firewall and port settings

### Debug Features
- Console output for connection status
- Error messages for media device issues
- Network packet validation
- Automatic reconnection attempts

## Future Enhancements
- **Video Grid**: Multiple video streams in grid layout
- **Audio Mixing**: Advanced server-side audio processing
- **Quality Adaptation**: Automatic quality adjustment
- **Recording**: Save video/audio sessions
- **Screen Sharing**: Share screen with all participants