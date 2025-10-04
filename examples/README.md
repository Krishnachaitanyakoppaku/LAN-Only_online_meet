# Examples

This directory contains example configurations and usage examples for the LAN Video Calling Application.

## Contents

- **Configuration Examples**: Sample configuration files
- **Usage Examples**: Code examples for common use cases
- **Integration Examples**: Examples of integrating with other applications
- **Customization Examples**: Examples of customizing the application

## Quick Start Examples

### Basic Server Configuration
```python
# examples/basic_server.py
from server.main_server import LANVideoServer

# Create and start server
server = LANVideoServer(host="0.0.0.0", port=8888)
server.start()
```

### Basic Client Configuration
```python
# examples/basic_client.py
from client.main_client import LANVideoClient

# Create and connect client
client = LANVideoClient()
client.connect("127.0.0.1", 8888, "MyUsername")
```

### Custom Video Settings
```python
# examples/custom_video.py
from client.video_client import VideoClient

# Set custom video settings
video_client = VideoClient(main_client)
video_client.set_video_settings(
    width=1280,
    height=720,
    fps=30,
    quality=90
)
```

## Configuration Examples

### Server Configuration
- `server_config.json` - Basic server configuration
- `advanced_server_config.json` - Advanced server settings
- `production_config.json` - Production deployment settings

### Client Configuration
- `client_config.json` - Basic client configuration
- `custom_client_config.json` - Customized client settings

## Integration Examples

### Web Integration
- `web_integration.py` - Example of integrating with web applications
- `api_integration.py` - Example of using the application via API

### Custom Protocols
- `custom_protocol.py` - Example of extending the communication protocol
- `plugin_example.py` - Example of creating plugins

## Usage Examples

### File Transfer
```python
# examples/file_transfer.py
from client.file_client import FileClient

# Upload a file
file_client = FileClient(main_client)
file_client.upload_file("/path/to/file.pdf")

# Download a file
file_client.download_file("file_id", "/path/to/save.pdf")
```

### Chat Integration
```python
# examples/chat_integration.py
from client.chat_client import ChatClient

# Send a message
chat_client = ChatClient(main_client)
chat_client.send_message("Hello, everyone!")

# Handle incoming messages
def on_message_received(message):
    print(f"Received: {message.message}")

chat_client.set_message_callback('on_message_received', on_message_received)
```

## Customization Examples

### Custom GUI Themes
- `custom_theme.py` - Example of creating custom GUI themes
- `dark_theme.py` - Dark theme example

### Custom Audio Processing
- `custom_audio.py` - Example of custom audio processing
- `noise_reduction.py` - Advanced noise reduction example

## Running Examples

To run the examples:

```bash
# Navigate to examples directory
cd examples

# Run a specific example
python3 basic_server.py
python3 basic_client.py

# Run with custom configuration
python3 custom_video.py --config custom_config.json
```

## Contributing Examples

When adding new examples:

1. Follow the existing naming convention
2. Include clear comments and documentation
3. Test all examples before submitting
4. Add to the appropriate category
5. Update this README with new examples

## Example Requirements

Some examples may require additional dependencies:

```bash
# Install example dependencies
pip install -r examples/requirements.txt
```

## Support

For questions about examples:
- Check the main documentation first
- Review the example code and comments
- Open an issue on GitHub
- Check existing discussions
