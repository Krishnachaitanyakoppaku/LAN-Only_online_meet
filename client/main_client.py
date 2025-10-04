"""
Main client for the LAN Video Calling Application
Handles connection to server, user interface, and coordinates all client components
"""

import socket
import threading
import time
import json
import sys
import os
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available. Video functionality will be limited.")
from typing import Dict, Any, Optional, Callable, List
from shared.constants import *
from shared.protocol import *
from shared.utils import logger, get_local_ip
from .video_client import VideoClient
from .audio_client import AudioClient
from .chat_client import ChatClient
from .file_client import FileClient


class LANVideoClient:
    """Main client class for LAN Video Calling Application"""
    
    def __init__(self):
        self.server_host = "127.0.0.1"
        self.server_port = DEFAULT_SERVER_PORT
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        self.is_authenticated = False
        
        # User info
        self.user_id: Optional[str] = None
        self.username: Optional[str] = None
        self.current_room_id: Optional[str] = None
        
        # Client components
        self.video_client = VideoClient(self)
        self.audio_client = AudioClient(self)
        self.chat_client = ChatClient(self)
        self.file_client = FileClient(self)
        
        # Network
        self.receive_thread: Optional[threading.Thread] = None
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.last_heartbeat = time.time()
        
        # Callbacks
        self.message_callbacks: Dict[str, Callable] = {}
        self.connection_callbacks: Dict[str, Callable] = {}
        
        # State
        self.room_participants: Dict[str, Dict[str, Any]] = {}
        self.available_rooms: List[Dict[str, Any]] = []
        
        # Setup message handlers
        self._setup_message_handlers()
    
    def _setup_message_handlers(self):
        """Setup message handlers"""
        self.message_callbacks = {
            MessageType.SUCCESS: self._handle_success,
            MessageType.ERROR: self._handle_error,
            MessageType.ACK: self._handle_ack,
            MessageType.USER_JOIN: self._handle_user_join,
            MessageType.USER_LEAVE: self._handle_user_leave,
            MessageType.ROOM_LIST: self._handle_room_list,
            MessageType.VIDEO_FRAME: self._handle_video_frame,
            MessageType.AUDIO_FRAME: self._handle_audio_frame,
            MessageType.SCREEN_SHARE: self._handle_screen_share,
            MessageType.CHAT_MESSAGE: self._handle_chat_message,
            MessageType.FILE_LIST: self._handle_file_list,
        }
    
    def connect(self, host: str, port: int, username: str) -> bool:
        """Connect to server"""
        try:
            self.server_host = host
            self.server_port = port
            self.username = username
            
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(CONNECTION_TIMEOUT)
            self.socket.connect((host, port))
            
            self.is_connected = True
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            # Start heartbeat thread
            self.heartbeat_thread = threading.Thread(target=self._send_heartbeat, daemon=True)
            self.heartbeat_thread.start()
            
            # Send connect message
            connect_msg = create_connect_message("", username)
            self.send_message(connect_msg)
            
            logger.info(f"Connected to server {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        if self.is_connected:
            # Send disconnect message
            if self.user_id:
                disconnect_msg = create_disconnect_message(self.user_id)
                self.send_message(disconnect_msg)
            
            # Stop threads
            self.is_connected = False
            
            # Close socket
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            
            # Stop client components
            self.video_client.stop()
            self.audio_client.stop()
            
            logger.info("Disconnected from server")
    
    def send_message(self, message: Message) -> bool:
        """Send message to server"""
        if not self.is_connected or not self.socket:
            return False
        
        try:
            data = Protocol.pack_message(message)
            self.socket.send(data)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def _receive_messages(self):
        """Receive messages from server"""
        buffer = b""
        
        while self.is_connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                
                buffer += data
                
                # Process complete messages
                while len(buffer) >= 4:
                    # Get message length
                    length = int.from_bytes(buffer[:4], byteorder='big')
                    
                    if len(buffer) < 4 + length:
                        break  # Incomplete message
                    
                    # Extract message
                    message_data = buffer[4:4+length]
                    buffer = buffer[4+length:]
                    
                    # Process message
                    self._process_message(message_data)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_connected:
                    logger.error(f"Error receiving message: {e}")
                break
        
        # Connection lost
        self.is_connected = False
        if self.connection_callbacks.get('on_disconnect'):
            self.connection_callbacks['on_disconnect']()
    
    def _process_message(self, message_data: bytes):
        """Process incoming message"""
        try:
            message = Message.from_json(message_data.decode('utf-8'))
            
            # Update heartbeat
            self.last_heartbeat = time.time()
            
            # Route to handler
            handler = self.message_callbacks.get(message.type)
            if handler:
                handler(message)
            else:
                logger.warning(f"No handler for message type: {message.type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _send_heartbeat(self):
        """Send heartbeat to server"""
        while self.is_connected:
            try:
                time.sleep(HEARTBEAT_INTERVAL)
                
                if time.time() - self.last_heartbeat > CONNECTION_TIMEOUT:
                    logger.warning("Connection timeout, attempting to reconnect...")
                    self.disconnect()
                    break
                
                heartbeat_msg = Message(msg_type=MessageType.HEARTBEAT)
                self.send_message(heartbeat_msg)
                
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
                break
    
    # Message handlers
    def _handle_success(self, message: Message):
        """Handle success message"""
        if message.data.get('user_id'):
            self.user_id = message.data['user_id']
            self.is_authenticated = True
            
            if self.connection_callbacks.get('on_connect'):
                self.connection_callbacks['on_connect'](message.data)
        
        logger.info(f"Success: {message.data.get('message', '')}")
    
    def _handle_error(self, message: Message):
        """Handle error message"""
        error_msg = message.data.get('message', 'Unknown error')
        logger.error(f"Server error: {error_msg}")
        
        if self.connection_callbacks.get('on_error'):
            self.connection_callbacks['on_error'](error_msg)
    
    def _handle_ack(self, message: Message):
        """Handle acknowledgment message"""
        pass  # Heartbeat response
    
    def _handle_user_join(self, message: Message):
        """Handle user join message"""
        user_data = message.data
        self.room_participants[user_data['user_id']] = user_data
        
        if self.connection_callbacks.get('on_user_join'):
            self.connection_callbacks['on_user_join'](user_data)
    
    def _handle_user_leave(self, message: Message):
        """Handle user leave message"""
        user_id = message.data.get('user_id')
        if user_id in self.room_participants:
            user_data = self.room_participants[user_id]
            del self.room_participants[user_id]
            
            if self.connection_callbacks.get('on_user_leave'):
                self.connection_callbacks['on_user_leave'](user_data)
    
    def _handle_room_list(self, message: Message):
        """Handle room list message"""
        self.available_rooms = message.data.get('rooms', [])
        
        if self.connection_callbacks.get('on_room_list'):
            self.connection_callbacks['on_room_list'](self.available_rooms)
    
    def _handle_video_frame(self, message: Message):
        """Handle video frame message"""
        frame_data = message.data
        user_id = frame_data.get('user_id')
        
        if user_id and user_id != self.user_id:
            if CV2_AVAILABLE:
                # Decode frame
                import base64
                frame_bytes = base64.b64decode(frame_data['frame_data'])
                
                # Convert to OpenCV format
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    self.video_client.display_remote_frame(user_id, frame)
    
    def _handle_audio_frame(self, message: Message):
        """Handle audio frame message"""
        audio_data = message.data
        user_id = audio_data.get('user_id')
        
        if user_id and user_id != self.user_id:
            # Decode audio
            import base64
            audio_bytes = base64.b64decode(audio_data['audio_data'])
            
            # Play audio
            self.audio_client.play_remote_audio(user_id, audio_bytes)
    
    def _handle_screen_share(self, message: Message):
        """Handle screen share message"""
        frame_data = message.data
        user_id = frame_data.get('user_id')
        
        if user_id and user_id != self.user_id:
            if CV2_AVAILABLE:
                # Decode frame
                import base64
                frame_bytes = base64.b64decode(frame_data['frame_data'])
                
                # Convert to OpenCV format
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    self.video_client.display_screen_share(user_id, frame)
    
    def _handle_chat_message(self, message: Message):
        """Handle chat message"""
        chat_data = message.data
        
        if self.connection_callbacks.get('on_chat_message'):
            self.connection_callbacks['on_chat_message'](chat_data)
    
    def _handle_file_list(self, message: Message):
        """Handle file list message"""
        files = message.data.get('files', [])
        
        if self.connection_callbacks.get('on_file_list'):
            self.connection_callbacks['on_file_list'](files)
    
    # Client operations
    def create_room(self, room_name: str, is_private: bool = False, 
                   password: str = None, max_participants: int = 50) -> bool:
        """Create a new room"""
        if not self.is_authenticated:
            return False
        
        message = Message(
            msg_type=MessageType.ROOM_CREATE,
            data={
                'room_name': room_name,
                'is_private': is_private,
                'password': password,
                'max_participants': max_participants
            }
        )
        
        return self.send_message(message)
    
    def join_room(self, room_id: str, password: str = None) -> bool:
        """Join a room"""
        if not self.is_authenticated:
            return False
        
        message = Message(
            msg_type=MessageType.ROOM_JOIN,
            data={
                'room_id': room_id,
                'password': password
            }
        )
        
        return self.send_message(message)
    
    def leave_room(self) -> bool:
        """Leave current room"""
        if not self.is_authenticated or not self.current_room_id:
            return False
        
        message = Message(
            msg_type=MessageType.ROOM_LEAVE,
            data={'room_id': self.current_room_id}
        )
        
        # Stop media streams
        self.video_client.stop_streaming()
        self.audio_client.stop_streaming()
        
        self.current_room_id = None
        self.room_participants.clear()
        
        return self.send_message(message)
    
    def send_chat_message(self, message_text: str) -> bool:
        """Send chat message"""
        if not self.is_authenticated or not self.current_room_id:
            return False
        
        message = Message(
            msg_type=MessageType.CHAT_MESSAGE,
            data={
                'room_id': self.current_room_id,
                'message': message_text
            }
        )
        
        return self.send_message(message)
    
    def start_video(self) -> bool:
        """Start video streaming"""
        if not self.is_authenticated or not self.current_room_id:
            return False
        
        success = self.video_client.start_camera()
        if success:
            # Notify server
            message = Message(
                msg_type=MessageType.VIDEO_START,
                data={'user_id': self.user_id}
            )
            self.send_message(message)
        
        return success
    
    def stop_video(self) -> bool:
        """Stop video streaming"""
        success = self.video_client.stop_camera()
        if success:
            # Notify server
            message = Message(
                msg_type=MessageType.VIDEO_STOP,
                data={'user_id': self.user_id}
            )
            self.send_message(message)
        
        return success
    
    def start_audio(self) -> bool:
        """Start audio streaming"""
        if not self.is_authenticated or not self.current_room_id:
            return False
        
        success = self.audio_client.start_microphone()
        if success:
            # Notify server
            message = Message(
                msg_type=MessageType.AUDIO_START,
                data={'user_id': self.user_id}
            )
            self.send_message(message)
        
        return success
    
    def stop_audio(self) -> bool:
        """Stop audio streaming"""
        success = self.audio_client.stop_microphone()
        if success:
            # Notify server
            message = Message(
                msg_type=MessageType.AUDIO_STOP,
                data={'user_id': self.user_id}
            )
            self.send_message(message)
        
        return success
    
    def start_screen_share(self) -> bool:
        """Start screen sharing"""
        if not self.is_authenticated or not self.current_room_id:
            return False
        
        success = self.video_client.start_screen_capture()
        if success:
            # Notify server
            message = Message(
                msg_type=MessageType.SCREEN_SHARE,
                data={'user_id': self.user_id, 'action': 'start'}
            )
            self.send_message(message)
        
        return success
    
    def stop_screen_share(self) -> bool:
        """Stop screen sharing"""
        success = self.video_client.stop_screen_capture()
        if success:
            # Notify server
            message = Message(
                msg_type=MessageType.SCREEN_SHARE,
                data={'user_id': self.user_id, 'action': 'stop'}
            )
            self.send_message(message)
        
        return success
    
    def upload_file(self, file_path: str) -> bool:
        """Upload a file"""
        if not self.is_authenticated:
            return False
        
        return self.file_client.upload_file(file_path)
    
    def download_file(self, file_id: str, save_path: str) -> bool:
        """Download a file"""
        if not self.is_authenticated:
            return False
        
        return self.file_client.download_file(file_id, save_path)
    
    def get_room_participants(self) -> Dict[str, Dict[str, Any]]:
        """Get current room participants"""
        return self.room_participants.copy()
    
    def get_available_rooms(self) -> List[Dict[str, Any]]:
        """Get available rooms"""
        return self.available_rooms.copy()
    
    def set_callback(self, event: str, callback: Callable):
        """Set event callback"""
        if event.startswith('on_'):
            self.connection_callbacks[event] = callback
        else:
            self.message_callbacks[event] = callback


def main():
    """Main function for testing the client"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LAN Video Calling Client')
    parser.add_argument('--host', default='127.0.0.1', help='Server host')
    parser.add_argument('--port', type=int, default=DEFAULT_SERVER_PORT, help='Server port')
    parser.add_argument('--username', required=True, help='Username')
    
    args = parser.parse_args()
    
    # Create client
    client = LANVideoClient()
    
    # Set up callbacks
    def on_connect(data):
        print(f"Connected as {data.get('user_id')}")
    
    def on_error(error):
        print(f"Error: {error}")
    
    def on_user_join(user):
        print(f"User joined: {user['username']}")
    
    def on_user_leave(user):
        print(f"User left: {user['username']}")
    
    def on_chat_message(data):
        print(f"Chat: {data['username']}: {data['message']}")
    
    client.set_callback('on_connect', on_connect)
    client.set_callback('on_error', on_error)
    client.set_callback('on_user_join', on_user_join)
    client.set_callback('on_user_leave', on_user_leave)
    client.set_callback('on_chat_message', on_chat_message)
    
    try:
        # Connect to server
        if client.connect(args.host, args.port, args.username):
            print("Connected to server. Type 'help' for commands.")
            
            # Simple command loop
            while client.is_connected:
                try:
                    command = input("> ").strip().split()
                    if not command:
                        continue
                    
                    if command[0] == 'help':
                        print("Commands: create <name>, join <id>, leave, chat <message>, start_video, stop_video, quit")
                    elif command[0] == 'create' and len(command) > 1:
                        client.create_room(' '.join(command[1:]))
                    elif command[0] == 'join' and len(command) > 1:
                        client.join_room(command[1])
                    elif command[0] == 'leave':
                        client.leave_room()
                    elif command[0] == 'chat' and len(command) > 1:
                        client.send_chat_message(' '.join(command[1:]))
                    elif command[0] == 'start_video':
                        client.start_video()
                    elif command[0] == 'stop_video':
                        client.stop_video()
                    elif command[0] == 'quit':
                        break
                    else:
                        print("Unknown command. Type 'help' for commands.")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
        else:
            print("Failed to connect to server")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nShutting down client...")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
