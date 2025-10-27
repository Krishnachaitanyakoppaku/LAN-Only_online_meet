# 🚀 LAN Communication Hub - Auto Setup

This setup automatically handles SSH tunnels for seamless camera/microphone access across different machines.

## 🎯 Quick Start

### For Server (Host):
```bash
python3 start_server.py
```

This will:
- ✅ Start the server automatically
- ✅ Detect server IP address automatically
- ✅ Create client connection scripts
- ✅ Show connection instructions

### For Clients (Participants):
```bash
python3 connect_client.py
```

This will:
- ✅ Scan network for servers automatically
- ✅ Test SSH connection
- ✅ Setup SSH tunnel automatically
- ✅ Provide localhost access for camera/microphone

## 📋 Step-by-Step Instructions

### 1. Start Server
On the host machine:
```bash
python3 start_server.py
```
The script will automatically detect and display the server IP.

### 2. Connect Clients
On each client machine:
```bash
python3 connect_client.py
```
The script will automatically scan for and detect available servers.

### 3. Access Application
- **Host**: Go to `http://localhost:5000` or `http://[detected-server-ip]:5000`
- **Clients**: Go to `http://localhost:5000` (after SSH tunnel)

### 4. Join Session
- **Host**: Create session (session ID will be auto-detected server IP)
- **Clients**: Join with session ID: `[server-ip]` (displayed by server script)

## 🔧 Manual Setup (Alternative)

If automatic setup doesn't work:

### Manual SSH Tunnel:
```bash
ssh -L 5000:[server-ip]:5000 username@[server-ip]
```
Replace `[server-ip]` with the actual server IP detected by the start_server.py script.

### Generated Scripts:
The `start_server.py` creates these scripts for clients:
- `client_connect.bat` (Windows)
- `client_connect.sh` (Linux/Mac)
- `client_connect.py` (Cross-platform)

## 🎯 Why SSH Tunnel?

**Problem**: Modern browsers require HTTPS for camera/microphone on remote connections
**Solution**: SSH tunnel makes remote server appear as localhost
**Result**: Camera/microphone works on HTTP via localhost

## 🔍 Troubleshooting

### If SSH tunnel fails:
1. Check SSH is installed: `ssh -V`
2. Test manual connection: `ssh username@[server-ip]`
3. Verify server IP and username are correct
4. Check network connectivity

### If camera/microphone still doesn't work:
1. Go to: `http://localhost:5000/media-test`
2. Check browser permissions
3. Try different browser
4. Clear browser cache/cookies

### Debug URLs:
- Media test: `http://[server-ip]:5000/media-test`
- Host method check: `http://[server-ip]:5000/check-host-method`

## 🎉 Expected Results

After setup:
- ✅ Host can access camera/microphone
- ✅ Clients can access camera/microphone (via SSH tunnel)
- ✅ Bidirectional video/audio streaming works
- ✅ All users can see and hear each other

## 📞 Connection Summary

| Machine | Access Method | URL | Camera/Mic |
|---------|---------------|-----|------------|
| Host | Direct | http://localhost:5000 | ✅ Works |
| Client | SSH Tunnel | http://localhost:5000 | ✅ Works |
| Client (Direct) | Direct | http://[server-ip]:5000 | ❌ May fail |

The SSH tunnel ensures all clients have the same access context as the host!