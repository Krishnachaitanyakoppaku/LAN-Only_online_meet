# Connection Troubleshooting Guide

## Issues Fixed in This Update

### 1. **Race Condition in Video Grid Initialization**
**Problem**: Video grid tried to create host slot before client_id was set
**Fix**: Delayed host slot creation until welcome message received

### 2. **File Sharing Controls Access Error**
**Problem**: Connection code tried to enable file sharing buttons before they were created
**Fix**: Added safety checks with `hasattr()` before accessing controls

### 3. **Enhanced Debugging**
**Added**: Debug prints to track connection process step by step

## Troubleshooting Steps

### **Step 1: Check Server Status**
1. **Start the server first** - Make sure server is running before connecting clients
2. **Check server logs** - Look for "Server started successfully" message
3. **Verify server IP** - Note the IP address shown in server interface

### **Step 2: Test Connection**
1. **Use Test Connection button** - Click "🔍 Test Connection" before joining
2. **Check console output** - Look for debug messages in terminal
3. **Verify IP address** - Make sure you're using the correct server IP

### **Step 3: Check Network Configuration**
1. **Same network** - Ensure server and client are on same LAN
2. **Firewall settings** - Check if firewall is blocking ports 8888, 8889, 8890
3. **Port availability** - Make sure ports are not in use by other applications

### **Step 4: Debug Connection Process**

#### **Server Side Debug Messages**
```
Server started successfully
Listening on 192.168.1.100:8888
Server waiting for client connections...
New client connection from ('192.168.1.101', 54321)
```

#### **Client Side Debug Messages**
```
Testing connection to 192.168.1.100:8888
Connection test successful
Attempting to connect to 192.168.1.100:8888
TCP connection successful
Creating UDP sockets...
UDP sockets created and bound successfully
```

## Common Issues and Solutions

### **Issue: "Connection timeout"**
**Causes**:
- Server not running
- Wrong IP address
- Network connectivity issues
- Firewall blocking connection

**Solutions**:
1. Start server first
2. Use correct IP address (check server display)
3. Test connection button first
4. Check firewall settings

### **Issue: "Connection refused"**
**Causes**:
- Server not started
- Port already in use
- Server crashed

**Solutions**:
1. Restart server
2. Check if port 8888 is available
3. Look for server error messages

### **Issue: Client connects but no video/audio**
**Causes**:
- UDP ports blocked
- Video grid initialization issues
- Media device access problems

**Solutions**:
1. Check UDP ports 8889, 8890
2. Enable camera/microphone permissions
3. Check console for video grid errors

## Network Configuration

### **Required Ports**
- **TCP 8888**: Main communication (chat, control, file sharing)
- **UDP 8889**: Video streaming
- **UDP 8890**: Audio streaming

### **Firewall Rules**
Allow incoming and outgoing traffic on:
- TCP port 8888
- UDP ports 8889, 8890

### **IP Address Configuration**
- **Server**: Binds to 0.0.0.0 (all interfaces)
- **Client**: Connects to server's LAN IP (e.g., 192.168.1.100)

## Testing Procedure

### **1. Start Server**
```
python3 server.py
# Look for: "Server started successfully"
# Note the IP address displayed
```

### **2. Test Connection**
```
python3 client.py
# Enter server IP
# Click "Test Connection"
# Should see: "Server is reachable!"
```

### **3. Join Meeting**
```
# Enter your name
# Click "Join Meeting"
# Should see: "Connected! Joining meeting..."
```

### **4. Check Debug Output**
Monitor console for debug messages to identify where the process fails.

## Fixed Issues Summary

✅ **Video grid initialization** - No more race conditions
✅ **File sharing controls** - Safe access with proper checks
✅ **Enhanced debugging** - Detailed connection process logging
✅ **Host slot creation** - Proper timing after client ID assignment
✅ **Error handling** - Better error messages and recovery

If connection issues persist after these fixes, check the debug output in the console to identify the specific failure point.