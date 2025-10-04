"""
Media server for handling video and audio streaming in the LAN Video Calling Application
"""

import time
import threading
import queue
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available. Video processing will be limited.")
from typing import Dict, List, Optional, Any, Tuple
from shared.constants import *
from shared.utils import logger
from shared.protocol import VideoFrame, AudioFrame, Message, MessageType
from .user_manager import UserManager
from .room_manager import RoomManager


class MediaStream:
    """Represents a media stream from a user"""
    
    def __init__(self, user_id: str, stream_type: str):
        self.user_id = user_id
        self.stream_type = stream_type  # 'video', 'audio', 'screen'
        self.is_active = False
        self.last_frame_time = 0
        self.frame_count = 0
        self.quality = 80  # Video quality (1-100)
        self.fps = 30  # Frames per second
        self.bitrate = 1000000  # Bits per second
        self.resolution = (VIDEO_WIDTH, VIDEO_HEIGHT)
        self.codec = 'H264'  # Video codec
        self.audio_sample_rate = AUDIO_SAMPLE_RATE
        self.audio_channels = AUDIO_CHANNELS
    
    def update_frame_time(self):
        """Update last frame time"""
        self.last_frame_time = time.time()
        self.frame_count += 1
    
    def is_streaming(self) -> bool:
        """Check if stream is active and recent"""
        if not self.is_active:
            return False
        
        # Consider stream inactive if no frames for 5 seconds
        return time.time() - self.last_frame_time < 5.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stream statistics"""
        return {
            'user_id': self.user_id,
            'stream_type': self.stream_type,
            'is_active': self.is_active,
            'is_streaming': self.is_streaming(),
            'frame_count': self.frame_count,
            'last_frame_time': self.last_frame_time,
            'quality': self.quality,
            'fps': self.fps,
            'bitrate': self.bitrate,
            'resolution': self.resolution
        }


class MediaServer:
    """Handles video and audio streaming"""
    
    def __init__(self, user_manager: UserManager, room_manager: RoomManager):
        self.user_manager = user_manager
        self.room_manager = room_manager
        self.video_streams: Dict[str, MediaStream] = {}
        self.audio_streams: Dict[str, MediaStream] = {}
        self.screen_streams: Dict[str, MediaStream] = {}
        self.lock = threading.RLock()
        
        # Video processing
        self.video_processor = VideoProcessor()
        self.audio_processor = AudioProcessor()
        
        # Statistics
        self.total_frames_sent = 0
        self.total_audio_frames_sent = 0
        self.start_time = time.time()
    
    def start_video_stream(self, user_id: str, resolution: Tuple[int, int] = None, 
                          quality: int = 80, fps: int = 30) -> bool:
        """Start video streaming for a user"""
        with self.lock:
            user = self.user_manager.get_user(user_id)
            if not user:
                return False
            
            # Create or update video stream
            if user_id in self.video_streams:
                stream = self.video_streams[user_id]
            else:
                stream = MediaStream(user_id, 'video')
                self.video_streams[user_id] = stream
            
            # Update stream settings
            stream.is_active = True
            stream.resolution = resolution or (VIDEO_WIDTH, VIDEO_HEIGHT)
            stream.quality = quality
            stream.fps = fps
            stream.update_frame_time()
            
            # Update user status
            self.user_manager.update_user_status(user_id, is_video_enabled=True)
            
            logger.info(f"Started video stream for user {user.username}")
            return True
    
    def stop_video_stream(self, user_id: str) -> bool:
        """Stop video streaming for a user"""
        with self.lock:
            if user_id in self.video_streams:
                self.video_streams[user_id].is_active = False
                self.user_manager.update_user_status(user_id, is_video_enabled=False)
                
                user = self.user_manager.get_user(user_id)
                if user:
                    logger.info(f"Stopped video stream for user {user.username}")
                return True
            return False
    
    def start_audio_stream(self, user_id: str, sample_rate: int = AUDIO_SAMPLE_RATE,
                          channels: int = AUDIO_CHANNELS) -> bool:
        """Start audio streaming for a user"""
        with self.lock:
            user = self.user_manager.get_user(user_id)
            if not user:
                return False
            
            # Create or update audio stream
            if user_id in self.audio_streams:
                stream = self.audio_streams[user_id]
            else:
                stream = MediaStream(user_id, 'audio')
                self.audio_streams[user_id] = stream
            
            # Update stream settings
            stream.is_active = True
            stream.audio_sample_rate = sample_rate
            stream.audio_channels = channels
            stream.update_frame_time()
            
            # Update user status
            self.user_manager.update_user_status(user_id, is_audio_enabled=True)
            
            logger.info(f"Started audio stream for user {user.username}")
            return True
    
    def stop_audio_stream(self, user_id: str) -> bool:
        """Stop audio streaming for a user"""
        with self.lock:
            if user_id in self.audio_streams:
                self.audio_streams[user_id].is_active = False
                self.user_manager.update_user_status(user_id, is_audio_enabled=False)
                
                user = self.user_manager.get_user(user_id)
                if user:
                    logger.info(f"Stopped audio stream for user {user.username}")
                return True
            return False
    
    def start_screen_share(self, user_id: str, resolution: Tuple[int, int] = None,
                          quality: int = 80) -> bool:
        """Start screen sharing for a user"""
        with self.lock:
            user = self.user_manager.get_user(user_id)
            if not user:
                return False
            
            # Create or update screen stream
            if user_id in self.screen_streams:
                stream = self.screen_streams[user_id]
            else:
                stream = MediaStream(user_id, 'screen')
                self.screen_streams[user_id] = stream
            
            # Update stream settings
            stream.is_active = True
            stream.resolution = resolution or (1920, 1080)  # Default screen resolution
            stream.quality = quality
            stream.update_frame_time()
            
            # Update user status
            self.user_manager.update_user_status(user_id, is_screen_sharing=True)
            
            logger.info(f"Started screen share for user {user.username}")
            return True
    
    def stop_screen_share(self, user_id: str) -> bool:
        """Stop screen sharing for a user"""
        with self.lock:
            if user_id in self.screen_streams:
                self.screen_streams[user_id].is_active = False
                self.user_manager.update_user_status(user_id, is_screen_sharing=False)
                
                user = self.user_manager.get_user(user_id)
                if user:
                    logger.info(f"Stopped screen share for user {user.username}")
                return True
            return False
    
    def process_video_frame(self, user_id: str, frame_data: bytes, 
                           width: int, height: int) -> bool:
        """Process and broadcast video frame"""
        with self.lock:
            # Check if user has active video stream
            if user_id not in self.video_streams or not self.video_streams[user_id].is_streaming():
                return False
            
            user = self.user_manager.get_user(user_id)
            if not user or not user.room_id:
                return False
            
            # Update stream statistics
            self.video_streams[user_id].update_frame_time()
            
            # Process frame (compress, optimize)
            processed_frame = self.video_processor.process_frame(
                frame_data, width, height, self.video_streams[user_id].quality
            )
            
            if processed_frame is None:
                return False
            
            # Create video frame message
            video_frame = VideoFrame(
                frame_data=processed_frame,
                width=width,
                height=height,
                user_id=user_id
            )
            
            # Broadcast to room participants
            from shared.protocol import create_video_frame_message
            message = create_video_frame_message(user_id, video_frame, user.room_id)
            
            sent_count = self.room_manager.broadcast_to_room(
                user.room_id, message, exclude_user=user_id
            )
            
            self.total_frames_sent += sent_count
            return sent_count > 0
    
    def process_audio_frame(self, user_id: str, audio_data: bytes,
                           sample_rate: int, channels: int) -> bool:
        """Process and broadcast audio frame"""
        with self.lock:
            # Check if user has active audio stream
            if user_id not in self.audio_streams or not self.audio_streams[user_id].is_streaming():
                return False
            
            user = self.user_manager.get_user(user_id)
            if not user or not user.room_id or user.is_muted:
                return False
            
            # Update stream statistics
            self.audio_streams[user_id].update_frame_time()
            
            # Process audio (noise reduction, compression)
            processed_audio = self.audio_processor.process_audio(
                audio_data, sample_rate, channels
            )
            
            if processed_audio is None:
                return False
            
            # Create audio frame message
            audio_frame = AudioFrame(
                audio_data=processed_audio,
                sample_rate=sample_rate,
                channels=channels,
                user_id=user_id
            )
            
            # Broadcast to room participants
            from shared.protocol import create_audio_frame_message
            message = create_audio_frame_message(user_id, audio_frame, user.room_id)
            
            sent_count = self.room_manager.broadcast_to_room(
                user.room_id, message, exclude_user=user_id
            )
            
            self.total_audio_frames_sent += sent_count
            return sent_count > 0
    
    def process_screen_frame(self, user_id: str, frame_data: bytes,
                            width: int, height: int) -> bool:
        """Process and broadcast screen share frame"""
        with self.lock:
            # Check if user has active screen share
            if user_id not in self.screen_streams or not self.screen_streams[user_id].is_streaming():
                return False
            
            user = self.user_manager.get_user(user_id)
            if not user or not user.room_id:
                return False
            
            # Update stream statistics
            self.screen_streams[user_id].update_frame_time()
            
            # Process frame (compress, optimize for screen sharing)
            processed_frame = self.video_processor.process_screen_frame(
                frame_data, width, height, self.screen_streams[user_id].quality
            )
            
            if processed_frame is None:
                return False
            
            # Create video frame message for screen share
            video_frame = VideoFrame(
                frame_data=processed_frame,
                width=width,
                height=height,
                user_id=user_id
            )
            
            # Broadcast to room participants
            from shared.protocol import create_video_frame_message
            message = create_video_frame_message(user_id, video_frame, user.room_id)
            message.type = MessageType.SCREEN_SHARE  # Mark as screen share
            
            sent_count = self.room_manager.broadcast_to_room(
                user.room_id, message, exclude_user=user_id
            )
            
            return sent_count > 0
    
    def get_stream_stats(self, user_id: str) -> Dict[str, Any]:
        """Get streaming statistics for a user"""
        with self.lock:
            stats = {
                'user_id': user_id,
                'video_stream': None,
                'audio_stream': None,
                'screen_stream': None
            }
            
            if user_id in self.video_streams:
                stats['video_stream'] = self.video_streams[user_id].get_stats()
            
            if user_id in self.audio_streams:
                stats['audio_stream'] = self.audio_streams[user_id].get_stats()
            
            if user_id in self.screen_streams:
                stats['screen_stream'] = self.screen_streams[user_id].get_stats()
            
            return stats
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get media server statistics"""
        with self.lock:
            uptime = time.time() - self.start_time
            active_video_streams = len([s for s in self.video_streams.values() if s.is_streaming()])
            active_audio_streams = len([s for s in self.audio_streams.values() if s.is_streaming()])
            active_screen_streams = len([s for s in self.screen_streams.values() if s.is_streaming()])
            
            return {
                'uptime': uptime,
                'total_frames_sent': self.total_frames_sent,
                'total_audio_frames_sent': self.total_audio_frames_sent,
                'active_video_streams': active_video_streams,
                'active_audio_streams': active_audio_streams,
                'active_screen_streams': active_screen_streams,
                'total_streams': len(self.video_streams) + len(self.audio_streams) + len(self.screen_streams)
            }


