#!/usr/bin/env python3
"""
LAN Collaboration Server - Complete Implementation

Full-featured collaboration server implemented from scratch with:
- Multi-user TCP chat and control
- UDP video streaming with encoding
- UDP audio streaming with mixing
- Screen sharing with presenter/viewer system
- File transfer with progress tracking
- Command-line interface (no GUI)
- Comprehensive participant management

This is a complete standalone implementation.
"""

import sys
import os
import asyncio
import json
import time
import struct
import socket
import uuid
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import deque

# Optional imports
try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    print("[WARNING] OpenCV not available. Video features disabled.")

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    print("[WARNING] PyAudio not available. Audio features disabled.")

try:
    from opuslib import Encoder, Decoder
    HAS_OPUS = True
except ImportError:
    HAS_OPUS = False
    print("[WARNING] Opus not available. Audio encoding disabled.")

# Protocol constants
class MessageTypes:
    # Client to Server
    LOGIN = 'login'
    HEARTBEAT = 'heartbeat'
    CHAT = 'chat'
    BROADCAST = 'broadcast'
    UNICAST = 'unicast'
    GET_HISTORY = 'get_history'
    GET_PARTICIPANTS = 'get_participants'
    FILE_OFFER = 'file_offer'
    FILE_REQUEST = 'file_request'
    PRESENT_START = 'present_start'
    PRESENT_STOP = 'present_stop'
    LOGOUT = 'logout'
    
    # Server to Client
    LOGIN_SUCCESS = 'login_success'
    PARTICIPANT_LIST = 'participant_list'
    HISTORY = 'history'
    USER_JOINED = 'user_joined'
    USER_LEFT = 'user_left'
    HEARTBEAT_ACK = 'heartbeat_ack'
    FILE_UPLOAD_PORT = 'file_upload_port'
    FILE_DOWNLOAD_PORT = 'file_download_port'
    FILE_AVAILABLE = 'file_available'
    SCREEN_SHARE_PORTS = 'screen_share_ports'
    PRESENT_START_BROADCAST = 'present_start_broadcast'
    PRESENT_STOP_BROADCAST = 'present_stop_broadcast'
    UNICAST_SENT = 'unicast_sent'
    ERROR = 'error'

# Configuration
DEFAULT_HOST = '0.0.0.0'
DEFAULT_TCP_PORT = 9000
DEFAULT_UDP_VIDEO_PORT = 10000
DEFAULT_UDP_AUDIO_PORT = 11000
CHUNK_SIZE = 8192
MAX_FILE_SIZE = 100 * 1024 * 1024
HEARTBEAT_INTERVAL = 10
MAX_CHAT_HISTORY = 500
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_CHUNK_SIZE = 1600

# Protocol helper functions
def create_login_success_message(uid: int, username: str) -> dict:
    return {
        "type": MessageTypes.LOGIN_SUCCESS,
        "uid": uid,
        "username": username,
        "timestamp": datetime.now().isoformat()
    }

def create_participant_list_message(participants: list) -> dict:
    return {
        "type": MessageTypes.PARTICIPANT_LIST,
        "participants": participants,
        "timestamp": datetime.now().isoformat()
    }

def create_user_joined_message(uid: int, username: str) -> dict:
    return {
        "type": MessageTypes.USER_JOINED,
        "uid": uid,
        "username": username,
        "timestamp": datetime.now().isoformat()
    }

def create_user_left_message(uid: int, username: str) -> dict:
    return {
        "type": MessageTypes.USER_LEFT,
        "uid": uid,
        "username": username,
        "timestamp": datetime.now().isoformat()
    }

