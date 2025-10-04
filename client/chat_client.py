"""
Chat client for handling messaging in the LAN Video Calling Application
"""

import time
from typing import List, Dict, Any, Callable
from shared.constants import *
from shared.protocol import Message, MessageType
from shared.utils import logger


class ChatMessage:
    """Represents a chat message"""
    
    def __init__(self, user_id: str, username: str, message: str, timestamp: float = None):
        self.user_id = user_id
        self.username = username
        self.message = message
        self.timestamp = timestamp or time.time()
        self.message_id = f"{user_id}_{int(self.timestamp * 1000)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'message_id': self.message_id,
            'user_id': self.user_id,
            'username': self.username,
            'message': self.message,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create message from dictionary"""
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            message=data['message'],
            timestamp=data.get('timestamp', time.time())
        )


class ChatClient:
    """Handles chat messaging functionality"""
    
    def __init__(self, main_client):
        self.main_client = main_client
        
        # Chat history
        self.chat_history: List[ChatMessage] = []
        self.max_history_size = 1000
        
        # Callbacks
        self.message_callbacks: Dict[str, Callable] = {}
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.start_time = time.time()
    
    def send_message(self, message_text: str) -> bool:
        """Send a chat message"""
        if not self.main_client.is_authenticated or not self.main_client.current_room_id:
            logger.warning("Cannot send message: not authenticated or not in room")
            return False
        
        if not message_text.strip():
            return False
        
        try:
            # Create message
            message = Message(
                msg_type=MessageType.CHAT_MESSAGE,
                data={
                    'room_id': self.main_client.current_room_id,
                    'message': message_text.strip()
                },
                sender=self.main_client.user_id,
                room_id=self.main_client.current_room_id
            )
            
            # Send to server
            success = self.main_client.send_message(message)
            
            if success:
                # Add to local history
                chat_msg = ChatMessage(
                    user_id=self.main_client.user_id,
                    username=self.main_client.username,
                    message=message_text.strip()
                )
                self._add_to_history(chat_msg)
                self.messages_sent += 1
                
                # Call callback
                if 'on_message_sent' in self.message_callbacks:
                    self.message_callbacks['on_message_sent'](chat_msg)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending chat message: {e}")
            return False
    
    def handle_incoming_message(self, message_data: Dict[str, Any]):
        """Handle incoming chat message from server"""
        try:
            # Create chat message
            chat_msg = ChatMessage.from_dict(message_data)
            
            # Add to history
            self._add_to_history(chat_msg)
            self.messages_received += 1
            
            # Call callback
            if 'on_message_received' in self.message_callbacks:
                self.message_callbacks['on_message_received'](chat_msg)
            
        except Exception as e:
            logger.error(f"Error handling incoming chat message: {e}")
    
    def _add_to_history(self, message: ChatMessage):
        """Add message to chat history"""
        self.chat_history.append(message)
        
        # Limit history size
        if len(self.chat_history) > self.max_history_size:
            self.chat_history = self.chat_history[-self.max_history_size:]
    
    def get_chat_history(self, limit: int = None) -> List[ChatMessage]:
        """Get chat history"""
        if limit is None:
            return self.chat_history.copy()
        else:
            return self.chat_history[-limit:] if limit > 0 else []
    
    def get_messages_by_user(self, user_id: str) -> List[ChatMessage]:
        """Get messages from a specific user"""
        return [msg for msg in self.chat_history if msg.user_id == user_id]
    
    def search_messages(self, query: str) -> List[ChatMessage]:
        """Search messages by content"""
        query_lower = query.lower()
        return [msg for msg in self.chat_history if query_lower in msg.message.lower()]
    
    def clear_history(self):
        """Clear chat history"""
        self.chat_history.clear()
        logger.info("Chat history cleared")
    
    def set_message_callback(self, event: str, callback: Callable):
        """Set message callback"""
        self.message_callbacks[event] = callback
    
    def get_chat_stats(self) -> Dict[str, Any]:
        """Get chat statistics"""
        uptime = time.time() - self.start_time
        
        # Count messages by user
        user_message_counts = {}
        for msg in self.chat_history:
            user_message_counts[msg.user_id] = user_message_counts.get(msg.user_id, 0) + 1
        
        return {
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'total_messages': len(self.chat_history),
            'uptime': uptime,
            'messages_per_minute': (self.messages_sent + self.messages_received) / (uptime / 60) if uptime > 0 else 0,
            'user_message_counts': user_message_counts,
            'history_size': len(self.chat_history)
        }
    
    def export_chat_history(self, file_path: str) -> bool:
        """Export chat history to file"""
        try:
            import json
            
            # Convert messages to dictionaries
            messages_data = [msg.to_dict() for msg in self.chat_history]
            
            # Add metadata
            export_data = {
                'export_timestamp': time.time(),
                'room_id': self.main_client.current_room_id,
                'total_messages': len(messages_data),
                'messages': messages_data
            }
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Chat history exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting chat history: {e}")
            return False
    
    def import_chat_history(self, file_path: str) -> bool:
        """Import chat history from file"""
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Import messages
            imported_count = 0
            for msg_data in data.get('messages', []):
                try:
                    chat_msg = ChatMessage.from_dict(msg_data)
                    self._add_to_history(chat_msg)
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"Error importing message: {e}")
            
            logger.info(f"Imported {imported_count} messages from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing chat history: {e}")
            return False
