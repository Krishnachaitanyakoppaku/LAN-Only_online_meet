"""
Communication protocol for LAN Video Calling Application
Handles message serialization, deserialization, and network communication
"""

import json
import struct
import base64
import hashlib
from typing import Dict, Any, Optional, Tuple
from .constants import MessageType, VIDEO_BUFFER_SIZE, AUDIO_BUFFER_SIZE, FILE_BUFFER_SIZE, CHAT_BUFFER_SIZE


class Message:
    """Base message class for all communication"""
    
    def __init__(self, msg_type: str, data: Dict[str, Any] = None, sender: str = None, 
                 recipient: str = None, room_id: str = None):
        self.type = msg_type
        self.data = data or {}
        self.sender = sender
        self.recipient = recipient
        self.room_id = room_id
        self.timestamp = self._get_timestamp()
        self.message_id = self._generate_id()
    
    def _get_timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()
    
    def _generate_id(self) -> str:
        """Generate unique message ID"""
        import uuid
        return str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'type': self.type,
            'data': self.data,
            'sender': self.sender,
            'recipient': self.recipient,
            'room_id': self.room_id,
            'timestamp': self.timestamp,
            'message_id': self.message_id
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            msg_type=data.get('type', ''),
            data=data.get('data', {}),
            sender=data.get('sender'),
            recipient=data.get('recipient'),
            room_id=data.get('room_id'),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class Protocol:
    """Network protocol handler for message transmission"""
    
    @staticmethod
    def pack_message(message: Message) -> bytes:
        """Pack message for network transmission"""
        json_data = message.to_json().encode('utf-8')
        length = len(json_data)
        
        # Pack: length (4 bytes) + data
        return struct.pack('!I', length) + json_data
    
    @staticmethod
    def unpack_message(data: bytes) -> Optional[Message]:
        """Unpack message from network data"""
        try:
            if len(data) < 4:
                return None
            
            # Unpack length
            length = struct.unpack('!I', data[:4])[0]
            
            if len(data) < 4 + length:
                return None
            
            # Extract JSON data
            json_data = data[4:4+length].decode('utf-8')
            return Message.from_json(json_data)
        except Exception as e:
            print(f"Error unpacking message: {e}")
            return None
    
    @staticmethod
    def pack_binary_data(data: bytes, data_type: str = "BINARY") -> bytes:
        """Pack binary data (video, audio, files) for transmission"""
        length = len(data)
        header = struct.pack('!I', length) + data_type.encode('utf-8')[:16].ljust(16, b'\x00')
        return header + data
    
    @staticmethod
    def unpack_binary_data(data: bytes) -> Tuple[Optional[bytes], str]:
        """Unpack binary data from network transmission"""
        try:
            if len(data) < 20:  # 4 bytes length + 16 bytes type
                return None, ""
            
            length = struct.unpack('!I', data[:4])[0]
            data_type = data[4:20].rstrip(b'\x00').decode('utf-8')
            
            if len(data) < 20 + length:
                return None, ""
            
            binary_data = data[20:20+length]
            return binary_data, data_type
        except Exception as e:
            print(f"Error unpacking binary data: {e}")
            return None, ""
    
    @staticmethod
    def _get_timestamp() -> float:
        """Get current timestamp"""
        import time
        return time.time()
    
    @staticmethod
    def _generate_id() -> str:
        """Generate unique message ID"""
        import uuid
        return str(uuid.uuid4())