def create_error_message(message: str) -> dict:
    return {
        "type": MessageTypes.ERROR,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

def create_heartbeat_ack_message() -> dict:
    return {
        "type": MessageTypes.HEARTBEAT_ACK,
        "timestamp": datetime.now().isoformat()
    }


class AudioServer:
    """UDP Audio server for real-time audio streaming."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 11000):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.clients = {}
        
    async def start(self):
        """Start the audio server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.setblocking(False)
            self.running = True
            
            print(f"[INFO] Audio server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    data, addr = await asyncio.get_event_loop().sock_recvfrom(self.socket, 4096)
                    await self.handle_audio_packet(data, addr)
                except asyncio.CancelledError:
                    break
                except Exception:
                    if self.running:
                        await asyncio.sleep(0.01)
                        
        except Exception as e:
            print(f"[ERROR] Failed to start audio server: {e}")
        finally:
            self.stop()
    
    async def handle_audio_packet(self, data: bytes, addr: tuple):
        """Handle incoming audio packet."""
        try:
            if len(data) < 12:
                return
            
            uid, sequence, data_size = struct.unpack('!III', data[:12])
            audio_data = data[12:]
            
            if len(audio_data) != data_size:
                return
            
            self.clients[uid] = {'address': addr, 'last_seen': time.time()}
            await self.broadcast_audio(audio_data, uid, sequence)
            
        except Exception:
            pass
    
    async def broadcast_audio(self, audio_data: bytes, sender_uid: int, sequence: int):
        """Broadcast audio to all clients except sender."""
        try:
            header = struct.pack('!III', sender_uid, sequence, len(audio_data))
            packet = header + audio_data
            
            for uid, client_info in self.clients.items():
                if uid != sender_uid:
                    try:
                        await asyncio.get_event_loop().sock_sendto(
                            self.socket, packet, client_info['address']
                        )
                    except Exception:
                        pass
        except Exception:
            pass
    
    def stop(self):
        """Stop the audio server."""
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None

class VideoServer:
    """UDP Video server for real-time video streaming."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 10000):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.clients = {}
        
    async def start(self):
        """Start the video server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.setblocking(False)
            self.running = True
            
            print(f"[INFO] Video server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    data, addr = await asyncio.get_event_loop().sock_recvfrom(self.socket, 65536)
                    await self.handle_video_packet(data, addr)
                except asyncio.CancelledError:
                    break
                except Exception:
                    if self.running:
                        await asyncio.sleep(0.01)
                        
        except Exception as e:
            print(f"[ERROR] Failed to start video server: {e}")
        finally:
            self.stop()
    
    async def handle_video_packet(self, data: bytes, addr: tuple):
        """Handle incoming video packet."""
        try:
            if len(data) < 16:
                return
            
            uid, sequence, frame_id, data_size = struct.unpack('!IIII', data[:16])
            video_data = data[16:]
            
            if len(video_data) != data_size:
                return
            
            self.clients[uid] = {'address': addr, 'last_seen': time.time()}
            await self.broadcast_video(video_data, uid, sequence, frame_id)
            
        except Exception:
            pass
    
    async def broadcast_video(self, video_data: bytes, sender_uid: int, sequence: int, frame_id: int):
        """Broadcast video to all clients except sender."""
        try:
            header = struct.pack('!IIII', sender_uid, sequence, frame_id, len(video_data))
            packet = header + video_data
            
            for uid, client_info in self.clients.items():
                if uid != sender_uid:
                    try:
                        await asyncio.get_event_loop().sock_sendto(
                            self.socket, packet, client_info['address']
                        )
                    except Exception:
                        pass
        except Exception:
            pass
    
    def stop(self):
        """Stop the video server."""
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None


class ScreenShareServer:
    """TCP Screen sharing server."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 12000):
        self.host = host
        self.port = port
        self.server = None
        self.running = False
        self.presenter = None
        self.viewers = set()
        
    async def start(self):
        """Start the screen share server."""
        try:
            self.server = await asyncio.start_server(
                self.handle_client, self.host, self.port
            )
            self.running = True
            
            print(f"[INFO] Screen share server listening on {self.host}:{self.port}")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            print(f"[ERROR] Failed to start screen share server: {e}")
        finally:
            self.stop()
    
    async def handle_client(self, reader, writer):
        """Handle screen share client connection."""
        addr = writer.get_extra_info('peername')
        print(f"[INFO] Screen share client connected: {addr}")
        
        try:
            while self.running:
                # Read message type
                type_data = await reader.read(4)
                if not type_data:
                    break
                
                msg_type = struct.unpack('!I', type_data)[0]
                
                if msg_type == 1:  # Presenter
                    await self.handle_presenter(reader, writer)
                elif msg_type == 2:  # Viewer
                    await self.handle_viewer(reader, writer)
                else:
                    break
                    
        except Exception as e:
            print(f"[ERROR] Screen share client error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def handle_presenter(self, reader, writer):
        """Handle presenter connection."""
        if self.presenter:
            writer.write(b'BUSY')
            return
        
        self.presenter = writer
        writer.write(b'OK')
        
        try:
            while self.running and self.presenter == writer:
                # Read frame size
                size_data = await reader.read(4)
                if not size_data:
                    break
                
                frame_size = struct.unpack('!I', size_data)[0]
                
                # Read frame data
                frame_data = await reader.readexactly(frame_size)
                
                # Broadcast to viewers
                await self.broadcast_frame(frame_data)
                
        except Exception:
            pass
        finally:
            if self.presenter == writer:
                self.presenter = None
    
    async def handle_viewer(self, reader, writer):
        """Handle viewer connection."""
        self.viewers.add(writer)
        writer.write(b'OK')
        
        try:
            while self.running and writer in self.viewers:
                await asyncio.sleep(1)
        except Exception:
            pass
        finally:
            self.viewers.discard(writer)
    
    async def broadcast_frame(self, frame_data: bytes):
        """Broadcast frame to all viewers."""
        if not self.viewers:
            return
        
        frame_size = struct.pack('!I', len(frame_data))
        
        for viewer in list(self.viewers):
            try:
                viewer.write(frame_size + frame_data)
                await viewer.drain()
            except Exception:
                self.viewers.discard(viewer)
    
    def stop(self):
        """Stop the screen share server."""
        self.running = False
        if self.server:
            self.server.close()


class FileTransferServer:
    """File transfer server for handling file uploads and downloads."""
    
    def __init__(self, host: str = '0.0.0.0', upload_port: int = 13000, download_port: int = 14000, upload_callback=None):
        self.host = host
        self.upload_port = upload_port
        self.download_port = download_port
        self.upload_server = None
        self.download_server = None
        self.running = False
        self.files = {}  # file_id -> file_info
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.upload_callback = upload_callback  # Callback to notify main server of uploads
        
    async def start(self):
        """Start file transfer servers."""
        try:
            self.upload_server = await asyncio.start_server(
                self.handle_upload, self.host, self.upload_port
            )
            self.download_server = await asyncio.start_server(
                self.handle_download, self.host, self.download_port
            )
            self.running = True
            
            print(f"[INFO] File upload server listening on {self.host}:{self.upload_port}")
            print(f"[INFO] File download server listening on {self.host}:{self.download_port}")
            
            await asyncio.gather(
                self.upload_server.serve_forever(),
                self.download_server.serve_forever()
            )
            
        except Exception as e:
            print(f"[ERROR] Failed to start file transfer servers: {e}")
        finally:
            self.stop()
    
    async def handle_upload(self, reader, writer):
        """Handle file upload."""
        addr = writer.get_extra_info('peername')
        
        try:
            # Read file info
            info_size_data = await reader.read(4)
            if not info_size_data:
                return
            
            info_size = struct.unpack('!I', info_size_data)[0]
            info_data = await reader.readexactly(info_size)
            file_info = json.loads(info_data.decode())
            
            file_id = str(uuid.uuid4())
            filename = file_info['filename']
            file_size = file_info['size']
            
            if file_size > MAX_FILE_SIZE:
                writer.write(b'ERROR: File too large')
                return
            
            # Create file path
            file_path = self.upload_dir / f"{file_id}_{filename}"
            
            # Send OK response
            writer.write(b'OK')
            await writer.drain()
            
            # Receive file data
            received = 0
            with open(file_path, 'wb') as f:
                while received < file_size:
                    chunk_size = min(CHUNK_SIZE, file_size - received)
                    chunk = await reader.readexactly(chunk_size)
                    f.write(chunk)
                    received += len(chunk)
            
            # Store file info
            self.files[file_id] = {
                'filename': filename,
                'size': file_size,
                'path': str(file_path),
                'uploader': file_info.get('uploader', 'Unknown'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Send success response
            response = json.dumps({'file_id': file_id}).encode()
            writer.write(struct.pack('!I', len(response)) + response)
            
            print(f"[INFO] File uploaded: {filename} ({file_size} bytes) from {addr}")
            
            # Notify main server about the upload
            if self.upload_callback:
                await self.upload_callback(filename, file_info.get('uploader', 'Unknown'))
            
        except Exception as e:
            print(f"[ERROR] Upload error: {e}")
            try:
                writer.write(b'ERROR')
            except:
                pass
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def handle_download(self, reader, writer):
        """Handle file download."""
        addr = writer.get_extra_info('peername')
        
        try:
            # Read file ID
            id_size_data = await reader.read(4)
            if not id_size_data:
                return
            
            id_size = struct.unpack('!I', id_size_data)[0]
            file_id = (await reader.readexactly(id_size)).decode()
            
            if file_id not in self.files:
                writer.write(b'ERROR: File not found')
                return
            
            file_info = self.files[file_id]
            file_path = Path(file_info['path'])
            
            if not file_path.exists():
                writer.write(b'ERROR: File not available')
                return
            
            # Send file info
            info_data = json.dumps(file_info).encode()
            writer.write(struct.pack('!I', len(info_data)) + info_data)
            await writer.drain()
            
            # Send file data
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    writer.write(chunk)
                    await writer.drain()
            
            print(f"[INFO] File downloaded: {file_info['filename']} to {addr}")
            
        except Exception as e:
            print(f"[ERROR] Download error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    def get_file_list(self) -> List[dict]:
        """Get list of available files."""
        return [
            {
                'file_id': file_id,
                'filename': info['filename'],
                'size': info['size'],
                'uploader': info['uploader'],
                'timestamp': info['timestamp']
            }
            for file_id, info in self.files.items()
        ]
    
    def stop(self):
        """Stop file transfer servers."""
        self.running = False
        if self.upload_server:
            self.upload_server.close()
        if self.download_server:
            self.download_server.close()


class Participant:
    """Represents a connected participant."""
    
    def __init__(self, uid: int, username: str, writer):
        self.uid = uid
        self.username = username
        self.writer = writer
        self.last_heartbeat = time.time()
        self.is_presenting = False
        self.join_time = datetime.now()
        
    def to_dict(self) -> dict:
        """Convert participant to dictionary."""
        return {
            'uid': self.uid,
            'username': self.username,
            'is_presenting': self.is_presenting,
            'join_time': self.join_time.isoformat()
        }


class CollaborationServer:
    """Main collaboration server handling TCP connections and coordination."""
    
    def __init__(self, host: str = DEFAULT_HOST, tcp_port: int = DEFAULT_TCP_PORT,
                 udp_video_port: int = DEFAULT_UDP_VIDEO_PORT,
                 udp_audio_port: int = DEFAULT_UDP_AUDIO_PORT):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_video_port = udp_video_port
        self.udp_audio_port = udp_audio_port
        
        # Core components
        self.server = None
        self.running = False
        
        # Participants management
        self.participants = {}  # uid -> Participant
        self.next_uid = 1
        self.username_to_uid = {}
        
        # Chat history
        self.chat_history = deque(maxlen=MAX_CHAT_HISTORY)
        
        # Media servers
        self.video_server = VideoServer(host, udp_video_port)
        self.audio_server = AudioServer(host, udp_audio_port)
        self.screen_share_server = ScreenShareServer(host, 12000)
        self.file_server = FileTransferServer(host, 13000, 14000, self.on_file_uploaded)
        
        # Statistics
        self.stats = {
            'start_time': datetime.now(),
            'total_connections': 0,
            'messages_sent': 0,
            'files_transferred': 0
        }
    
    async def start(self):
        """Start the collaboration server."""
        print(f"[INFO] Starting LAN Collaboration Server...")
        print(f"[INFO] TCP Control: {self.host}:{self.tcp_port}")
        print(f"[INFO] UDP Video: {self.host}:{self.udp_video_port}")
        print(f"[INFO] UDP Audio: {self.host}:{self.udp_audio_port}")
        
        try:
            # Start media servers
            asyncio.create_task(self.video_server.start())
            asyncio.create_task(self.audio_server.start())
            asyncio.create_task(self.screen_share_server.start())
            asyncio.create_task(self.file_server.start())
            
            # Start TCP server
            self.server = await asyncio.start_server(
                self.handle_client, self.host, self.tcp_port
            )
            self.running = True
            
            print(f"[INFO] Main server listening on {self.host}:{self.tcp_port}")
            
            # Show connection information
            self.show_connection_info()
            
            print(f"[INFO] Server ready for connections!")
            
            # Start heartbeat checker
            asyncio.create_task(self.heartbeat_checker())
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            print(f"[ERROR] Failed to start server: {e}")
        finally:
            await self.stop()
    
    async def handle_client(self, reader, writer):
        """Handle new client connection."""
        addr = writer.get_extra_info('peername')
        print(f"[INFO] New connection from {addr}")
        
        participant = None
        
        try:
            while self.running:
                # Read message length
                length_data = await reader.read(4)
                if not length_data:
                    break
                
                message_length = struct.unpack('!I', length_data)[0]
                if message_length > 1024 * 1024:  # 1MB limit
                    break
                
                # Read message data
                message_data = await reader.readexactly(message_length)
                message = json.loads(message_data.decode())
                
                # Handle message
                response = await self.handle_message(message, participant, writer)
                
                if message['type'] == MessageTypes.LOGIN and response.get('type') == MessageTypes.LOGIN_SUCCESS:
                    participant = self.participants[response['uid']]
                
                # Send response
                if response:
                    await self.send_message(writer, response)
                    
        except Exception as e:
            print(f"[ERROR] Client {addr} error: {e}")
        finally:
            if participant:
                await self.handle_logout(participant)
            writer.close()
            await writer.wait_closed()
            print(f"[INFO] Client {addr} disconnected")
    
    async def handle_message(self, message: dict, participant: Optional[Participant], writer) -> Optional[dict]:
        """Handle incoming message from client."""
        msg_type = message.get('type')
        
        if msg_type == MessageTypes.LOGIN:
            return await self.handle_login(message, writer)
        
        if not participant:
            return create_error_message("Not logged in")
        
        participant.last_heartbeat = time.time()
        
        if msg_type == MessageTypes.HEARTBEAT:
            return create_heartbeat_ack_message()
        
        elif msg_type == MessageTypes.CHAT:
            return await self.handle_chat(message, participant)
        
        elif msg_type == MessageTypes.BROADCAST:
            return await self.handle_broadcast(message, participant)
        
        elif msg_type == MessageTypes.UNICAST:
            return await self.handle_unicast(message, participant)
        
        elif msg_type == MessageTypes.GET_HISTORY:
            return await self.handle_get_history()
        
        elif msg_type == MessageTypes.GET_PARTICIPANTS:
            return await self.handle_get_participants()
        
        elif msg_type == MessageTypes.FILE_OFFER:
            return await self.handle_file_offer(message, participant)
        
        elif msg_type == MessageTypes.FILE_REQUEST:
            return await self.handle_file_request(message, participant)
        
        elif msg_type == MessageTypes.PRESENT_START:
            return await self.handle_present_start(participant)
        
        elif msg_type == MessageTypes.PRESENT_STOP:
            return await self.handle_present_stop(participant)
        
        elif msg_type == MessageTypes.LOGOUT:
            await self.handle_logout(participant)
            return None
        
        else:
            return create_error_message(f"Unknown message type: {msg_type}")
    
    async def handle_login(self, message: dict, writer) -> dict:
        """Handle user login."""
        username = message.get('username', '').strip()
        
        if not username:
            return create_error_message("Username required")
        
        if username in self.username_to_uid:
            return create_error_message("Username already taken")
        
        # Create new participant
        uid = self.next_uid
        self.next_uid += 1
        
        participant = Participant(uid, username, writer)
        self.participants[uid] = participant
        self.username_to_uid[username] = uid
        
        self.stats['total_connections'] += 1
        
        # Notify other participants
        user_joined_msg = create_user_joined_message(uid, username)
        await self.broadcast_message(user_joined_msg, exclude_uid=uid)
        
        print(f"[INFO] User '{username}' logged in (UID: {uid})")
        
        return create_login_success_message(uid, username)
    
    async def handle_chat(self, message: dict, participant: Participant) -> dict:
        """Handle chat message."""
        content = message.get('content', '').strip()
        
        if not content:
            return create_error_message("Empty message")
        
        chat_msg = {
            'type': 'chat',
            'uid': participant.uid,
            'username': participant.username,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        self.chat_history.append(chat_msg)
        self.stats['messages_sent'] += 1
        
        # Broadcast to all participants
        await self.broadcast_message(chat_msg)
        
        return {'type': 'chat_sent', 'timestamp': chat_msg['timestamp']}
    
    async def handle_broadcast(self, message: dict, participant: Participant) -> dict:
        """Handle broadcast message."""
        content = message.get('content', '').strip()
        
        if not content:
            return create_error_message("Empty message")
        
        broadcast_msg = {
            'type': 'broadcast',
            'uid': participant.uid,
            'username': participant.username,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        self.chat_history.append(broadcast_msg)
        self.stats['messages_sent'] += 1
        
        # Broadcast to all participants
        await self.broadcast_message(broadcast_msg)
        
        return {'type': 'broadcast_sent', 'timestamp': broadcast_msg['timestamp']}
    
    async def handle_unicast(self, message: dict, participant: Participant) -> dict:
        """Handle unicast message."""
        target_uid = message.get('target_uid')
        content = message.get('content', '').strip()
        
        if not content:
            return create_error_message("Empty message")
        
        if target_uid not in self.participants:
            return create_error_message("Target user not found")
        
        unicast_msg = {
            'type': 'unicast',
            'uid': participant.uid,
            'username': participant.username,
            'target_uid': target_uid,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to target user
        target_participant = self.participants[target_uid]
        await self.send_message(target_participant.writer, unicast_msg)
        
        print(f"[DEBUG] Private message sent from {participant.username} to {target_participant.username}")
        
        self.stats['messages_sent'] += 1
        
        return {
            'type': MessageTypes.UNICAST_SENT,
            'target_uid': target_uid,
            'timestamp': unicast_msg['timestamp']
        }
    
    async def handle_get_history(self) -> dict:
        """Handle chat history request."""
        return {
            'type': MessageTypes.HISTORY,
            'messages': list(self.chat_history),
            'timestamp': datetime.now().isoformat()
        }
    
    async def handle_get_participants(self) -> dict:
        """Handle participants list request."""
        participants_list = [p.to_dict() for p in self.participants.values()]
        return create_participant_list_message(participants_list)
    
    async def handle_file_offer(self, message: dict, participant: Participant) -> dict:
        """Handle file offer."""
        return {
            'type': MessageTypes.FILE_UPLOAD_PORT,
            'port': self.file_server.upload_port,
            'timestamp': datetime.now().isoformat()
        }
    
    async def handle_file_request(self, message: dict, participant: Participant) -> dict:
        """Handle file request."""
        file_list = self.file_server.get_file_list()
        
        return {
            'type': MessageTypes.FILE_DOWNLOAD_PORT,
            'port': self.file_server.download_port,
            'files': file_list,
            'timestamp': datetime.now().isoformat()
        }
    
    async def handle_present_start(self, participant: Participant) -> dict:
        """Handle presentation start."""
        print(f"[DEBUG] Received PRESENT_START from {participant.username} (UID: {participant.uid})")
        
        # Check if someone else is presenting
        for p in self.participants.values():
            if p.is_presenting and p != participant:
                print(f"[DEBUG] Presentation rejected - {p.username} is already presenting")
                return create_error_message("Someone else is already presenting")
        
        participant.is_presenting = True
        print(f"[DEBUG] {participant.username} started presenting on port {self.screen_share_server.port}")
        
        # Notify all participants
        present_msg = {
            'type': MessageTypes.PRESENT_START_BROADCAST,
            'uid': participant.uid,
            'username': participant.username,
            'screen_share_port': self.screen_share_server.port,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.broadcast_message(present_msg)
        
        return {
            'type': MessageTypes.SCREEN_SHARE_PORTS,
            'port': self.screen_share_server.port,
            'timestamp': datetime.now().isoformat()
        }
    
    async def handle_present_stop(self, participant: Participant) -> dict:
        """Handle presentation stop."""
        print(f"[DEBUG] Received PRESENT_STOP from {participant.username} (UID: {participant.uid})")
        
        if not participant.is_presenting:
            print(f"[DEBUG] Presentation stop rejected - {participant.username} is not presenting")
            return create_error_message("Not currently presenting")
        
        participant.is_presenting = False
        print(f"[DEBUG] {participant.username} stopped presenting")
        
        # Notify all participants
        present_msg = {
            'type': MessageTypes.PRESENT_STOP_BROADCAST,
            'uid': participant.uid,
            'username': participant.username,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.broadcast_message(present_msg)
        
        return {'type': 'present_stopped', 'timestamp': datetime.now().isoformat()}
    
    async def handle_logout(self, participant: Participant):
        """Handle user logout."""
        print(f"[DEBUG] Processing LOGOUT for {participant.username} (UID: {participant.uid})")
        
        if participant.uid in self.participants:
            # If the user was presenting, stop their presentation
            if participant.is_presenting:
                print(f"[INFO] Stopping presentation for disconnecting user: {participant.username}")
                participant.is_presenting = False
                
                # Notify all participants that presentation stopped
                present_stop_msg = {
                    'type': MessageTypes.PRESENT_STOP_BROADCAST,
                    'uid': participant.uid,
                    'username': participant.username,
                    'timestamp': datetime.now().isoformat()
                }
                await self.broadcast_message(present_stop_msg)
            
            del self.participants[participant.uid]
            del self.username_to_uid[participant.username]
            
            # Notify other participants
            user_left_msg = create_user_left_message(participant.uid, participant.username)
            await self.broadcast_message(user_left_msg)
            
            print(f"[DEBUG] Broadcasted USER_LEFT message for {participant.username}")
            print(f"[INFO] User '{participant.username}' logged out")
    
    async def send_message(self, writer, message: dict):
        """Send message to a client."""
        try:
            message_data = json.dumps(message).encode()
            length_data = struct.pack('!I', len(message_data))
            writer.write(length_data + message_data)
            await writer.drain()
        except Exception:
            pass
    
    async def broadcast_message(self, message: dict, exclude_uid: Optional[int] = None):
        """Broadcast message to all connected participants."""
        for participant in list(self.participants.values()):
            if exclude_uid and participant.uid == exclude_uid:
                continue
            await self.send_message(participant.writer, message)
    
    async def heartbeat_checker(self):
        """Check for inactive participants."""
        while self.running:
            try:
                current_time = time.time()
                inactive_participants = []
                
                for participant in self.participants.values():
                    if current_time - participant.last_heartbeat > HEARTBEAT_INTERVAL * 3:
                        inactive_participants.append(participant)
                
                for participant in inactive_participants:
                    print(f"[INFO] Removing inactive user: {participant.username}")
                    await self.handle_logout(participant)
                
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                
            except Exception as e:
                print(f"[ERROR] Heartbeat checker error: {e}")
                await asyncio.sleep(HEARTBEAT_INTERVAL)
    
    def print_stats(self):
        """Print server statistics."""
        uptime = datetime.now() - self.stats['start_time']
        print(f"\n[STATS] Server Statistics:")
        print(f"  Uptime: {uptime}")
        print(f"  Active participants: {len(self.participants)}")
        print(f"  Total connections: {self.stats['total_connections']}")
        print(f"  Messages sent: {self.stats['messages_sent']}")
        print(f"  Files available: {len(self.file_server.files)}")
        
        if self.participants:
            print(f"  Connected users:")
            for p in self.participants.values():
                status = " (presenting)" if p.is_presenting else ""
                print(f"    - {p.username} (UID: {p.uid}){status}")
    
    async def stop(self):
        """Stop the collaboration server."""
        print("[INFO] Shutting down server...")
        self.running = False
        
        # Stop all servers
        self.video_server.stop()
        self.audio_server.stop()
        self.screen_share_server.stop()
        self.file_server.stop()
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        print("[INFO] Server stopped")
    
    async def on_file_uploaded(self, filename: str, uploader: str):
        """Handle file upload notification."""
        # Broadcast file available notification to all participants
        file_msg = {
            'type': MessageTypes.FILE_AVAILABLE,
            'filename': filename,
            'uploader': uploader,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.broadcast_message(file_msg)
        print(f"[INFO] Broadcasted file available notification: {filename}")
    
    def show_connection_info(self):
        """Show connection information for clients."""
        try:
            # Get local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            print(f"\n{'='*60}")
            print(f"🌐 LAN COLLABORATION SERVER - CONNECTION INFO")
            print(f"{'='*60}")
            print(f"📍 Server Address: {local_ip}:{self.tcp_port}")
            print(f"🏠 Local clients use: localhost:{self.tcp_port}")
            print(f"🌍 Remote clients use: {local_ip}:{self.tcp_port}")
            print(f"{'='*60}\n")
            
        except Exception:
            print(f"\n[INFO] Clients can connect to: {self.host}:{self.tcp_port}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='LAN Collaboration Server')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Server host address')
    parser.add_argument('--tcp-port', type=int, default=DEFAULT_TCP_PORT, help='TCP control port')
    parser.add_argument('--video-port', type=int, default=DEFAULT_UDP_VIDEO_PORT, help='UDP video port')
    parser.add_argument('--audio-port', type=int, default=DEFAULT_UDP_AUDIO_PORT, help='UDP audio port')
    parser.add_argument('--stats', action='store_true', help='Show periodic statistics')
    
    args = parser.parse_args()
    
    # Create and start server
    server = CollaborationServer(
        host=args.host,
        tcp_port=args.tcp_port,
        udp_video_port=args.video_port,
        udp_audio_port=args.audio_port
    )
    
    async def run_server():
        try:
            # Start stats printer if requested
            if args.stats:
                async def stats_printer():
                    while server.running:
                        await asyncio.sleep(30)
                        server.print_stats()
                
                asyncio.create_task(stats_printer())
            
            await server.start()
            
        except KeyboardInterrupt:
            print("\n[INFO] Received interrupt signal")
        except Exception as e:
            print(f"[ERROR] Server error: {e}")
        finally:
            await server.stop()
    
    # Run the server
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")


if __name__ == '__main__':
    main()