# Session Joining Troubleshooting Guide

## Common Issues and Solutions

### Issue: "Session not found" error when trying to join

**Possible Causes:**
1. Host hasn't created the session yet
2. Wrong session ID (IP address)
3. Network connectivity issues
4. Server not running

**Solutions:**

#### 1. Verify the Session ID
- The session ID should be the **server's IP address**
- Common formats: `192.168.1.100`, `10.0.0.5`, etc.
- **NOT** `localhost` or `127.0.0.1` (unless connecting from the same machine)

#### 2. Get the Correct Session ID
- Ask the host to check the server IP displayed at the top of their browser
- Or visit `http://[server-ip]:5000/api/server-info` to see the server IP
- Or visit `http://[server-ip]:5000/api/debug/sessions` to see active sessions

#### 3. Check Network Connectivity
- Ensure you're on the same network as the host
- Try pinging the server IP: `ping [server-ip]`
- Try accessing the server directly: `http://[server-ip]:5000`

#### 4. Verify Server is Running
- Host should see "Server Started" message
- Server should be accessible at `http://[server-ip]:5000`

### Issue: Can connect to server but session join fails

**Solutions:**
1. **Host should create session first**: Go to the main page and click "Host Session"
2. **Use exact session ID**: Copy the session ID exactly as shown by the host
3. **Check for typos**: Session IDs are case-sensitive

### Issue: Multiple users can't join the same session

**Solutions:**
1. **All users must use the same session ID** (the server's IP address)
2. **Host must create session before others join**
3. **Check server logs** for specific error messages

## Step-by-Step Joining Process

### For the Host:
1. Start the server: `python server.py`
2. Note the server IP shown in the console and browser
3. Go to `http://[server-ip]:5000`
4. Click "Host Session"
5. Enter your username
6. Click "Create Session"
7. Share the session ID (server IP) with participants

### For Participants:
1. Get the session ID from the host (should be the server's IP address)
2. Go to `http://[server-ip]:5000`
3. Click "Join Session"
4. Enter your username
5. Enter the session ID (server IP)
6. Click "Join Session"

## Debug Information

### Check Active Sessions
Visit: `http://[server-ip]:5000/api/debug/sessions`

This will show:
- All active sessions
- Connected users
- Server IP address
- Session details

### Check Server Information
Visit: `http://[server-ip]:5000/api/server-info`

This will show:
- Server IP address
- Server port
- UDP port

## Common Network Issues

### Private Networks
- Ensure all devices are on the same network
- Check firewall settings
- Some routers may block inter-device communication

### IP Address Changes
- Server IP may change if DHCP assigns a new address
- Restart the server to get the current IP
- Use static IP assignment if possible

### Port Blocking
- Default port is 5000
- Ensure port 5000 is not blocked by firewall
- Try different port if needed: `python server.py --port 8080`

## Still Having Issues?

1. **Check server console logs** for detailed error messages
2. **Check browser console** (F12) for JavaScript errors
3. **Verify network connectivity** between all devices
4. **Restart the server** and try again
5. **Use the debug endpoints** to see current server state

## Example Working Setup

```
Network: 192.168.1.0/24
Server IP: 192.168.1.100
Server URL: http://192.168.1.100:5000
Session ID: 192.168.1.100

Host: Creates session with ID "192.168.1.100"
Client 1: Joins session with ID "192.168.1.100"  
Client 2: Joins session with ID "192.168.1.100"
```

All participants must use the **same session ID** (the server's IP address).