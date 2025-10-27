# Client Connection Guide

## ✅ Server Status: WORKING
Your server is running correctly and accessible from the network!

## 🌐 Server Information
- **Server IP**: `172.17.222.34`
- **Port**: `5000`
- **Status**: Active with 1 session available

## 📱 For Clients to Join:

### Step 1: Use the Correct URL
Clients should access: **`http://172.17.222.34:5000/simple-join`**

❌ **Don't use**: `http://localhost:5000` (only works on host machine)
✅ **Use**: `http://172.17.222.34:5000/simple-join`

### Step 2: Simple Join Process
1. Open the URL: `http://172.17.222.34:5000/simple-join`
2. Enter your name
3. Click "Join Meeting"
4. You'll automatically join the active session!

## 🔧 Troubleshooting

### If clients can't access the page:

1. **Check Network Connection**
   - Ensure client is on the same network
   - Try pinging: `ping 172.17.222.34`

2. **Check Windows Firewall**
   - Windows might be blocking port 5000
   - Add exception for port 5000 or temporarily disable firewall

3. **Clear Browser Cache**
   - Press Ctrl+F5 to hard refresh
   - Or use incognito/private browsing mode

4. **Test Connection**
   - Try accessing: `http://172.17.222.34:5000/api/server-info`
   - Should show server information

## 🚀 Quick Test Commands

### On Host Machine:
```bash
# Test local access
curl http://localhost:5000/api/sessions

# Test network access  
curl http://172.17.222.34:5000/api/sessions
```

### On Client Machine:
```bash
# Test if server is reachable
ping 172.17.222.34

# Test if port is open
telnet 172.17.222.34 5000

# Test API access
curl http://172.17.222.34:5000/api/server-info
```

## 📋 Current Session Status
- **Active Sessions**: 1
- **Session Name**: main_session  
- **Host**: kkc
- **Users**: 3 (kkc, test_client, network_test_client)

## 🎯 Share This Link
Give this exact link to your clients:
**`http://172.17.222.34:5000/simple-join`**

They just need to:
1. Click the link
2. Enter their name  
3. Click "Join Meeting"
4. Done! ✅