
import json

# Constants
TCP_CONTROL_PORT = 5000
UDP_VIDEO_PORT = 5001
UDP_AUDIO_PORT = 5002
TCP_FILE_PORT = 5003
TCP_SCREEN_SHARING_PORT = 5004

# Message Types
REGISTER = 'REGISTER'
CHAT = 'CHAT'
FILE_META = 'FILE_META'
FILE_GET = 'FILE_GET'
FILE_CHUNK = 'FILE_CHUNK'
FILE_EOF = 'FILE_EOF'

def create_message(msg_type, payload):
    """Creates a JSON message."""
    return json.dumps({'type': msg_type, 'payload': payload}).encode('utf-8')

def parse_message(data):
    """Parses a JSON message."""
    return json.loads(data.decode('utf-8'))
