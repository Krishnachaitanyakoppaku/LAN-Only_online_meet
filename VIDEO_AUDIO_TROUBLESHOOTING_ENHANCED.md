# Enhanced Video and Audio Troubleshooting

## Issues Being Investigated

### 1. **Client Video Not Visible on Server**
### 2. **Audio Not Working Properly on Server and Client**

## Enhanced Debugging Added

### **Server Side Debugging**
```python
# Video Grid Updates
print(f"Updating video grid - clients: {len(self.clients)}")
print(f"Created video label for client {client_id}: {client_info['name']}")

# Video Display Updates  
print(f"Attempting to update video display for client {client_id}")
print(f"Available video labels: {list(self.video_labels.keys())}")

# Video Reception
print(f"Server received video from client {client_id}, size: {frame_size} bytes")
print(f"Known clients: {list(self.clients.keys())}")

# Audio Initialization
print("Starting host speaker...")
print("Host speaker started successfully")
```

### **Client Side Debugging**
```python
# Audio Initialization
print("Starting client speaker...")
print("Client speaker started successfully")

# Video Loop Status
print(f"Video loop started - enabled: {self.video_enabled}")
print(f"Video loop ended - enabled: {self.video_enabled}")
```

## Diagnostic Steps

### **Step 1: Check Server Video Grid Creation**
When clients join, you should see:
```
Updating video grid - clients: 1
Created video label for client 1: User_123
```

If you don't see this, the video grid isn't being created properly.

### **Step 2: Check Video Reception on Server**
When client sends video, you should see:
```
Server received video from client 1, size: 1234 bytes
Attempting to update video display for client 1
Available video labels: [1]
Server updated display for client 1
```

### **Step 3: Check Audio Initialization**
When server/client starts, you should see:
```
Starting host speaker...
Host speaker started successfully
Starting client speaker...
Client speaker started successfully
```

### **Step 4: Check Audio Transmission**
When client sends audio, you should see:
```
Audio sent: Client 1, 1024 bytes
Server received audio from client 1, 1024 bytes
Server playing audio from client 1
```

## Common Issues and Solutions

### **Issue: Video Grid Not Created**
**Symptoms**: No "Created video label" messages
**Causes**: 
- `video_grid_frame` not initialized
- `update_video_grid()` not called when clients join

**Solution**: Check server GUI initialization

### **Issue: Video Labels Not Found**
**Symptoms**: "Available video labels: []" when trying to update
**Causes**:
- Video grid cleared but not recreated
- Client ID mismatch

**Solution**: Ensure video grid is properly recreated when clients join/leave

### **Issue: Audio Not Initializing**
**Symptoms**: No "speaker started successfully" messages
**Causes**:
- PyAudio not available
- Audio device access issues
- Permission problems

**Solutions**:
1. Check PyAudio installation: `pip install pyaudio`
2. Check audio device permissions
3. Try different audio devices

### **Issue: Video Frames Not Received**
**Symptoms**: No "Server received video" messages
**Causes**:
- UDP port blocked
- Client not sending video
- Network connectivity issues

**Solutions**:
1. Check UDP port 8889 is open
2. Verify client video is enabled
3. Check network connectivity

## Testing Protocol

### **1. Start Server**
```bash
python3 server.py
```
**Expected Output**:
```
Server started successfully
Starting host speaker...
Host speaker started successfully
```

### **2. Connect Client**
```bash
python3 client.py
```
**Expected Output**:
```
Connected! Joining meeting...
Starting client speaker...
Client speaker started successfully
```

**Server Should Show**:
```
Updating video grid - clients: 1
Created video label for client 1: User_123
```

### **3. Enable Client Video**
Click video button on client.

**Expected Output**:
```
Video loop started - enabled: true
Video frame sent to server - Client ID: 1, Size: 1234 bytes
```

**Server Should Show**:
```
Server received video from client 1, size: 1234 bytes
Attempting to update video display for client 1
Available video labels: [1]
Server updated display for client 1
```

### **4. Enable Client Audio**
Click microphone button on client.

**Expected Output**:
```
Audio sent: Client 1, 1024 bytes
```

**Server Should Show**:
```
Server received audio from client 1, 1024 bytes
Server playing audio from client 1
```

## Troubleshooting Commands

### **Check Audio Devices**
```python
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"Device {i}: {info['name']}")
```

### **Check Network Connectivity**
```bash
# Test UDP ports
nc -u -l 8889  # On server
nc -u server_ip 8889  # On client
```

### **Check Video Capture**
```python
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f"Camera working: {ret}")
```

## Expected Debug Flow

### **Successful Video Flow**:
1. Server: "Updating video grid - clients: 1"
2. Server: "Created video label for client 1"
3. Client: "Video loop started"
4. Client: "Video frame sent to server"
5. Server: "Server received video from client 1"
6. Server: "Server updated display for client 1"

### **Successful Audio Flow**:
1. Server: "Starting host speaker... Host speaker started successfully"
2. Client: "Starting client speaker... Client speaker started successfully"
3. Client: "Audio sent: Client 1, 1024 bytes"
4. Server: "Server received audio from client 1, 1024 bytes"
5. Server: "Server playing audio from client 1"

## Next Steps

Run the server and client with these enhanced debug messages and check the console output. The debug messages will help identify exactly where the video and audio pipelines are failing.

If you see all the expected messages but still no video/audio, the issue might be with:
1. GUI display updates (video)
2. Audio device configuration (audio)
3. Frame encoding/decoding (video)
4. Audio format compatibility (audio)

Share the debug output to identify the specific failure point!