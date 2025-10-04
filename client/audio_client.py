"""
Audio client for handling audio capture, processing, and playback in the LAN Video Calling Application
"""

try:
    import pyaudio
    import numpy as np
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: PyAudio not available. Audio functionality will be limited.")
import threading
import time
import wave
import io
from typing import Dict, Optional, Callable
from shared.constants import *
from shared.protocol import AudioFrame, Message, MessageType
from shared.utils import logger


class AudioClient:
    """Handles audio capture, processing, and playback"""
    
    def __init__(self, main_client):
        self.main_client = main_client
        
        # Audio capture
        if PYAUDIO_AVAILABLE:
            self.audio = pyaudio.PyAudio()
        else:
            self.audio = None
        self.microphone_stream = None
        self.is_microphone_running = False
        self.microphone_thread: Optional[threading.Thread] = None
        
        # Audio playback
        self.speaker_stream = None
        self.audio_queues: Dict[str, list] = {}  # user_id -> audio queue
        self.playback_threads: Dict[str, threading.Thread] = {}
        self.is_playback_running = False
        
        # Audio settings
        self.sample_rate = AUDIO_SAMPLE_RATE
        self.channels = AUDIO_CHANNELS
        self.chunk_size = AUDIO_CHUNK_SIZE
        if PYAUDIO_AVAILABLE:
            self.format = pyaudio.paInt16
        else:
            self.format = None
        
        # Audio processing
        self.audio_processor = AudioProcessor()
        
        # Audio controls
        self.is_muted = False
        self.volume = 1.0
        self.microphone_volume = 1.0
        
        # Statistics
        self.audio_frames_sent = 0
        self.audio_frames_received = 0
        self.start_time = time.time()
    
    def start_microphone(self) -> bool:
        """Start microphone capture"""
        try:
            if not PYAUDIO_AVAILABLE or not self.audio:
                logger.error("PyAudio not available. Cannot start microphone.")
                return False
                
            if self.is_microphone_running:
                return True
            
            # Create microphone stream
            self.microphone_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=None
            )
            
            # Start capture thread
            self.is_microphone_running = True
            self.microphone_thread = threading.Thread(target=self._microphone_capture_loop, daemon=True)
            self.microphone_thread.start()
            
            logger.info("Microphone started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting microphone: {e}")
            return False
    
    def stop_microphone(self) -> bool:
        """Stop microphone capture"""
        try:
            if not self.is_microphone_running:
                return True
            
            self.is_microphone_running = False
            
            # Wait for thread to finish
            if self.microphone_thread and self.microphone_thread.is_alive():
                self.microphone_thread.join(timeout=2.0)
            
            # Close microphone stream
            if self.microphone_stream:
                self.microphone_stream.stop_stream()
                self.microphone_stream.close()
                self.microphone_stream = None
            
            logger.info("Microphone stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping microphone: {e}")
            return False
    
    def start_speakers(self) -> bool:
        """Start speaker playback"""
        try:
            if self.is_playback_running:
                return True
            
            # Create speaker stream
            self.speaker_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_playback_running = True
            logger.info("Speakers started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting speakers: {e}")
            return False
    
    def stop_speakers(self) -> bool:
        """Stop speaker playback"""
        try:
            if not self.is_playback_running:
                return True
            
            self.is_playback_running = False
            
            # Stop all playback threads
            for thread in self.playback_threads.values():
                if thread.is_alive():
                    thread.join(timeout=1.0)
            self.playback_threads.clear()
            
            # Close speaker stream
            if self.speaker_stream:
                self.speaker_stream.stop_stream()
                self.speaker_stream.close()
                self.speaker_stream = None
            
            # Clear audio queues
            self.audio_queues.clear()
            
            logger.info("Speakers stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping speakers: {e}")
            return False
    
    def _microphone_capture_loop(self):
        """Microphone capture loop"""
        while self.is_microphone_running and self.microphone_stream:
            try:
                # Read audio data
                audio_data = self.microphone_stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Convert to numpy array
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Apply microphone volume
                if self.microphone_volume != 1.0:
                    audio_array = (audio_array * self.microphone_volume).astype(np.int16)
                
                # Process audio
                processed_audio = self.audio_processor.process_audio(audio_array)
                
                # Send audio frame if not muted
                if not self.is_muted and self.main_client.is_authenticated:
                    self._send_audio_frame(processed_audio)
                
            except Exception as e:
                logger.error(f"Error in microphone capture loop: {e}")
                break
    
    def _send_audio_frame(self, audio_data):
        """Send audio frame to server"""
        try:
            # Create audio frame
            audio_frame = AudioFrame(
                audio_data=audio_data.tobytes(),
                sample_rate=self.sample_rate,
                channels=self.channels,
                user_id=self.main_client.user_id
            )
            
            # Send to server
            message = Message(
                msg_type=MessageType.AUDIO_FRAME,
                data=audio_frame.to_dict(),
                sender=self.main_client.user_id,
                room_id=self.main_client.current_room_id
            )
            
            self.main_client.send_message(message)
            self.audio_frames_sent += 1
            
        except Exception as e:
            logger.error(f"Error sending audio frame: {e}")
    
    def play_remote_audio(self, user_id: str, audio_data: bytes):
        """Play remote audio from a user"""
        try:
            if not PYAUDIO_AVAILABLE:
                return
                
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Apply volume
            if self.volume != 1.0:
                audio_array = (audio_array * self.volume).astype(np.int16)
            
            # Add to audio queue
            if user_id not in self.audio_queues:
                self.audio_queues[user_id] = []
                # Start playback thread for this user
                self._start_playback_thread(user_id)
            
            self.audio_queues[user_id].append(audio_array)
            self.audio_frames_received += 1
            
        except Exception as e:
            logger.error(f"Error playing remote audio: {e}")
    
    def _start_playback_thread(self, user_id: str):
        """Start playback thread for a user"""
        if user_id in self.playback_threads:
            return
        
        thread = threading.Thread(
            target=self._playback_loop,
            args=(user_id,),
            daemon=True
        )
        self.playback_threads[user_id] = thread
        thread.start()
    
    def _playback_loop(self, user_id: str):
        """Audio playback loop for a user"""
        while self.is_playback_running and user_id in self.audio_queues:
            try:
                if user_id in self.audio_queues and self.audio_queues[user_id]:
                    # Get audio data from queue
                    audio_data = self.audio_queues[user_id].pop(0)
                    
                    # Play audio
                    if self.speaker_stream and self.speaker_stream.is_active():
                        self.speaker_stream.write(audio_data.tobytes())
                else:
                    # No audio data, wait a bit
                    time.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"Error in playback loop for {user_id}: {e}")
                break
        
        # Clean up
        if user_id in self.audio_queues:
            del self.audio_queues[user_id]
        if user_id in self.playback_threads:
            del self.playback_threads[user_id]
    
    def mute_microphone(self, muted: bool = True):
        """Mute/unmute microphone"""
        self.is_muted = muted
        logger.info(f"Microphone {'muted' if muted else 'unmuted'}")
    
    def set_volume(self, volume: float):
        """Set speaker volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        logger.info(f"Volume set to {self.volume}")
    
    def set_microphone_volume(self, volume: float):
        """Set microphone volume (0.0 to 1.0)"""
        self.microphone_volume = max(0.0, min(1.0, volume))
        logger.info(f"Microphone volume set to {self.microphone_volume}")
    
    def get_audio_stats(self) -> Dict[str, any]:
        """Get audio statistics"""
        uptime = time.time() - self.start_time
        fps_sent = self.audio_frames_sent / uptime if uptime > 0 else 0
        fps_received = self.audio_frames_received / uptime if uptime > 0 else 0
        
        return {
            'is_microphone_running': self.is_microphone_running,
            'is_playback_running': self.is_playback_running,
            'is_muted': self.is_muted,
            'volume': self.volume,
            'microphone_volume': self.microphone_volume,
            'audio_frames_sent': self.audio_frames_sent,
            'audio_frames_received': self.audio_frames_received,
            'fps_sent': fps_sent,
            'fps_received': fps_received,
            'active_audio_streams': len(self.audio_queues),
            'audio_settings': {
                'sample_rate': self.sample_rate,
                'channels': self.channels,
                'chunk_size': self.chunk_size
            }
        }
    
    def stop(self):
        """Stop all audio operations"""
        self.stop_microphone()
        self.stop_speakers()
    
    def __del__(self):
        """Cleanup audio resources"""
        self.stop()
        if hasattr(self, 'audio'):
            self.audio.terminate()


class AudioProcessor:
    """Processes audio for transmission and playback"""
    
    def __init__(self):
        self.noise_reduction = True
        self.echo_cancellation = True
        self.auto_gain_control = True
        self.voice_activity_detection = True
        
        # Audio processing parameters
        self.noise_threshold = 0.01
        self.gain_target = 0.3
        self.echo_delay = 0.1
    
    def process_audio(self, audio_data):
        """Process audio data"""
        try:
            processed_audio = audio_data.copy().astype(np.float32)
            
            # Normalize to [-1, 1] range
            processed_audio = processed_audio / 32768.0
            
            # Apply voice activity detection
            if self.voice_activity_detection:
                if not self._has_voice_activity(processed_audio):
                    # Return silence if no voice activity
                    return np.zeros_like(audio_data)
            
            # Apply noise reduction
            if self.noise_reduction:
                processed_audio = self._reduce_noise(processed_audio)
            
            # Apply echo cancellation (simplified)
            if self.echo_cancellation:
                processed_audio = self._cancel_echo(processed_audio)
            
            # Apply auto gain control
            if self.auto_gain_control:
                processed_audio = self._apply_auto_gain(processed_audio)
            
            # Convert back to int16
            processed_audio = np.clip(processed_audio * 32768.0, -32768, 32767).astype(np.int16)
            
            return processed_audio
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return audio_data
    
    def _has_voice_activity(self, audio_data) -> bool:
        """Detect voice activity in audio"""
        try:
            # Calculate RMS (Root Mean Square)
            rms = np.sqrt(np.mean(audio_data ** 2))
            return rms > self.noise_threshold
        except:
            return True
    
    def _reduce_noise(self, audio_data):
        """Reduce background noise"""
        try:
            # Simple noise reduction using spectral subtraction
            # This is a simplified implementation
            
            # Apply a simple high-pass filter
            if len(audio_data) > 1:
                filtered = np.diff(audio_data)
                filtered = np.append(filtered, [0])
                return filtered
            
            return audio_data
        except:
            return audio_data
    
    def _cancel_echo(self, audio_data):
        """Cancel echo (simplified implementation)"""
        try:
            # This is a placeholder for echo cancellation
            # In a real implementation, you would use more sophisticated algorithms
            return audio_data
        except:
            return audio_data
    
    def _apply_auto_gain(self, audio_data):
        """Apply automatic gain control"""
        try:
            # Calculate current RMS
            rms = np.sqrt(np.mean(audio_data ** 2))
            
            if rms > 0:
                # Calculate gain factor
                gain_factor = self.gain_target / rms
                gain_factor = min(gain_factor, 10.0)  # Limit maximum gain
                
                # Apply gain
                audio_data = audio_data * gain_factor
            
            return audio_data
        except:
            return audio_data
    
    def set_noise_reduction(self, enabled: bool):
        """Enable/disable noise reduction"""
        self.noise_reduction = enabled
    
    def set_echo_cancellation(self, enabled: bool):
        """Enable/disable echo cancellation"""
        self.echo_cancellation = enabled
    
    def set_auto_gain_control(self, enabled: bool):
        """Enable/disable auto gain control"""
        self.auto_gain_control = enabled
    
    def set_voice_activity_detection(self, enabled: bool):
        """Enable/disable voice activity detection"""
        self.voice_activity_detection = enabled
