# 🔒 HTTPS SSL Certificate Setup

This server automatically generates SSL certificates to enable camera and microphone access in web browsers.

## Why HTTPS is Required

Modern web browsers require HTTPS for accessing:
- 📹 Camera (getUserMedia)
- 🎤 Microphone (getUserMedia)
- 📍 Geolocation
- 🔔 Notifications
- 📱 Device sensors

## How It Works

1. **Automatic Certificate Generation**: The server uses Python's `cryptography` library to create self-signed SSL certificates
2. **IP-Based Certificates**: Certificates are generated for your actual network IP address
3. **Browser Compatibility**: Works with all modern browsers (Chrome, Firefox, Safari, Edge)

## Starting the Server

### Option 1: Quick Start
```bash
python start_https_server.py
```

### Option 2: Direct Start
```bash
python server.py
```

## Accessing the Server

1. **Main Server**: `https://[YOUR_IP]:5000/`
2. **Camera Test**: `https://[YOUR_IP]:5000/camera-test`
3. **Media Test**: `https://[YOUR_IP]:5000/media-test`

## Browser Security Warning

You will see a security warning because the certificate is self-signed:

### Chrome/Edge:
1. Click "Advanced"
2. Click "Proceed to [IP] (unsafe)"

### Firefox:
1. Click "Advanced"
2. Click "Accept the Risk and Continue"

### Safari:
1. Click "Show Details"
2. Click "visit this website"
3. Click "Visit Website"

## Mobile Devices

1. Connect to the same WiFi network
2. Open `https://[SERVER_IP]:5000/camera-test`
3. Accept the security warning
4. Allow camera/microphone permissions

## Technical Details

### Certificate Information:
- **Type**: Self-signed X.509 certificate
- **Key Size**: 2048-bit RSA
- **Validity**: 365 days
- **Subject Alternative Names**: localhost, server IP, 127.0.0.1

### Files Created:
- `ssl_certs/server.crt` - SSL certificate
- `ssl_certs/server.key` - Private key

### Fallback Methods:
1. **Primary**: Python cryptography library
2. **Secondary**: OpenSSL (if available)
3. **Tertiary**: Flask's adhoc SSL
4. **Final**: HTTP (with warning)

## Troubleshooting

### Certificate Generation Failed
- Install required dependencies: `pip install cryptography`
- Check file permissions in `ssl_certs/` directory

### Browser Still Shows HTTP
- Clear browser cache
- Check that server started with HTTPS
- Verify no proxy/firewall blocking HTTPS

### Camera/Microphone Not Working
- Ensure you're using HTTPS (not HTTP)
- Check browser permissions
- Try the camera test page: `/camera-test`

### Network Access Issues
- Check firewall settings
- Ensure port 5000 is open
- Verify all devices on same network

## Security Notes

⚠️ **Self-signed certificates are safe for local network use but should not be used in production**

✅ **For local development and LAN communication, self-signed certificates provide the necessary security for browser APIs**

🔒 **The certificate is automatically regenerated if expired or missing**