"""
Room management system for the LAN Video Calling Application
Handles meeting rooms, room creation, joining, and room state management
"""

import time
import threading
import uuid
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from shared.constants import *
from shared.utils import logger
from .user_manager import UserManager


@dataclass
class Room:
    """Room data structure"""
    room_id: str
    room_name: str
    created_by: str
    created_at: float = field(default_factory=time.time)
    max_participants: int = 50
    is_private: bool = False
    password: Optional[str] = None
    participants: Set[str] = field(default_factory=set)
    is_recording: bool = False
    recording_start_time: Optional[float] = None
    chat_history: List[Dict[str, Any]] = field(default_factory=list)
    shared_files: List[Dict[str, Any]] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=lambda: {
        'allow_screen_share': True,
        'allow_file_share': True,
        'allow_chat': True,
        'auto_mute_new_users': False,
        'waiting_room_enabled': False
    })
    
    def add_participant(self, user_id: str) -> bool:
        """Add participant to room"""
        if len(self.participants) < self.max_participants:
            self.participants.add(user_id)
            return True
        return False
    
    def remove_participant(self, user_id: str) -> bool:
        """Remove participant from room"""
        if user_id in self.participants:
            self.participants.remove(user_id)
            return True
        return False
    
    def get_participant_count(self) -> int:
        """Get number of participants"""
        return len(self.participants)
    
    def is_full(self) -> bool:
        """Check if room is full"""
        return len(self.participants) >= self.max_participants
    
    def add_chat_message(self, user_id: str, username: str, message: str) -> None:
        """Add message to chat history"""
        chat_entry = {
            'user_id': user_id,
            'username': username,
            'message': message,
            'timestamp': time.time()
        }
        self.chat_history.append(chat_entry)
        
        # Keep only last 100 messages
        if len(self.chat_history) > 100:
            self.chat_history = self.chat_history[-100:]
    
    def add_shared_file(self, file_info: Dict[str, Any]) -> None:
        """Add shared file to room"""
        self.shared_files.append(file_info)
    
    def start_recording(self) -> bool:
        """Start room recording"""
        if not self.is_recording:
            self.is_recording = True
            self.recording_start_time = time.time()
            return True
        return False
    
    def stop_recording(self) -> bool:
        """Stop room recording"""
        if self.is_recording:
            self.is_recording = False
            self.recording_start_time = None
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert room to dictionary"""
        return {
            'room_id': self.room_id,
            'room_name': self.room_name,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'max_participants': self.max_participants,
            'is_private': self.is_private,
            'participant_count': self.get_participant_count(),
            'is_recording': self.is_recording,
            'settings': self.settings
        }


class RoomManager:
    """Manages rooms and room operations"""
    
    def __init__(self, user_manager: UserManager):
        self.rooms: Dict[str, Room] = {}
        self.user_manager = user_manager
        self.lock = threading.RLock()
        self.cleanup_thread = threading.Thread(target=self._cleanup_empty_rooms, daemon=True)
        self.cleanup_thread.start()
    
    def create_room(self, room_name: str, created_by: str, is_private: bool = False, 
                   password: Optional[str] = None, max_participants: int = 50) -> Room:
        """Create a new room"""
        with self.lock:
            # Check if user exists
            user = self.user_manager.get_user(created_by)
            if not user:
                raise ValueError("User not found")
            
            # Generate unique room ID
            room_id = str(uuid.uuid4())
            
            # Create room
            room = Room(
                room_id=room_id,
                room_name=room_name,
                created_by=created_by,
                is_private=is_private,
                password=password,
                max_participants=max_participants
            )
            
            self.rooms[room_id] = room
            logger.info(f"Created room: {room_name} ({room_id}) by {user.username}")
            
            return room
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID"""
        with self.lock:
            return self.rooms.get(room_id)
    
    def join_room(self, room_id: str, user_id: str, password: Optional[str] = None) -> bool:
        """Join a room"""
        with self.lock:
            room = self.rooms.get(room_id)
            user = self.user_manager.get_user(user_id)
            
            if not room or not user:
                return False
            
            # Check if room is full
            if room.is_full():
                return False
            
            # Check password for private rooms
            if room.is_private and room.password != password:
                return False
            
            # Add user to room
            if room.add_participant(user_id):
                # Update user's room
                self.user_manager.update_user_status(user_id, room_id=room_id)
                logger.info(f"User {user.username} joined room {room.room_name}")
                return True
            
            return False
    
    def leave_room(self, room_id: str, user_id: str) -> bool:
        """Leave a room"""
        with self.lock:
            room = self.rooms.get(room_id)
            user = self.user_manager.get_user(user_id)
            
            if not room or not user:
                return False
            
            # Remove user from room
            if room.remove_participant(user_id):
                # Update user's room
                self.user_manager.update_user_status(user_id, room_id=None)
                logger.info(f"User {user.username} left room {room.room_name}")
                return True
            
            return False
    
    def delete_room(self, room_id: str, user_id: str) -> bool:
        """Delete a room (only by creator or admin)"""
        with self.lock:
            room = self.rooms.get(room_id)
            user = self.user_manager.get_user(user_id)
            
            if not room or not user:
                return False
            
            # Check permissions
            if room.created_by != user_id and not user.permissions.get('can_manage_rooms', False):
                return False
            
            # Remove all participants
            for participant_id in list(room.participants):
                self.user_manager.update_user_status(participant_id, room_id=None)
            
            # Delete room
            del self.rooms[room_id]
            logger.info(f"Room {room.room_name} deleted by {user.username}")
            
            return True
    
    def get_room_list(self, include_private: bool = False) -> List[Dict[str, Any]]:
        """Get list of available rooms"""
        with self.lock:
            rooms = []
            for room in self.rooms.values():
                if not room.is_private or include_private:
                    rooms.append(room.to_dict())
            return rooms
    
    def get_room_participants(self, room_id: str) -> List[Dict[str, Any]]:
        """Get list of participants in a room"""
        with self.lock:
            room = self.rooms.get(room_id)
            if not room:
                return []
            
            participants = []
            for user_id in room.participants:
                user = self.user_manager.get_user(user_id)
                if user and user.is_online:
                    participants.append(user.to_dict())
            
            return participants
    
    def broadcast_to_room(self, room_id: str, message: Any, exclude_user: Optional[str] = None) -> int:
        """Broadcast message to all participants in a room"""
        with self.lock:
            room = self.rooms.get(room_id)
            if not room:
                return 0
            
            sent_count = 0
            for user_id in room.participants:
                if exclude_user and user_id == exclude_user:
                    continue
                
                user = self.user_manager.get_user(user_id)
                if user and user.is_online and user.connection:
                    try:
                        user.connection.send(message)
                        sent_count += 1
                    except Exception as e:
                        logger.error(f"Error broadcasting to user {user_id}: {e}")
            
            return sent_count
    
    def add_chat_message(self, room_id: str, user_id: str, message: str) -> bool:
        """Add chat message to room"""
        with self.lock:
            room = self.rooms.get(room_id)
            user = self.user_manager.get_user(user_id)
            
            if not room or not user:
                return False
            
            # Check if user is in room
            if user_id not in room.participants:
                return False
            
            # Add message to chat history
            room.add_chat_message(user_id, user.username, message)
            
            # Broadcast message to all participants
            from shared.protocol import create_chat_message
            chat_msg = create_chat_message(user_id, message, room_id)
            self.broadcast_to_room(room_id, chat_msg, exclude_user=user_id)
            
            return True
    
    def get_chat_history(self, room_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a room"""
        with self.lock:
            room = self.rooms.get(room_id)
            if not room:
                return []
            
            return room.chat_history[-limit:] if limit > 0 else room.chat_history
    
    def start_recording(self, room_id: str, user_id: str) -> bool:
        """Start recording a room"""
        with self.lock:
            room = self.rooms.get(room_id)
            user = self.user_manager.get_user(user_id)
            
            if not room or not user:
                return False
            
            # Check permissions
            if not user.permissions.get('can_record', False):
                return False
            
            return room.start_recording()
    
    def stop_recording(self, room_id: str, user_id: str) -> bool:
        """Stop recording a room"""
        with self.lock:
            room = self.rooms.get(room_id)
            user = self.user_manager.get_user(user_id)
            
            if not room or not user:
                return False
            
            # Check permissions
            if not user.permissions.get('can_record', False):
                return False
            
            return room.stop_recording()
    
    def update_room_settings(self, room_id: str, user_id: str, settings: Dict[str, Any]) -> bool:
        """Update room settings"""
        with self.lock:
            room = self.rooms.get(room_id)
            user = self.user_manager.get_user(user_id)
            
            if not room or not user:
                return False
            
            # Check permissions (creator or admin)
            if room.created_by != user_id and not user.permissions.get('can_manage_rooms', False):
                return False
            
            room.settings.update(settings)
            return True
    
    def add_shared_file(self, room_id: str, file_info: Dict[str, Any]) -> bool:
        """Add shared file to room"""
        with self.lock:
            room = self.rooms.get(room_id)
            if not room:
                return False
            
            room.add_shared_file(file_info)
            return True
    
    def get_shared_files(self, room_id: str) -> List[Dict[str, Any]]:
        """Get shared files for a room"""
        with self.lock:
            room = self.rooms.get(room_id)
            if not room:
                return []
            
            return room.shared_files
    
    def _cleanup_empty_rooms(self):
        """Clean up empty rooms (runs in background thread)"""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                
                with self.lock:
                    empty_rooms = []
                    for room_id, room in self.rooms.items():
                        if room.get_participant_count() == 0:
                            # Keep room for 10 minutes after last participant leaves
                            if time.time() - room.created_at > 600:
                                empty_rooms.append(room_id)
                    
                    for room_id in empty_rooms:
                        room = self.rooms[room_id]
                        logger.info(f"Cleaning up empty room: {room.room_name}")
                        del self.rooms[room_id]
                        
            except Exception as e:
                logger.error(f"Error in room cleanup: {e}")
    
    def get_room_stats(self) -> Dict[str, Any]:
        """Get room statistics"""
        with self.lock:
            total_rooms = len(self.rooms)
            active_rooms = len([r for r in self.rooms.values() if r.get_participant_count() > 0])
            total_participants = sum(r.get_participant_count() for r in self.rooms.values())
            
            return {
                'total_rooms': total_rooms,
                'active_rooms': active_rooms,
                'total_participants': total_participants,
                'empty_rooms': total_rooms - active_rooms
            }
    
    def get_default_room(self):
        """Get the default room (first public room)"""
        with self.lock:
            for room in self.rooms.values():
                if not room.is_private:
                    return room
            return None
    
    def get_all_rooms(self):
        """Get all rooms"""
        with self.lock:
            return list(self.rooms.values())
