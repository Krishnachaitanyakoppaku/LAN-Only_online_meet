# Screen Sharing Setup Guide

## Dependencies Required

For screen sharing to work, you need the following Python packages:

### Required for All Platforms:
```bash
pip install opencv-python
```

### Required for Windows/Linux:
```bash
pip install Pillow
```

### macOS:
Screen capture uses the built-in `screencapture` command, so no additional dependencies are needed beyond OpenCV.

## How to Use Screen Sharing

### As a Presenter:
1. Connect to the server
2. Click the "🖥️ Share" button in the media controls
3. Your screen will be captured and shared with all participants
4. Click "🖥️ Sharing" again to stop sharing

### As a Viewer:
1. When someone starts sharing, you'll see a message: "🖥️ [Username] started screen sharing"
2. A new window will automatically open showing the shared screen
3. Use the "🔍 Fullscreen" button to view in fullscreen mode
4. Close the window or wait for the presenter to stop sharing

## Features:
- ✅ Real-time screen sharing at 10 FPS
- ✅ Automatic window opening for viewers
- ✅ Fullscreen support
- ✅ Cross-platform compatibility
- ✅ Automatic cleanup when sharing stops
- ✅ Only one presenter at a time (server enforced)

## Troubleshooting:

### "Screen capture not supported" error:
- **Windows/Linux**: Install Pillow with `pip install Pillow`
- **macOS**: Make sure you have screen recording permissions enabled

### Permission Issues on macOS:
1. Go to System Preferences → Security & Privacy → Privacy
2. Select "Screen Recording" from the left sidebar
3. Add your terminal application or Python to the allowed apps

### Poor Performance:
- Screen sharing runs at 10 FPS to balance quality and performance
- Large screens are automatically resized to 1280px width maximum
- JPEG compression is used to reduce bandwidth

## Technical Details:
- Uses TCP connection to screen share server (port 12000 by default)
- Screen capture resolution is automatically optimized
- Supports multiple viewers for one presenter
- Graceful handling of connection errors and cleanup