class VideoFrame:
    """Video frame data structure"""
    
    def __init__(self, frame_data: bytes, width: int, height: int, 
                 timestamp: float = None, user_id: str = None):
        self.frame_data = frame_data
        self.width = width
        self.height = height
        self.timestamp = timestamp or Protocol._get_timestamp()
        self.user_id = user_id
        self.frame_id = Protocol._generate_id()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert frame to dictionary"""
        return {
            'frame_data': base64.b64encode(self.frame_data).decode('utf-8'),
            'width': self.width,
            'height': self.height,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'frame_id': self.frame_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoFrame':
        """Create frame from dictionary"""
        frame_data = base64.b64decode(data['frame_data'])
        return cls(
            frame_data=frame_data,
            width=data['width'],
            height=data['height'],
            timestamp=data.get('timestamp'),
            user_id=data.get('user_id')
        )


class AudioFrame:
    """Audio frame data structure"""
    
    def __init__(self, audio_data: bytes, sample_rate: int, channels: int,
                 timestamp: float = None, user_id: str = None):
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.channels = channels
        self.timestamp = timestamp or Protocol._get_timestamp()
        self.user_id = user_id
        self.frame_id = Protocol._generate_id()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audio frame to dictionary"""
        return {
            'audio_data': base64.b64encode(self.audio_data).decode('utf-8'),
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'frame_id': self.frame_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioFrame':
        """Create audio frame from dictionary"""
        audio_data = base64.b64decode(data['audio_data'])
        return cls(
            audio_data=audio_data,
            sample_rate=data['sample_rate'],
            channels=data['channels'],
            timestamp=data.get('timestamp'),
            user_id=data.get('user_id')
        )


class FileChunk:
    """File chunk data structure for file transfers"""
    
    def __init__(self, file_id: str, chunk_index: int, chunk_data: bytes,
                 total_chunks: int, file_name: str, file_size: int):
        self.file_id = file_id
        self.chunk_index = chunk_index
        self.chunk_data = chunk_data
        self.total_chunks = total_chunks
        self.file_name = file_name
        self.file_size = file_size
        self.chunk_size = len(chunk_data)
        self.checksum = hashlib.md5(chunk_data).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary"""
        return {
            'file_id': self.file_id,
            'chunk_index': self.chunk_index,
            'chunk_data': base64.b64encode(self.chunk_data).decode('utf-8'),
            'total_chunks': self.total_chunks,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'chunk_size': self.chunk_size,
            'checksum': self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileChunk':
        """Create chunk from dictionary"""
        chunk_data = base64.b64decode(data['chunk_data'])
        return cls(
            file_id=data['file_id'],
            chunk_index=data['chunk_index'],
            chunk_data=chunk_data,
            total_chunks=data['total_chunks'],
            file_name=data['file_name'],
            file_size=data['file_size']
        )


# Message factory functions
def create_connect_message(user_id: str, username: str) -> Message:
    """Create connection message"""
    return Message(
        msg_type=MessageType.CONNECT,
        data={'user_id': user_id, 'username': username}
    )


def create_disconnect_message(user_id: str) -> Message:
    """Create disconnection message"""
    return Message(
        msg_type=MessageType.DISCONNECT,
        data={'user_id': user_id}
    )


def create_room_join_message(user_id: str, room_id: str) -> Message:
    """Create room join message"""
    return Message(
        msg_type=MessageType.ROOM_JOIN,
        data={'user_id': user_id, 'room_id': room_id},
        room_id=room_id
    )


def create_chat_message(user_id: str, message: str, room_id: str) -> Message:
    """Create chat message"""
    return Message(
        msg_type=MessageType.CHAT_MESSAGE,
        data={'user_id': user_id, 'message': message},
        sender=user_id,
        room_id=room_id
    )


def create_video_frame_message(user_id: str, frame: VideoFrame, room_id: str) -> Message:
    """Create video frame message"""
    return Message(
        msg_type=MessageType.VIDEO_FRAME,
        data=frame.to_dict(),
        sender=user_id,
        room_id=room_id
    )


def create_audio_frame_message(user_id: str, frame: AudioFrame, room_id: str) -> Message:
    """Create audio frame message"""
    return Message(
        msg_type=MessageType.AUDIO_FRAME,
        data=frame.to_dict(),
        sender=user_id,
        room_id=room_id
    )


def create_file_upload_message(user_id: str, file_info: Dict[str, Any]) -> Message:
    """Create file upload message"""
    return Message(
        msg_type=MessageType.FILE_UPLOAD_START,
        data={'user_id': user_id, 'file_info': file_info}
    )
