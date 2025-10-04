"""
Video client for handling video capture, processing, and display in the LAN Video Calling Application
"""

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available. Video functionality will be limited.")
import threading
import time
import base64
from typing import Dict, Optional, Callable, Tuple
from shared.constants import *
from shared.protocol import VideoFrame, Message, MessageType
from shared.utils import logger


class VideoClient:
    """Handles video capture, processing, and streaming"""
    
    def __init__(self, main_client):
        self.main_client = main_client
        
        # Video capture
        self.camera: Optional[cv2.VideoCapture] = None
        self.camera_thread: Optional[threading.Thread] = None
        self.is_camera_running = False
        
        # Screen capture
        self.screen_capture_thread: Optional[threading.Thread] = None
        self.is_screen_sharing = False
        
        # Video display
        self.remote_frames: Dict[str, np.ndarray] = {}
        self.screen_share_frames: Dict[str, np.ndarray] = {}
        self.display_callbacks: Dict[str, Callable] = {}
        
        # Video settings
        self.video_width = VIDEO_WIDTH
        self.video_height = VIDEO_HEIGHT
        self.video_fps = VIDEO_FPS
        self.video_quality = VIDEO_QUALITY
        
        # Frame processing
        self.frame_processor = VideoFrameProcessor()
        
        # Statistics
        self.frames_sent = 0
        self.frames_received = 0
        self.start_time = time.time()
    
    def start_camera(self, camera_index: int = 0) -> bool:
        """Start video camera capture"""
        try:
            if not CV2_AVAILABLE:
                logger.error("OpenCV not available. Cannot start camera.")
                return False
                
            if self.is_camera_running:
                return True
            
            # Initialize camera
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                logger.error("Failed to open camera")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.video_fps)
            
            # Start capture thread
            self.is_camera_running = True
            self.camera_thread = threading.Thread(target=self._camera_capture_loop, daemon=True)
            self.camera_thread.start()
            
            logger.info("Camera started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting camera: {e}")
            return False
    
    def stop_camera(self) -> bool:
        """Stop video camera capture"""
        try:
            if not self.is_camera_running:
                return True
            
            self.is_camera_running = False
            
            # Wait for thread to finish
            if self.camera_thread and self.camera_thread.is_alive():
                self.camera_thread.join(timeout=2.0)
            
            # Release camera
            if self.camera:
                self.camera.release()
                self.camera = None
            
            logger.info("Camera stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping camera: {e}")
            return False
    
    def start_screen_capture(self) -> bool:
        """Start screen capture for sharing"""
        try:
            if self.is_screen_sharing:
                return True
            
            # Start screen capture thread
            self.is_screen_sharing = True
            self.screen_capture_thread = threading.Thread(target=self._screen_capture_loop, daemon=True)
            self.screen_capture_thread.start()
            
            logger.info("Screen capture started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting screen capture: {e}")
            return False
    
    def stop_screen_capture(self) -> bool:
        """Stop screen capture"""
        try:
            if not self.is_screen_sharing:
                return True
            
            self.is_screen_sharing = False
            
            # Wait for thread to finish
            if self.screen_capture_thread and self.screen_capture_thread.is_alive():
                self.screen_capture_thread.join(timeout=2.0)
            
            logger.info("Screen capture stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping screen capture: {e}")
            return False
    
    def _camera_capture_loop(self):
        """Camera capture loop"""
        frame_interval = 1.0 / self.video_fps
        
        while self.is_camera_running and self.camera:
            try:
                start_time = time.time()
                
                # Capture frame
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to capture frame")
                    continue
                
                # Resize frame if needed
                if frame.shape[:2] != (self.video_height, self.video_width):
                    frame = cv2.resize(frame, (self.video_width, self.video_height))
                
                # Process and send frame
                self._process_and_send_frame(frame, 'video')
                
                # Maintain frame rate
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in camera capture loop: {e}")
                break
    
    def _screen_capture_loop(self):
        """Screen capture loop"""
        frame_interval = 1.0 / 15  # 15 FPS for screen sharing
        
        while self.is_screen_sharing:
            try:
                start_time = time.time()
                
                # Capture screen (simplified - would need platform-specific implementation)
                screen_frame = self._capture_screen()
                if screen_frame is not None:
                    # Resize for transmission
                    screen_frame = cv2.resize(screen_frame, (1280, 720))
                    
                    # Process and send frame
                    self._process_and_send_frame(screen_frame, 'screen')
                
                # Maintain frame rate
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in screen capture loop: {e}")
                break
    
    def _capture_screen(self):
        """Capture screen (platform-specific implementation needed)"""
        try:
            # This is a simplified implementation
            # In a real application, you would use platform-specific libraries
            # like mss (Multi-Screen Shot) for cross-platform screen capture
            
            # For now, return a placeholder frame
            placeholder = np.zeros((720, 1280, 3), dtype=np.uint8)
            cv2.putText(placeholder, "Screen Share", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
            return placeholder
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None
    
    def _process_and_send_frame(self, frame, frame_type: str):
        """Process frame and send to server"""
        try:
            # Process frame (compress, optimize)
            processed_frame = self.frame_processor.process_frame(frame, self.video_quality)
            if processed_frame is None:
                return
            
            # Encode frame
            frame_bytes = processed_frame.tobytes()
            
            # Create video frame
            video_frame = VideoFrame(
                frame_data=frame_bytes,
                width=frame.shape[1],
                height=frame.shape[0],
                user_id=self.main_client.user_id
            )
            
            # Send to server
            if frame_type == 'video':
                message = Message(
                    msg_type=MessageType.VIDEO_FRAME,
                    data=video_frame.to_dict(),
                    sender=self.main_client.user_id,
                    room_id=self.main_client.current_room_id
                )
            else:  # screen share
                message = Message(
                    msg_type=MessageType.SCREEN_SHARE,
                    data=video_frame.to_dict(),
                    sender=self.main_client.user_id,
                    room_id=self.main_client.current_room_id
                )
            
            self.main_client.send_message(message)
            self.frames_sent += 1
            
        except Exception as e:
            logger.error(f"Error processing and sending frame: {e}")
    
    def display_remote_frame(self, user_id: str, frame):
        """Display remote video frame"""
        try:
            self.remote_frames[user_id] = frame
            self.frames_received += 1
            
            # Call display callback if set
            if 'on_frame_received' in self.display_callbacks:
                self.display_callbacks['on_frame_received'](user_id, frame)
            
        except Exception as e:
            logger.error(f"Error displaying remote frame: {e}")
    
    def display_screen_share(self, user_id: str, frame):
        """Display screen share frame"""
        try:
            self.screen_share_frames[user_id] = frame
            
            # Call display callback if set
            if 'on_screen_share' in self.display_callbacks:
                self.display_callbacks['on_screen_share'](user_id, frame)
            
        except Exception as e:
            logger.error(f"Error displaying screen share: {e}")
    
    def get_remote_frame(self, user_id: str):
        """Get remote frame for a user"""
        return self.remote_frames.get(user_id)
    
    def get_screen_share_frame(self, user_id: str):
        """Get screen share frame for a user"""
        return self.screen_share_frames.get(user_id)
    
    def set_display_callback(self, event: str, callback: Callable):
        """Set display callback"""
        self.display_callbacks[event] = callback
    
    def set_video_settings(self, width: int, height: int, fps: int, quality: int):
        """Set video settings"""
        self.video_width = width
        self.video_height = height
        self.video_fps = fps
        self.video_quality = quality
        
        # Update camera settings if running
        if self.camera and self.camera.isOpened():
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.camera.set(cv2.CAP_PROP_FPS, fps)
    
    def get_video_stats(self) -> Dict[str, any]:
        """Get video statistics"""
        uptime = time.time() - self.start_time
        fps_sent = self.frames_sent / uptime if uptime > 0 else 0
        fps_received = self.frames_received / uptime if uptime > 0 else 0
        
        return {
            'is_camera_running': self.is_camera_running,
            'is_screen_sharing': self.is_screen_sharing,
            'frames_sent': self.frames_sent,
            'frames_received': self.frames_received,
            'fps_sent': fps_sent,
            'fps_received': fps_received,
            'active_remote_streams': len(self.remote_frames),
            'active_screen_shares': len(self.screen_share_frames),
            'video_settings': {
                'width': self.video_width,
                'height': self.video_height,
                'fps': self.video_fps,
                'quality': self.video_quality
            }
        }
    
    def stop(self):
        """Stop all video operations"""
        self.stop_camera()
        self.stop_screen_capture()
        self.remote_frames.clear()
        self.screen_share_frames.clear()


class VideoFrameProcessor:
    """Processes video frames for transmission"""
    
    def __init__(self):
        self.compression_quality = 80
        self.noise_reduction = True
        self.brightness_adjustment = 0
        self.contrast_adjustment = 1.0
    
    def process_frame(self, frame, quality: int = 80):
        """Process frame for transmission"""
        try:
            processed_frame = frame.copy()
            
            # Apply brightness and contrast adjustments
            if self.brightness_adjustment != 0 or self.contrast_adjustment != 1.0:
                processed_frame = cv2.convertScaleAbs(
                    processed_frame, 
                    alpha=self.contrast_adjustment, 
                    beta=self.brightness_adjustment
                )
            
            # Apply noise reduction
            if self.noise_reduction:
                processed_frame = cv2.bilateralFilter(processed_frame, 9, 75, 75)
            
            # Compress frame
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            result, encoded_img = cv2.imencode('.jpg', processed_frame, encode_param)
            
            if result:
                # Decode back to get compressed frame
                compressed_frame = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
                return compressed_frame
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return None
    
    def set_compression_quality(self, quality: int):
        """Set compression quality (1-100)"""
        self.compression_quality = max(1, min(100, quality))
    
    def set_noise_reduction(self, enabled: bool):
        """Enable/disable noise reduction"""
        self.noise_reduction = enabled
    
    def set_brightness_contrast(self, brightness: int, contrast: float):
        """Set brightness and contrast adjustments"""
        self.brightness_adjustment = brightness
        self.contrast_adjustment = max(0.1, min(3.0, contrast))