class VideoProcessor:
    """Handles video frame processing and compression"""
    
    def __init__(self):
        if CV2_AVAILABLE:
            self.codec = cv2.VideoWriter_fourcc(*'H264')
        else:
            self.codec = None
    
    def process_frame(self, frame_data: bytes, width: int, height: int, 
                     quality: int = 80) -> Optional[bytes]:
        """Process and compress video frame"""
        try:
            if not CV2_AVAILABLE:
                # Return original data if OpenCV not available
                return frame_data
            
            # Convert bytes to numpy array
            frame_array = np.frombuffer(frame_data, dtype=np.uint8)
            frame = frame_array.reshape((height, width, 3))
            
            # Apply compression
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
            
            if result:
                return encoded_img.tobytes()
            return None
            
        except Exception as e:
            logger.error(f"Error processing video frame: {e}")
            return None
    
    def process_screen_frame(self, frame_data: bytes, width: int, height: int,
                            quality: int = 80) -> Optional[bytes]:
        """Process screen share frame with different compression settings"""
        try:
            # Convert bytes to numpy array
            frame_array = np.frombuffer(frame_data, dtype=np.uint8)
            frame = frame_array.reshape((height, width, 3))
            
            # For screen sharing, use PNG compression for better text quality
            encode_param = [int(cv2.IMWRITE_PNG_COMPRESSION), 9 - (quality // 10)]
            result, encoded_img = cv2.imencode('.png', frame, encode_param)
            
            if result:
                return encoded_img.tobytes()
            return None
            
        except Exception as e:
            logger.error(f"Error processing screen frame: {e}")
            return None


class AudioProcessor:
    """Handles audio frame processing and compression"""
    
    def __init__(self):
        self.noise_reduction = True
        self.volume_normalization = True
    
    def process_audio(self, audio_data: bytes, sample_rate: int, 
                     channels: int) -> Optional[bytes]:
        """Process audio frame"""
        try:
            if not CV2_AVAILABLE:
                # Return original data if numpy not available
                return audio_data
            
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Apply noise reduction (simple implementation)
            if self.noise_reduction:
                audio_array = self._reduce_noise(audio_array)
            
            # Apply volume normalization
            if self.volume_normalization:
                audio_array = self._normalize_volume(audio_array)
            
            return audio_array.tobytes()
            
        except Exception as e:
            logger.error(f"Error processing audio frame: {e}")
            return None
    
    def _reduce_noise(self, audio_array):
        """Simple noise reduction"""
        # Simple high-pass filter to remove low-frequency noise
        if len(audio_array) > 1:
            filtered = np.diff(audio_array)
            filtered = np.append(filtered, [0])  # Maintain array length
            return filtered.astype(np.int16)
        return audio_array
    
    def _normalize_volume(self, audio_array):
        """Normalize audio volume"""
        if len(audio_array) == 0:
            return audio_array
        
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
        
        if rms > 0:
            # Normalize to 70% of max volume
            target_rms = 0.7 * 32767
            normalized = audio_array * (target_rms / rms)
            return np.clip(normalized, -32768, 32767).astype(np.int16)
        
        return audio_array
