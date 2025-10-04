"""
User management system for the LAN Video Calling Application
Handles user authentication, sessions, and user state management
"""

import time
import threading
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from shared.constants import *
from shared.utils import logger


@dataclass
class User:
    """User data structure"""
    user_id: str
    username: str
    connection: Any = None
    room_id: Optional[str] = None
    is_online: bool = True
    is_muted: bool = False
    is_video_enabled: bool = True
    is_audio_enabled: bool = True
    is_screen_sharing: bool = False
    last_seen: float = field(default_factory=time.time)
    permissions: Dict[str, bool] = field(default_factory=lambda: {
        'can_mute_others': False,
        'can_kick_users': False,
        'can_manage_rooms': False,
        'can_record': False
    })
    
    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'room_id': self.room_id,
            'is_online': self.is_online,
            'is_muted': self.is_muted,
            'is_video_enabled': self.is_video_enabled,
            'is_audio_enabled': self.is_audio_enabled,
            'is_screen_sharing': self.is_screen_sharing,
            'last_seen': self.last_seen,
            'permissions': self.permissions
        }


class UserManager:
    """Manages users and their sessions"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.username_to_id: Dict[str, str] = {}
        self.lock = threading.RLock()
        self.cleanup_thread = threading.Thread(target=self._cleanup_inactive_users, daemon=True)
        self.cleanup_thread.start()
    
    def create_user(self, username: str, connection: Any = None) -> User:
        """Create a new user"""
        with self.lock:
            # Check if username already exists
            if username in self.username_to_id:
                existing_user_id = self.username_to_id[username]
                if existing_user_id in self.users:
                    existing_user = self.users[existing_user_id]
                    if existing_user.is_online:
                        raise ValueError(f"Username '{username}' is already in use")
                    else:
                        # Reconnect existing user
                        existing_user.connection = connection
                        existing_user.is_online = True
                        existing_user.update_last_seen()
                        return existing_user
            
            # Create new user
            user_id = str(uuid.uuid4())
            user = User(
                user_id=user_id,
                username=username,
                connection=connection
            )
            
            self.users[user_id] = user
            self.username_to_id[username] = user_id
            
            logger.info(f"Created new user: {username} ({user_id})")
            return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        with self.lock:
            return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        with self.lock:
            user_id = self.username_to_id.get(username)
            if user_id:
                return self.users.get(user_id)
            return None
    
    def remove_user(self, user_id: str) -> bool:
        """Remove user from system"""
        with self.lock:
            if user_id in self.users:
                user = self.users[user_id]
                username = user.username
                
                # Remove from room if in one
                if user.room_id:
                    self._leave_room(user_id, user.room_id)
                
                # Clean up connections
                if user.connection:
                    try:
                        user.connection.close()
                    except:
                        pass
                
                # Remove from mappings
                del self.users[user_id]
                if username in self.username_to_id:
                    del self.username_to_id[username]
                
                logger.info(f"Removed user: {username} ({user_id})")
                return True
            return False
    
    def update_user_status(self, user_id: str, **kwargs) -> bool:
        """Update user status"""
        with self.lock:
            user = self.users.get(user_id)
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                user.update_last_seen()
                return True
            return False
    
    def mute_user(self, user_id: str, muted: bool = True) -> bool:
        """Mute/unmute user"""
        return self.update_user_status(user_id, is_muted=muted)
    
    def enable_video(self, user_id: str, enabled: bool = True) -> bool:
        """Enable/disable user video"""
        return self.update_user_status(user_id, is_video_enabled=enabled)
    
    def enable_audio(self, user_id: str, enabled: bool = True) -> bool:
        """Enable/disable user audio"""
        return self.update_user_status(user_id, is_audio_enabled=enabled)
    
    def start_screen_share(self, user_id: str) -> bool:
        """Start screen sharing for user"""
        return self.update_user_status(user_id, is_screen_sharing=True)
    
    def stop_screen_share(self, user_id: str) -> bool:
        """Stop screen sharing for user"""
        return self.update_user_status(user_id, is_screen_sharing=False)
    
    def set_user_permissions(self, user_id: str, permissions: Dict[str, bool]) -> bool:
        """Set user permissions"""
        with self.lock:
            user = self.users.get(user_id)
            if user:
                user.permissions.update(permissions)
                user.update_last_seen()
                return True
            return False
    
    def get_online_users(self) -> List[User]:
        """Get all online users"""
        with self.lock:
            return [user for user in self.users.values() if user.is_online]
    
    def get_users_in_room(self, room_id: str) -> List[User]:
        """Get all users in a specific room"""
        with self.lock:
            return [user for user in self.users.values() 
                   if user.is_online and user.room_id == room_id]
    
    def get_user_list(self) -> List[Dict[str, Any]]:
        """Get list of all users as dictionaries"""
        with self.lock:
            return [user.to_dict() for user in self.users.values()]
    
    def _leave_room(self, user_id: str, room_id: str):
        """Internal method to remove user from room"""
        user = self.users.get(user_id)
        if user and user.room_id == room_id:
            user.room_id = None
            user.is_screen_sharing = False
    
    def _cleanup_inactive_users(self):
        """Clean up inactive users (runs in background thread)"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                current_time = time.time()
                
                with self.lock:
                    inactive_users = []
                    for user_id, user in self.users.items():
                        if not user.is_online:
                            continue
                        
                        # Consider user inactive if no activity for 5 minutes
                        if current_time - user.last_seen > 300:
                            inactive_users.append(user_id)
                    
                    for user_id in inactive_users:
                        logger.info(f"Cleaning up inactive user: {user_id}")
                        self.remove_user(user_id)
                        
            except Exception as e:
                logger.error(f"Error in user cleanup: {e}")
    
    def disconnect_user(self, user_id: str) -> bool:
        """Disconnect user (mark as offline but keep in system)"""
        with self.lock:
            user = self.users.get(user_id)
            if user:
                user.is_online = False
                user.connection = None
                user.update_last_seen()
                logger.info(f"Disconnected user: {user.username} ({user_id})")
                return True
            return False
    
    def reconnect_user(self, user_id: str, connection: Any) -> bool:
        """Reconnect user with new connection"""
        with self.lock:
            user = self.users.get(user_id)
            if user:
                user.connection = connection
                user.is_online = True
                user.update_last_seen()
                logger.info(f"Reconnected user: {user.username} ({user_id})")
                return True
            return False
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        with self.lock:
            total_users = len(self.users)
            online_users = len([u for u in self.users.values() if u.is_online])
            users_in_rooms = len([u for u in self.users.values() 
                                if u.is_online and u.room_id])
            
            return {
                'total_users': total_users,
                'online_users': online_users,
                'users_in_rooms': users_in_rooms,
                'offline_users': total_users - online_users
            }
