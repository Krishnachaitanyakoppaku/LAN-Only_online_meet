# Testing Guide - LAN Communication Hub

## Quick Test Steps

### 1. Start the Server
```bash
python3 start_server.py
```
or
```bash
python3 server.py
```

### 2. Test Session Creation
1. Open browser to `http://localhost:5000`
2. Click "Host Session"
3. Enter your username (e.g., "HostUser")
4. Leave session ID empty for auto-generation
5. Click "Start Session"

**Expected Result**: You should see a modal with:
- Session ID displayed (e.g., "session_1234567890")
- Copy buttons for Session ID and Share URL
- List of participants (just you)
- "Enter Session" button

### 3. Test Session Joining
1. Open another browser tab/window to `http://localhost:5000`
2. Click "Join Session"
3. Enter a different username (e.g., "JoinUser")
4. Enter the Session ID from step 2
5. Click "Join Session"

**Expected Result**: You should be redirected to the session page with:
- Session ID displayed in header
- Your username shown
- Both users in participants list
- Video/audio controls available

### 4. Test URL Sharing
1. Copy the "Share this URL" from the session creation modal
2. Open the URL in a new browser tab
3. The session ID should be auto-filled
4. Enter a username and join

## Troubleshooting

### If Session Creation Fails
- Check browser console (F12) for errors
- Check server terminal for error messages
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### If Session Joining Fails
- Verify the session ID is correct (case-sensitive)
- Check if the session still exists (sessions expire when empty)
- Check browser console and server logs

### If Video/Audio Doesn't Work
- Allow camera/microphone permissions when prompted
- Check if other applications are using the camera
- Try a different browser (Chrome/Firefox recommended)

### Common Issues
1. **"Session not found"**: The session ID is incorrect or the session expired
2. **"Connection failed"**: Server is not running or port 5000 is blocked
3. **"No session data found"**: Trying to access session page without proper session data

## Debug Information

### Server Logs
The server will show:
- Connection/disconnection events
- Session creation/joining attempts
- Error messages

### Browser Console
Press F12 and check Console tab for:
- JavaScript errors
- Socket connection status
- Session data

### Network Tab
Check Network tab in browser dev tools for:
- WebSocket connections
- Failed requests
- Response status codes

## Test Scenarios

### Scenario 1: Basic Session
1. Host creates session
2. Host shares session ID with others
3. Others join using the session ID
4. All participants can see each other

### Scenario 2: URL Sharing
1. Host creates session
2. Host shares the generated URL
3. Others click the URL and join directly
4. Session ID is auto-filled

### Scenario 3: Multiple Participants
1. Host creates session
2. 3-4 people join the session
3. All participants appear in the participants list
4. Video grid shows all participants

## Expected Behavior

### Session Creation
- ✅ Session ID is generated and displayed
- ✅ Copy buttons work for Session ID and URL
- ✅ Host can enter the session
- ✅ Session persists until all users leave

### Session Joining
- ✅ Users can join with correct session ID
- ✅ Participants list updates in real-time
- ✅ All users can see each other
- ✅ Chat, video, audio, and file sharing work

### Error Handling
- ✅ Clear error messages for invalid session IDs
- ✅ Graceful handling of connection failures
- ✅ Automatic reconnection attempts
- ✅ Proper cleanup on disconnection

## Performance Notes

- **Video Quality**: Adjustable in settings (affects bandwidth)
- **Audio Quality**: Real-time mixing (may have slight delay)
- **File Sharing**: Limited by LAN bandwidth
- **Screen Sharing**: High quality but bandwidth intensive

## Security Notes

- All communication stays on local network
- No data is stored permanently
- Sessions are isolated from each other
- No external internet access required
