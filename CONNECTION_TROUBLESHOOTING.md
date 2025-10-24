# Connection Troubleshooting Guide

## Issue: "Connection timed out" - Client can't connect to server

### 🔍 **Diagnostic Results**
✅ All ports (8888, 8889, 8890) are available  
✅ Server code imports and initializes correctly  
✅ Python environment has all required modules  
✅ Firewall allows local connections  
❌ **No server detected listening on any port**

## 🎯 **Most Likely Causes**

### 1. **Server Not Actually Started**
**Symptoms**: Server GUI is open but no "Server Running" status
**Solution**: 
- Click the **"🚀 Start Server"** button in the server GUI
- Look for "● Server Running" status (green text)
- Check that the button changes to "⏹ Stop Server"

### 2. **Silent Server Startup Error**
**Symptoms**: Clicked start but no connections work
**Solution**:
- Check server window for error messages
- Look in server activity log for "Failed to start server" messages
- Restart the server application completely

### 3. **Wrong IP Address in Client**
**Symptoms**: Server running but client times out
**Solution**:
- **Same Machine**: Use `127.0.0.1` in client
- **Different Machines**: Use server's local IP (shown in server GUI)
- **Current Network IP**: `10.42.0.221` (from diagnostic)

## 📋 **Step-by-Step Troubleshooting**

### Step 1: Verify Server Status
1. Open server application
2. Click **"🚀 Start Server"** button
3. Confirm you see:
   - "● Server Running" (green text)
   - Button changes to "⏹ Stop Server"
   - Server IP displayed (e.g., "🌐 Server: 10.42.0.221:8888")

### Step 2: Check for Error Messages
1. Look at server activity log
2. Check for any red error messages
3. If you see "Failed to start server", restart the application

### Step 3: Test Connection
1. **Same Machine**: Use `127.0.0.1` in client
2. **Network**: Use the IP shown in server GUI
3. Click "🔍 Test Connection" in client before connecting

### Step 4: Verify Network Setup
1. Both devices on same network (WiFi/Ethernet)
2. No VPN interfering with local connections
3. Firewall allows Python applications

## 🔧 **Quick Fixes**

### Fix 1: Restart Everything
```bash
1. Close both server and client applications
2. Restart server application
3. Click "Start Server" and wait for "Server Running"
4. Start client and use correct IP address
```

### Fix 2: Use Localhost (Same Machine)
```bash
1. Run both server and client on same computer
2. Use IP address: 127.0.0.1
3. This bypasses network issues
```

### Fix 3: Check Server Logs
```bash
1. Look at server activity log panel
2. Check for error messages when starting
3. If errors appear, restart server application
```

## 🌐 **IP Address Guide**

### When to Use Each IP:
- **127.0.0.1**: Server and client on same machine
- **10.42.0.221**: Current network IP (from diagnostic)
- **192.168.x.x**: Common home network IPs
- **Server GUI Shows**: Use the IP displayed in server interface

### Finding Server IP:
1. Server GUI displays IP when running
2. Look for "🌐 Server: [IP]:[PORT]" text
3. Use that exact IP in client

## ⚠️ **Common Mistakes**

### ❌ **Don't Do This:**
- Using `0.0.0.0` in client (server binding address)
- Connecting before server shows "Running" status
- Using old/cached IP addresses
- Ignoring error messages in server log

### ✅ **Do This:**
- Wait for "Server Running" confirmation
- Use IP shown in server GUI
- Test connection before joining meeting
- Check server logs for errors

## 🚀 **Success Checklist**

Before attempting to connect:
- [ ] Server application is open
- [ ] Clicked "Start Server" button
- [ ] See "● Server Running" status
- [ ] Server shows IP address (e.g., 10.42.0.221:8888)
- [ ] Client uses same IP address as shown in server
- [ ] Both devices on same network (if different machines)

## 🔍 **Still Not Working?**

If following all steps above doesn't work:

1. **Restart Computer**: Sometimes network stack needs reset
2. **Check Antivirus**: May be blocking Python network access
3. **Try Different Port**: Change from 8888 to 9999 in both server and client
4. **Use Different Network**: Try mobile hotspot or different WiFi
5. **Check System Firewall**: Ensure Python is allowed through firewall

## 💡 **Pro Tips**

- **Test First**: Always use "Test Connection" before joining
- **Same Machine**: Start with localhost (127.0.0.1) to verify functionality
- **Network Issues**: If network doesn't work, try same machine first
- **Error Messages**: Always check server activity log for clues
- **IP Changes**: Network IP can change, always check server GUI for current IP

The diagnostic shows your system is capable of running the server correctly. The issue is most likely that the server isn't actually started or there's a silent startup error.