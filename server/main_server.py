"""
Main server for the LAN Video Calling Application
Handles all network connections, message routing, and coordinates all server components
"""

import socket
import threading
import time
import json
import sys
import os
from typing import Dict, Any, Optional
from shared.constants import *
from shared.protocol import *
from shared.utils import logger, get_local_ip, get_available_port
from .user_manager import UserManager
from .room_manager import RoomManager
from .file_server import FileServer
from .media_server import MediaServer


class ClientConnection:
    """Represents a client connection"""
    
    def __init__(self, socket: socket.socket, address: tuple):
        self.socket = socket
        self.address = address
        self.user_id: Optional[str] = None
        self.is_authenticated = False
        self.last_heartbeat = time.time()
        self.receive_thread: Optional[threading.Thread] = None
        self.is_connected = True
    
    def send(self, message: Any) -> bool:
        """Send message to client"""
        try:
            if isinstance(message, Message):
                data = Protocol.pack_message(message)
            else:
                data = message
            
            self.socket.send(data)
            return True
        except Exception as e:
            logger.error(f"Error sending message to {self.address}: {e}")
            return False
    
    def close(self):
        """Close connection"""
        self.is_connected = False
        try:
            self.socket.close()
        except:
            pass


class LANVideoServer:
    """Main server class for LAN Video Calling Application"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = DEFAULT_SERVER_PORT):
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        
        # Server components
        self.user_manager = UserManager()
        self.room_manager = RoomManager(self.user_manager)
        self.file_server = FileServer(self.user_manager, self.room_manager)
        self.media_server = MediaServer(self.user_manager, self.room_manager)
        
        # Connection management
        self.connections: Dict[str, ClientConnection] = {}
        self.connection_lock = threading.RLock()
        
        # Server threads
        self.accept_thread: Optional[threading.Thread] = None
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.stats_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.total_connections = 0
        self.start_time = time.time()
    
    def start(self) -> bool:
        """Start the server"""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(50)
            
            self.is_running = True
            
            # Start server threads
            self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True)
            self.stats_thread = threading.Thread(target=self._stats_monitor, daemon=True)
            
            self.accept_thread.start()
            self.heartbeat_thread.start()
            self.stats_thread.start()
            
            logger.info(f"Server started on {self.host}:{self.port}")
            logger.info(f"Local IP: {get_local_ip()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop(self):
        """Stop the server"""
        self.is_running = False
        
        # Close all connections
        with self.connection_lock:
            for connection in self.connections.values():
                connection.close()
            self.connections.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("Server stopped")
    
    def _accept_connections(self):
        """Accept incoming connections"""
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                client_socket.settimeout(CONNECTION_TIMEOUT)
                
                # Create connection object
                connection = ClientConnection(client_socket, address)
                connection_id = f"{address[0]}:{address[1]}"
                
                with self.connection_lock:
                    self.connections[connection_id] = connection
                    self.total_connections += 1
                
                # Start receive thread for this connection
                receive_thread = threading.Thread(
                    target=self._handle_connection,
                    args=(connection_id, connection),
                    daemon=True
                )
                connection.receive_thread = receive_thread
                receive_thread.start()
                
                logger.info(f"New connection from {address}")
                
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error accepting connection: {e}")
    
    def _handle_connection(self, connection_id: str, connection: ClientConnection):
        """Handle client connection"""
        buffer = b""
        
        while connection.is_connected and self.is_running:
            try:
                # Receive data
                data = connection.socket.recv(4096)
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
                    self._process_message(connection_id, connection, message_data)
                
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error handling connection {connection_id}: {e}")
                break
        
        # Clean up connection
        self._disconnect_client(connection_id, connection)
    
    def _process_message(self, connection_id: str, connection: ClientConnection, message_data: bytes):
        """Process incoming message"""
        try:
            message = Message.from_json(message_data.decode('utf-8'))
            connection.last_heartbeat = time.time()
            
            # Route message based on type
            if message.type == MessageType.CONNECT:
                self._handle_connect(connection_id, connection, message)
            elif message.type == MessageType.DISCONNECT:
                self._handle_disconnect(connection_id, connection, message)
            elif message.type == MessageType.HEARTBEAT:
                self._handle_heartbeat(connection_id, connection, message)
            elif message.type == MessageType.ROOM_CREATE:
                self._handle_room_create(connection_id, connection, message)
            elif message.type == MessageType.ROOM_JOIN:
                self._handle_room_join(connection_id, connection, message)
            elif message.type == MessageType.ROOM_LEAVE:
                self._handle_room_leave(connection_id, connection, message)
            elif message.type == MessageType.CHAT_MESSAGE:
                self._handle_chat_message(connection_id, connection, message)
            elif message.type == MessageType.VIDEO_FRAME:
                self._handle_video_frame(connection_id, connection, message)
            elif message.type == MessageType.AUDIO_FRAME:
                self._handle_audio_frame(connection_id, connection, message)
            elif message.type == MessageType.SCREEN_SHARE:
                self._handle_screen_share(connection_id, connection, message)
            elif message.type == MessageType.FILE_UPLOAD_START:
                self._handle_file_upload_start(connection_id, connection, message)
            elif message.type == MessageType.FILE_UPLOAD_CHUNK:
                self._handle_file_upload_chunk(connection_id, connection, message)
            elif message.type == MessageType.FILE_DOWNLOAD_REQUEST:
                self._handle_file_download_request(connection_id, connection, message)
            else:
                logger.warning(f"Unknown message type: {message.type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _handle_connect(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle user connection"""
        try:
            username = message.data.get('username')
            if not username:
                self._send_error(connection, "Username required")
                return
            
            # Create user
            user = self.user_manager.create_user(username, connection)
            connection.user_id = user.user_id
            connection.is_authenticated = True
            
            # Send success response
            response = Message(
                msg_type=MessageType.SUCCESS,
                data={
                    'user_id': user.user_id,
                    'message': 'Connected successfully'
                }
            )
            connection.send(response)
            
            # Broadcast user join
            self._broadcast_user_join(user)
            
            logger.info(f"User {username} connected with ID {user.user_id}")
            
        except Exception as e:
            self._send_error(connection, str(e))
    
    def _handle_disconnect(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle user disconnection"""
        if connection.user_id:
            user = self.user_manager.get_user(connection.user_id)
            if user:
                # Leave room if in one
                if user.room_id:
                    self.room_manager.leave_room(user.room_id, connection.user_id)
                
                # Broadcast user leave
                self._broadcast_user_leave(user)
                
                # Remove user
                self.user_manager.remove_user(connection.user_id)
                
                logger.info(f"User {user.username} disconnected")
        
        self._disconnect_client(connection_id, connection)
    
    def _handle_heartbeat(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle heartbeat message"""
        connection.last_heartbeat = time.time()
        
        # Send heartbeat response
        response = Message(msg_type=MessageType.ACK)
        connection.send(response)
    
    def _handle_room_create(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle room creation"""
        if not connection.is_authenticated:
            self._send_error(connection, "Not authenticated")
            return
        
        try:
            room_name = message.data.get('room_name')
            is_private = message.data.get('is_private', False)
            password = message.data.get('password')
            max_participants = message.data.get('max_participants', 50)
            
            if not room_name:
                self._send_error(connection, "Room name required")
                return
            
            # Create room
            room = self.room_manager.create_room(
                room_name=room_name,
                created_by=connection.user_id,
                is_private=is_private,
                password=password,
                max_participants=max_participants
            )
            
            # Send success response
            response = Message(
                msg_type=MessageType.SUCCESS,
                data={'room': room.to_dict()}
            )
            connection.send(response)
            
        except Exception as e:
            self._send_error(connection, str(e))
    
    def _handle_room_join(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle room join"""
        if not connection.is_authenticated:
            self._send_error(connection, "Not authenticated")
            return
        
        try:
            room_id = message.data.get('room_id')
            password = message.data.get('password')
            
            if not room_id:
                self._send_error(connection, "Room ID required")
                return
            
            # Join room
            success = self.room_manager.join_room(room_id, connection.user_id, password)
            
            if success:
                room = self.room_manager.get_room(room_id)
                participants = self.room_manager.get_room_participants(room_id)
                
                # Send success response
                response = Message(
                    msg_type=MessageType.SUCCESS,
                    data={
                        'room': room.to_dict(),
                        'participants': participants
                    }
                )
                connection.send(response)
                
                # Broadcast user join to room
                user = self.user_manager.get_user(connection.user_id)
                if user:
                    self._broadcast_to_room(room_id, Message(
                        msg_type=MessageType.USER_JOIN,
                        data=user.to_dict()
                    ), exclude_user=connection.user_id)
            else:
                self._send_error(connection, "Failed to join room")
                
        except Exception as e:
            self._send_error(connection, str(e))
    
    def _handle_room_leave(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle room leave"""
        if not connection.is_authenticated:
            return
        
        try:
            room_id = message.data.get('room_id')
            if room_id:
                success = self.room_manager.leave_room(room_id, connection.user_id)
                
                if success:
                    # Broadcast user leave to room
                    user = self.user_manager.get_user(connection.user_id)
                    if user:
                        self._broadcast_to_room(room_id, Message(
                            msg_type=MessageType.USER_LEAVE,
                            data={'user_id': connection.user_id}
                        ))
                        
        except Exception as e:
            logger.error(f"Error handling room leave: {e}")
    
    def _handle_chat_message(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle chat message"""
        if not connection.is_authenticated:
            return
        
        try:
            room_id = message.data.get('room_id')
            message_text = message.data.get('message')
            
            if room_id and message_text:
                success = self.room_manager.add_chat_message(
                    room_id, connection.user_id, message_text
                )
                
                if not success:
                    self._send_error(connection, "Failed to send message")
                    
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
    
    def _handle_video_frame(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle video frame"""
        if not connection.is_authenticated:
            return
        
        try:
            frame_data = message.data.get('frame_data')
            width = message.data.get('width')
            height = message.data.get('height')
            
            if frame_data and width and height:
                # Decode base64 frame data
                import base64
                frame_bytes = base64.b64decode(frame_data)
                
                # Process video frame
                self.media_server.process_video_frame(
                    connection.user_id, frame_bytes, width, height
                )
                
        except Exception as e:
            logger.error(f"Error handling video frame: {e}")
    
    def _handle_audio_frame(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle audio frame"""
        if not connection.is_authenticated:
            return
        
        try:
            audio_data = message.data.get('audio_data')
            sample_rate = message.data.get('sample_rate')
            channels = message.data.get('channels')
            
            if audio_data and sample_rate and channels:
                # Decode base64 audio data
                import base64
                audio_bytes = base64.b64decode(audio_data)
                
                # Process audio frame
                self.media_server.process_audio_frame(
                    connection.user_id, audio_bytes, sample_rate, channels
                )
                
        except Exception as e:
            logger.error(f"Error handling audio frame: {e}")
    
    def _handle_screen_share(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle screen share frame"""
        if not connection.is_authenticated:
            return
        
        try:
            frame_data = message.data.get('frame_data')
            width = message.data.get('width')
            height = message.data.get('height')
            
            if frame_data and width and height:
                # Decode base64 frame data
                import base64
                frame_bytes = base64.b64decode(frame_data)
                
                # Process screen share frame
                self.media_server.process_screen_frame(
                    connection.user_id, frame_bytes, width, height
                )
                
        except Exception as e:
            logger.error(f"Error handling screen share: {e}")
    
    def _handle_file_upload_start(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle file upload start"""
        if not connection.is_authenticated:
            self._send_error(connection, "Not authenticated")
            return
        
        try:
            filename = message.data.get('filename')
            file_size = message.data.get('file_size')
            room_id = message.data.get('room_id')
            
            if not filename or not file_size:
                self._send_error(connection, "Filename and file size required")
                return
            
            # Start file upload
            file_id = self.file_server.start_file_upload(
                connection.user_id, filename, file_size, room_id
            )
            
            # Send success response
            response = Message(
                msg_type=MessageType.SUCCESS,
                data={'file_id': file_id}
            )
            connection.send(response)
            
        except Exception as e:
            self._send_error(connection, str(e))
    
    def _handle_file_upload_chunk(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle file upload chunk"""
        if not connection.is_authenticated:
            return
        
        try:
            file_id = message.data.get('file_id')
            chunk_index = message.data.get('chunk_index')
            chunk_data = message.data.get('chunk_data')
            checksum = message.data.get('checksum')
            
            if file_id and chunk_index is not None and chunk_data and checksum:
                # Decode base64 chunk data
                import base64
                chunk_bytes = base64.b64decode(chunk_data)
                
                # Upload chunk
                success = self.file_server.upload_chunk(
                    file_id, chunk_index, chunk_bytes, checksum
                )
                
                if success:
                    # Send progress update
                    progress = self.file_server.get_upload_progress(file_id)
                    if progress:
                        response = Message(
                            msg_type=MessageType.ACK,
                            data={'progress': progress}
                        )
                        connection.send(response)
                else:
                    self._send_error(connection, "Failed to upload chunk")
                    
        except Exception as e:
            logger.error(f"Error handling file upload chunk: {e}")
    
    def _handle_file_download_request(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle file download request"""
        if not connection.is_authenticated:
            self._send_error(connection, "Not authenticated")
            return
        
        try:
            file_id = message.data.get('file_id')
            
            if not file_id:
                self._send_error(connection, "File ID required")
                return
            
            # Get file info
            file_info = self.file_server.download_file(file_id, connection.user_id)
            
            if file_info:
                # Send file info
                response = Message(
                    msg_type=MessageType.SUCCESS,
                    data={'file_info': file_info}
                )
                connection.send(response)
            else:
                self._send_error(connection, "File not found or access denied")
                
        except Exception as e:
            self._send_error(connection, str(e))
    
    def _send_error(self, connection: ClientConnection, error_message: str):
        """Send error message to client"""
        error_msg = Message(
            msg_type=MessageType.ERROR,
            data={'message': error_message}
        )
        connection.send(error_msg)
    
    def _broadcast_user_join(self, user):
        """Broadcast user join to all connected clients"""
        message = Message(
            msg_type=MessageType.USER_JOIN,
            data=user.to_dict()
        )
        self._broadcast_to_all(message)
    
    def _broadcast_user_leave(self, user):
        """Broadcast user leave to all connected clients"""
        message = Message(
            msg_type=MessageType.USER_LEAVE,
            data={'user_id': user.user_id, 'username': user.username}
        )
        self._broadcast_to_all(message)
    
    def _broadcast_to_room(self, room_id: str, message: Message, exclude_user: str = None):
        """Broadcast message to all users in a room"""
        participants = self.room_manager.get_room_participants(room_id)
        
        for participant in participants:
            if exclude_user and participant['user_id'] == exclude_user:
                continue
            
            connection = self._get_connection_by_user_id(participant['user_id'])
            if connection:
                connection.send(message)
    
    def _broadcast_to_all(self, message: Message):
        """Broadcast message to all connected clients"""
        with self.connection_lock:
            for connection in self.connections.values():
                if connection.is_authenticated:
                    connection.send(message)
    
    def _get_connection_by_user_id(self, user_id: str) -> Optional[ClientConnection]:
        """Get connection by user ID"""
        with self.connection_lock:
            for connection in self.connections.values():
                if connection.user_id == user_id:
                    return connection
        return None
    
    def _disconnect_client(self, connection_id: str, connection: ClientConnection):
        """Disconnect and clean up client"""
        with self.connection_lock:
            if connection_id in self.connections:
                del self.connections[connection_id]
        
        connection.close()
        logger.info(f"Client {connection_id} disconnected")
    
    def _heartbeat_monitor(self):
        """Monitor client heartbeats and disconnect inactive clients"""
        while self.is_running:
            try:
                time.sleep(HEARTBEAT_INTERVAL)
                current_time = time.time()
                
                inactive_connections = []
                with self.connection_lock:
                    for connection_id, connection in self.connections.items():
                        if current_time - connection.last_heartbeat > CONNECTION_TIMEOUT:
                            inactive_connections.append(connection_id)
                
                for connection_id in inactive_connections:
                    connection = self.connections.get(connection_id)
                    if connection:
                        logger.info(f"Disconnecting inactive client: {connection_id}")
                        self._disconnect_client(connection_id, connection)
                        
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
    
    def _stats_monitor(self):
        """Monitor and log server statistics"""
        while self.is_running:
            try:
                time.sleep(60)  # Log stats every minute
                
                user_stats = self.user_manager.get_user_stats()
                room_stats = self.room_manager.get_room_stats()
                file_stats = self.file_server.get_server_stats()
                media_stats = self.media_server.get_server_stats()
                
                logger.info(f"Server Stats - Users: {user_stats['online_users']}, "
                           f"Rooms: {room_stats['active_rooms']}, "
                           f"Files: {file_stats['total_files']}, "
                           f"Connections: {len(self.connections)}")
                
            except Exception as e:
                logger.error(f"Error in stats monitor: {e}")
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        uptime = time.time() - self.start_time
        return {
            'host': self.host,
            'port': self.port,
            'uptime': uptime,
            'is_running': self.is_running,
            'total_connections': self.total_connections,
            'active_connections': len(self.connections),
            'user_stats': self.user_manager.get_user_stats(),
            'room_stats': self.room_manager.get_room_stats(),
            'file_stats': self.file_server.get_server_stats(),
            'media_stats': self.media_server.get_server_stats()
        }


def main():
    """Main function to start the server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LAN Video Calling Server')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=DEFAULT_SERVER_PORT, help='Server port')
    
    args = parser.parse_args()
    
    # Create and start server
    server = LANVideoServer(args.host, args.port)
    
    try:
        if server.start():
            print(f"Server running on {args.host}:{args.port}")
            print(f"Local IP: {get_local_ip()}")
            print("Press Ctrl+C to stop the server")
            
            # Keep server running
            while server.is_running:
                time.sleep(1)
        else:
            print("Failed to start server")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()
    except Exception as e:
        logger.error(f"Server error: {e}")
        server.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
