"""
Host Server for the LAN Video Calling Application
Acts as both server and host participant with full meeting control capabilities
"""

import socket
import threading
import time
import json
import sys
import os
import uuid
from typing import Dict, Any, Optional
from shared.constants import *
from shared.protocol import *
from shared.utils import logger, get_local_ip, get_available_port
from .main_server import LANVideoServer, ClientConnection
from .user_manager import UserManager
from .room_manager import RoomManager
from .file_server import FileServer
from .media_server import MediaServer


class HostServer(LANVideoServer):
    """Host-enabled server that acts as both server and host participant"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = DEFAULT_SERVER_PORT, host_username: str = "Host"):
        super().__init__(host, port)
        self.host_username = host_username
        self.host_id = "host_" + str(uuid.uuid4())[:8]
        self.is_host_connected = False
        
        # Host-specific capabilities
        self.meeting_controls = {
            'mute_all': False,
            'disable_video_all': False,
            'recording': False,
            'screen_sharing': False,
            'chat_enabled': True,
            'file_sharing_enabled': True
        }
        
        # Host privileges
        self.host_privileges = {
            'kick_participants': True,
            'mute_participants': True,
            'disable_video_participants': True,
            'control_recording': True,
            'manage_rooms': True,
            'view_all_messages': True,
            'download_all_files': True
        }
    
    def start_host_mode(self) -> bool:
        """Start server in host mode"""
        if not self.start():
            return False
        
        # Create default meeting room
        self._create_default_room()
        
        logger.info(f"Host server started. Waiting for host '{self.host_username}' to connect.")
        return True
    
    def _handle_connect(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle user connection with host privileges check"""
        try:
            username = message.data.get('username')
            if not username:
                self._send_error(connection, "Username required")
                return
            
            # Create user
            user = self.user_manager.create_user(username, connection)
            connection.is_authenticated = True
            
            # Check if this is the host connecting
            if username == self.host_username and not self.is_host_connected:
                self.is_host_connected = True
                user.is_host = True
                user.user_id = self.host_id  # Assign the predefined host ID
                self.user_manager.remap_user_id(user.user_id, self.host_id)
                connection.user_id = self.host_id
                logger.info(f"Host '{username}' has connected. ID: {self.host_id}")
            else:
                connection.user_id = user.user_id

            # Send success response with room info
            default_room = self.room_manager.get_default_room()
            response = Message(
                msg_type=MessageType.SUCCESS,
                data={
                    'user_id': user.user_id,
                    'message': 'Connected successfully',
                    'is_host': user.is_host,
                    'default_room': default_room.to_dict() if default_room else None,
                    'meeting_controls': self.meeting_controls
                }
            )
            connection.send(response)
            
            # Broadcast user join
            self._broadcast_user_join(user)
            
            logger.info(f"User {username} connected with ID {user.user_id}")
            
            # Automatically join user to the default room
            default_room = self.room_manager.get_default_room()
            if default_room:
                # Use the overridden _handle_room_join to add the user
                join_message = Message(msg_type=MessageType.ROOM_JOIN, data={'room_id': default_room.room_id})
                self._handle_room_join(connection_id, connection, join_message)

        except Exception as e:
            self._send_error(connection, str(e))

    def _create_default_room(self):
        """Create default meeting room"""
        try:
            # Create a temporary user for room creation
            temp_user_id = "temp_" + str(uuid.uuid4())[:8]
            room = self.room_manager.create_room(
                room_name="Main Meeting Room",
                created_by=temp_user_id,
                is_private=False,
                password=None,
                max_participants=100
            )
            logger.info(f"Default room created: {room.room_name} ({room.room_id})")
            
        except Exception as e:
            logger.error(f"Failed to create default room: {e}")

    
    def _send_meeting_state_to_user(self, connection: ClientConnection):
        """Send current meeting state to a user"""
        try:
            # Get all rooms and participants
            rooms = self.room_manager.get_all_rooms()
            participants = []
            
            for room in rooms:
                room_participants = self.room_manager.get_room_participants(room.room_id)
                participants.extend(room_participants)
            
            # Send meeting state
            state_message = Message(
                msg_type=MessageType.MEETING_STATE,
                data={
                    'host_username': self.host_username,
                    'meeting_controls': self.meeting_controls,
                    'rooms': [room.to_dict() for room in rooms],
                    'participants': participants,
                    'host_privileges': self.host_privileges
                }
            )
            connection.send(state_message)
            
        except Exception as e:
            logger.error(f"Error sending meeting state: {e}")
    
    def _handle_room_create(self, connection_id: str, connection: ClientConnection, message: Message):
        """Disable room creation for clients in host mode."""
        if connection.user_id != self.host_id:
            self._send_error(connection, "Room creation is disabled in this meeting.")

    def _handle_room_join(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle room join with host approval"""
        if not connection.is_authenticated:
            self._send_error(connection, "Not authenticated")
            return
        
        try:
            room_id = message.data.get('room_id')
            password = message.data.get('password')
            
            if not room_id:
                self._send_error(connection, "Room ID required")
                return
            
            # Check if room exists
            room = self.room_manager.get_room(room_id)
            if not room:
                self._send_error(connection, "Room not found")
                return
            
            # Join room
            success = self.room_manager.join_room(room_id, connection.user_id, password)
            
            if success:
                participants = self.room_manager.get_room_participants(room_id)
                
                # Send success response
                response = Message(
                    msg_type=MessageType.SUCCESS,
                    data={
                        'room': room.to_dict(),
                        'participants': participants,
                        'meeting_controls': self.meeting_controls
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
                    
                    # Notify host of new participant
                    if self.is_host_connected and connection.user_id != self.host_id and user:
                        self._notify_host_participant_join(user, room)
            else:
                self._send_error(connection, "Failed to join room")
                
        except Exception as e:
            self._send_error(connection, str(e))
    
    def _handle_chat_message(self, connection_id: str, connection: ClientConnection, message: Message):
        """Handle chat message with host monitoring"""
        if not connection.is_authenticated:
            return
        
        try:
            room_id = message.data.get('room_id')
            message_text = message.data.get('message')
            
            if room_id and message_text:
                # Check if chat is enabled
                if not self.meeting_controls['chat_enabled']:
                    self._send_error(connection, "Chat is disabled by host")
                    return
                
                success = self.room_manager.add_chat_message(
                    room_id, connection.user_id, message_text
                )
                
                if success:
                    # Notify host of message (if not from host)
                    if self.is_host_connected and connection.user_id != self.host_id:
                        self._notify_host_chat_message(connection.user_id, room_id, message_text)
                else:
                    self._send_error(connection, "Failed to send message")
                    
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
    
    # Host control methods
    def mute_all_participants(self, mute: bool = True):
        """Mute/unmute all participants"""
        self.meeting_controls['mute_all'] = mute
        
        # Broadcast control change
        control_message = Message(
            msg_type=MessageType.MEETING_CONTROL,
            data={
                'control': 'mute_all',
                'value': mute,
                'host_username': self.host_username
            }
        )
        self._broadcast_to_all(control_message)
        
        logger.info(f"Host {self.host_username} {'muted' if mute else 'unmuted'} all participants")
    
    def disable_video_all_participants(self, disable: bool = True):
        """Disable/enable video for all participants"""
        self.meeting_controls['disable_video_all'] = disable
        
        # Broadcast control change
        control_message = Message(
            msg_type=MessageType.MEETING_CONTROL,
            data={
                'control': 'disable_video_all',
                'value': disable,
                'host_username': self.host_username
            }
        )
        self._broadcast_to_all(control_message)
        
        logger.info(f"Host {self.host_username} {'disabled' if disable else 'enabled'} video for all participants")
    
    def start_recording(self):
        """Start meeting recording"""
        self.meeting_controls['recording'] = True
        
        # Broadcast recording start
        control_message = Message(
            msg_type=MessageType.MEETING_CONTROL,
            data={
                'control': 'recording',
                'value': True,
                'host_username': self.host_username
            }
        )
        self._broadcast_to_all(control_message)
        
        logger.info(f"Host {self.host_username} started recording")
    
    def stop_recording(self):
        """Stop meeting recording"""
        self.meeting_controls['recording'] = False
        
        # Broadcast recording stop
        control_message = Message(
            msg_type=MessageType.MEETING_CONTROL,
            data={
                'control': 'recording',
                'value': False,
                'host_username': self.host_username
            }
        )
        self._broadcast_to_all(control_message)
        
        logger.info(f"Host {self.host_username} stopped recording")
    
    def kick_participant(self, user_id: str, reason: str = "Kicked by host"):
        """Kick a participant from the meeting"""
        if not self.host_privileges['kick_participants']:
            return False
        
        # Get user connection
        connection = self._get_connection_by_user_id(user_id)
        if not connection:
            return False
        
        # Send kick message
        kick_message = Message(
            msg_type=MessageType.KICK,
            data={
                'reason': reason,
                'host_username': self.host_username
            }
        )
        connection.send(kick_message)
        
        # Disconnect user
        self._disconnect_client(f"user_{user_id}", connection)
        
        logger.info(f"Host {self.host_username} kicked user {user_id}: {reason}")
        return True
    
    def toggle_chat(self, enabled: bool):
        """Enable/disable chat for all participants"""
        self.meeting_controls['chat_enabled'] = enabled
        
        # Broadcast control change
        control_message = Message(
            msg_type=MessageType.MEETING_CONTROL,
            data={
                'control': 'chat_enabled',
                'value': enabled,
                'host_username': self.host_username
            }
        )
        self._broadcast_to_all(control_message)
        
        logger.info(f"Host {self.host_username} {'enabled' if enabled else 'disabled'} chat")
    
    def toggle_file_sharing(self, enabled: bool):
        """Enable/disable file sharing for all participants"""
        self.meeting_controls['file_sharing_enabled'] = enabled
        
        # Broadcast control change
        control_message = Message(
            msg_type=MessageType.MEETING_CONTROL,
            data={
                'control': 'file_sharing_enabled',
                'value': enabled,
                'host_username': self.host_username
            }
        )
        self._broadcast_to_all(control_message)
        
        logger.info(f"Host {self.host_username} {'enabled' if enabled else 'disabled'} file sharing")
    
    def get_meeting_stats(self) -> Dict[str, Any]:
        """Get comprehensive meeting statistics"""
        stats = self.get_server_info()
        stats.update({
            'host_username': self.host_username,
            'host_id': self.host_id,
            'is_host_connected': self.is_host_connected,
            'meeting_controls': self.meeting_controls,
            'host_privileges': self.host_privileges
        })
        return stats


def main():
    """Main function to start the host server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LAN Video Calling Host Server')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=DEFAULT_SERVER_PORT, help='Server port')
    parser.add_argument('--username', default='Host', help='Host username')
    
    args = parser.parse_args()
    
    # Create and start host server
    server = HostServer(args.host, args.port, args.username)
    
    try:
        if server.start_host_mode():
            print(f"Host server running on {args.host}:{args.port}")
            print(f"Host username: {args.username}")
            print(f"Local IP: {get_local_ip()}")
            print("Press Ctrl+C to stop the server")
            
            # Keep server running
            while server.is_running:
                time.sleep(1)
        else:
            print("Failed to start host server")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nShutting down host server...")
        server.stop()
    except Exception as e:
        logger.error(f"Host server error: {e}")
        server.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
