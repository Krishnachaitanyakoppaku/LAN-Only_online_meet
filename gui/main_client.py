#!/usr/bin/env python3
"""
LAN Communication Client - Clean & Efficient Version
Built from scratch using CN_project best practices and server GUI patterns

Features:
- Multi-user video conferencing (UDP)
- Multi-user audio conferencing (UDP) 
- Screen sharing viewing (TCP)
- Group text chat (TCP)
- File sharing (TCP)
- Clean, responsive GUI
- Robust error handling
- Efficient resource management
"""

import socket
import threading
import json
import time
import struct
import os
import base64
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import queue
import cv2
import pyaudio
from PIL import Image, ImageTk
import numpy as np
import uuid

# Optional imports
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    print("Warning: mss module not available. Screen sharing will be disabled.")

# Protocol constants (matching server)
class MessageTypes:
    # Client to Server
    LOGIN = 'login'
    HEARTBEAT = 'heartbeat'
    CHAT = 'chat'
    BROADCAST = 'broadcast'
    UNICAST = 'unicast'
    FILE_OFFER = 'file_offer'
    FILE_REQUEST = 'file_request'
    PRESENT_START = 'present_start'
    PRESENT_STOP = 'present_stop'
    LOGOUT = 'logout'
    MEDIA_STATUS_UPDATE = 'media_status_update'
    
    # Server to Client
    LOGIN_SUCCESS = 'login_success'
    USER_JOINED = 'user_joined'
    USER_LEFT = 'user_left'
    HEARTBEAT_ACK = 'heartbeat_ack'
    FILE_UPLOAD_PORT = 'file_upload_port'
    FILE_DOWNLOAD_PORT = 'file_download_port'
    FILE_AVAILABLE = 'file_available'
    PRESENT_START_BROADCAST = 'present_start_broadcast'
    PRESENT_STOP_BROADCAST = 'present_stop_broadcast'
    ERROR = 'error'
    HOST_STATUS_UPDATE = 'host_status_update'

# Network Configuration
DEFAULT_TCP_PORT = 8888
DEFAULT_UDP_VIDEO_PORT = 8889
DEFAULT_UDP_AUDIO_PORT = 8890
HEARTBEAT_INTERVAL = 10

# Protocol helper functions
def create_login_message(username: str) -> dict:
    return {"type": MessageTypes.LOGIN, "name": username}  # Server expects 'name', not 'username'

def create_heartbeat_message() -> dict:
    return {"type": MessageTypes.HEARTBEAT, "timestamp": time.time()}

def create_chat_message(text: str) -> dict:
    return {"type": MessageTypes.CHAT, "message": text, "timestamp": time.time()}  # Server expects 'message' field

def create_logout_message() -> dict:
    return {"type": MessageTypes.LOGOUT, "timestamp": time.time()}

def create_media_status_update(video_enabled: bool, audio_enabled: bool) -> dict:
    return {
        "type": MessageTypes.MEDIA_STATUS_UPDATE,
        "video_enabled": video_enabled,
        "audio_enabled": audio_enabled,
        "timestamp": time.time()
    }

class LANCommunicationClient:
    """Clean, efficient LAN Communication Client"""
    
    def __init__(self):
        # Connection settings
        self.server_host = 'localhost'
        self.tcp_port = DEFAULT_TCP_PORT
        self.udp_video_port = DEFAULT_UDP_VIDEO_PORT
        self.udp_audio_port = DEFAULT_UDP_AUDIO_PORT
        
        # Connection state
        self.connected = False
        self.running = True
        self.client_id = None
        self.client_name = ""
        
        # Sockets
        self.tcp_socket = None
        self.udp_video_socket = None
        self.udp_audio_socket = None
        
        # Media state
        self.video_enabled = False
        self.audio_enabled = False
        self.speaker_enabled = True
        self.video_cap = None
        self.audio_stream = None
        self.audio_output_stream = None
        
        # Data structures
        self.participants = {}
        self.chat_history = []
        self.shared_files = {}
        
        # GUI components
        self.root = None
        self.setup_gui()
        
        # Queues for thread-safe GUI updates
        self.video_frame_queue = queue.Queue(maxsize=5)
        self.chat_update_queue = queue.Queue()
        
        # Screen sharing
        self.current_presentation = None
        self.screen_viewer_active = False
        
        print("✅ LAN Communication Client initialized")
    
    def setup_gui(self):
        """Setup clean, efficient GUI"""
        self.root = tk.Tk()
        self.root.title("LAN Communication Client")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2c3e50')
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Show connection screen initially
        self.show_connection_screen(main_frame)
    
    def show_connection_screen(self, parent):
        """Show connection screen"""
        # Clear parent
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Connection frame
        conn_frame = tk.Frame(parent, bg='#34495e', relief=tk.RAISED, bd=2)
        conn_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(conn_frame, text="🌐 LAN Communication Client", 
                              font=('Segoe UI', 24, 'bold'), 
                              fg='#ecf0f1', bg='#34495e')
        title_label.pack(pady=30)
        
        # Connection form
        form_frame = tk.Frame(conn_frame, bg='#34495e')
        form_frame.pack(expand=True)
        
        # Server IP
        tk.Label(form_frame, text="Server IP:", font=('Segoe UI', 12), 
                fg='#ecf0f1', bg='#34495e').pack(pady=5)
        self.server_ip_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=20)
        self.server_ip_entry.pack(pady=5)
        self.server_ip_entry.insert(0, "localhost")
        
        # Username
        tk.Label(form_frame, text="Your Name:", font=('Segoe UI', 12), 
                fg='#ecf0f1', bg='#34495e').pack(pady=5)
        self.name_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=20)
        self.name_entry.pack(pady=5)
        self.name_entry.insert(0, f"User_{int(time.time()) % 1000}")
        
        # Connect button
        self.connect_btn = tk.Button(form_frame, text="🔗 Connect", 
                                   font=('Segoe UI', 12, 'bold'),
                                   bg='#27ae60', fg='white', 
                                   command=self.connect_to_server,
                                   width=15, height=2)
        self.connect_btn.pack(pady=20)
        
        # Status label
        self.status_label = tk.Label(form_frame, text="Ready to connect", 
                                   font=('Segoe UI', 10), 
                                   fg='#95a5a6', bg='#34495e')
        self.status_label.pack(pady=10)
        
        # Bind Enter key
        self.root.bind('<Return>', lambda e: self.connect_to_server())
    
    def connect_to_server(self):
        """Connect to server with clean error handling"""
        try:
            self.server_host = self.server_ip_entry.get().strip()
            self.client_name = self.name_entry.get().strip()
            
            if not self.server_host or not self.client_name:
                self.status_label.config(text="❌ Please fill in all fields", fg='#e74c3c')
                return
            
            self.status_label.config(text="🔄 Connecting...", fg='#f39c12')
            self.connect_btn.config(state=tk.DISABLED)
            self.root.update()
            
            # Create TCP connection
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(10)
            self.tcp_socket.connect((self.server_host, self.tcp_port))
            
            # Create UDP sockets
            self.udp_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Bind UDP sockets to receive data from server
            try:
                self.udp_video_socket.bind(('', self.udp_video_port))
                print(f"✅ UDP video socket bound to port {self.udp_video_port}")
            except Exception as e:
                print(f"❌ Failed to bind UDP video socket: {e}")
                
            try:
                self.udp_audio_socket.bind(('', self.udp_audio_port))
                print(f"✅ UDP audio socket bound to port {self.udp_audio_port}")
            except Exception as e:
                print(f"❌ Failed to bind UDP audio socket: {e}")
            
            self.connected = True
            print(f"✅ Connected to server at {self.server_host}:{self.tcp_port}")
            
            # Start network threads
            print("🔄 Starting network threads...")
            threading.Thread(target=self.tcp_receiver, daemon=True).start()
            threading.Thread(target=self.udp_video_receiver, daemon=True).start()
            threading.Thread(target=self.udp_audio_receiver, daemon=True).start()
            threading.Thread(target=self.heartbeat_loop, daemon=True).start()
            print("✅ All network threads started")
            
            # Send login message
            login_msg = create_login_message(self.client_name)
            print(f"🔄 Sending login message: {login_msg}")
            if self.send_tcp_message(login_msg):
                print("✅ Login message sent successfully")
            else:
                print("❌ Failed to send login message")
            
            # Show main interface
            self.show_main_interface()
            
            print(f"✅ Connected to {self.server_host}:{self.tcp_port}")
            
        except Exception as e:
            self.status_label.config(text=f"❌ Connection failed: {str(e)}", fg='#e74c3c')
            self.connect_btn.config(state=tk.NORMAL)
            print(f"❌ Connection error: {e}")
    
    def show_main_interface(self):
        """Show main communication interface"""
        # Clear root
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        main_container = tk.Frame(self.root, bg='#2c3e50')
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top panel - Controls
        self.create_control_panel(main_container)
        
        # Middle panel - Video and Chat
        middle_frame = tk.Frame(main_container, bg='#2c3e50')
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Left side - Video display
        self.create_video_panel(middle_frame)
        
        # Right side - Chat and participants
        self.create_chat_panel(middle_frame)
        
        # Start GUI update loop
        self.gui_update_loop()
    
    def create_control_panel(self, parent):
        """Create control panel with media buttons"""
        control_frame = tk.Frame(parent, bg='#34495e', relief=tk.RAISED, bd=1)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Left side - Media controls
        media_frame = tk.Frame(control_frame, bg='#34495e')
        media_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Video button
        self.video_btn = tk.Button(media_frame, text="📹\nVideo", 
                                 font=('Segoe UI', 10, 'bold'),
                                 bg='#404040', fg='white', 
                                 command=self.toggle_video,
                                 width=8, height=2)
        self.video_btn.pack(side=tk.LEFT, padx=5)
        
        # Audio button
        self.audio_btn = tk.Button(media_frame, text="🎤\nMic", 
                                 font=('Segoe UI', 10, 'bold'),
                                 bg='#404040', fg='white', 
                                 command=self.toggle_audio,
                                 width=8, height=2)
        self.audio_btn.pack(side=tk.LEFT, padx=5)
        
        # Speaker button
        self.speaker_btn = tk.Button(media_frame, text="🔊\nSpeaker", 
                                   font=('Segoe UI', 10, 'bold'),
                                   bg='#27ae60', fg='white', 
                                   command=self.toggle_speaker,
                                   width=8, height=2)
        self.speaker_btn.pack(side=tk.LEFT, padx=5)
        
        # Right side - Connection info
        info_frame = tk.Frame(control_frame, bg='#34495e')
        info_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Connection status
        self.conn_info_label = tk.Label(info_frame, 
                                      text=f"✅ Connected as {self.client_name}", 
                                      font=('Segoe UI', 10), 
                                      fg='#27ae60', bg='#34495e')
        self.conn_info_label.pack()
        
        # Disconnect button
        disconnect_btn = tk.Button(info_frame, text="🚪 Leave", 
                                 font=('Segoe UI', 10, 'bold'),
                                 bg='#e74c3c', fg='white', 
                                 command=self.disconnect,
                                 width=8, height=1)
        disconnect_btn.pack(pady=5)
    
    def create_video_panel(self, parent):
        """Create video display panel"""
        video_frame = tk.Frame(parent, bg='#34495e', relief=tk.RAISED, bd=1)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Video display label
        self.video_display = tk.Label(video_frame, 
                                    text="📹 Video Display\n\nNo video stream", 
                                    font=('Segoe UI', 14),
                                    fg='#95a5a6', bg='#2c3e50',
                                    width=40, height=20)
        self.video_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_chat_panel(self, parent):
        """Create chat and participants panel"""
        right_frame = tk.Frame(parent, bg='#2c3e50')
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Participants panel
        participants_frame = tk.Frame(right_frame, bg='#34495e', relief=tk.RAISED, bd=1)
        participants_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(participants_frame, text="👥 Participants", 
                font=('Segoe UI', 12, 'bold'), 
                fg='#ecf0f1', bg='#34495e').pack(pady=5)
        
        self.participants_listbox = tk.Listbox(participants_frame, 
                                             font=('Segoe UI', 10),
                                             bg='#2c3e50', fg='#ecf0f1',
                                             height=6, width=25)
        self.participants_listbox.pack(padx=10, pady=(0, 10))
        
        # Chat panel
        chat_frame = tk.Frame(right_frame, bg='#34495e', relief=tk.RAISED, bd=1)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(chat_frame, text="💬 Chat", 
                font=('Segoe UI', 12, 'bold'), 
                fg='#ecf0f1', bg='#34495e').pack(pady=5)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, 
                                                    font=('Segoe UI', 9),
                                                    bg='#2c3e50', fg='#ecf0f1',
                                                    height=15, width=30,
                                                    wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.pack(padx=10, pady=(0, 5))
        
        # Chat input
        chat_input_frame = tk.Frame(chat_frame, bg='#34495e')
        chat_input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.chat_entry = tk.Entry(chat_input_frame, font=('Segoe UI', 10))
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.chat_entry.bind('<Return>', self.send_chat_message)
        
        send_btn = tk.Button(chat_input_frame, text="📤", 
                           font=('Segoe UI', 10, 'bold'),
                           bg='#3498db', fg='white', 
                           command=self.send_chat_message,
                           width=3)
        send_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # File management button (like server's settings)
        file_mgmt_btn = tk.Button(chat_frame, text="📁 File Manager", 
                                font=('Segoe UI', 10, 'bold'),
                                bg='#9b59b6', fg='white', 
                                command=self.open_file_manager,
                                width=15, height=1)
        file_mgmt_btn.pack(pady=5)
    
    def send_tcp_message(self, message):
        """Send TCP message to server with improved error handling"""
        try:
            if not self.connected or not self.tcp_socket:
                print(f"❌ Cannot send message: connected={self.connected}, socket={self.tcp_socket is not None}")
                return False
            
            # Check if socket is still valid
            try:
                # Test socket with a non-blocking check
                self.tcp_socket.settimeout(0.1)
                ready = self.tcp_socket.recv(0, socket.MSG_PEEK)
            except socket.timeout:
                # Timeout is good, socket is alive
                pass
            except Exception as e:
                print(f"❌ Socket is dead: {e}")
                self.handle_disconnection()
                return False
            finally:
                self.tcp_socket.settimeout(None)  # Reset to blocking
            
            message_data = json.dumps(message).encode('utf-8')
            message_length = struct.pack('!I', len(message_data))
            
            # Send length + data (matching server protocol)
            full_message = message_length + message_data
            
            # Use sendall to ensure complete transmission
            self.tcp_socket.sendall(full_message)
            
            print(f"📤 Sent message: type={message.get('type')}, size={len(message_data)} bytes")
            return True
            
        except BrokenPipeError:
            print("❌ Broken pipe - server disconnected")
            self.handle_disconnection()
            return False
        except ConnectionResetError:
            print("❌ Connection reset by server")
            self.handle_disconnection()
            return False
        except Exception as e:
            print(f"❌ TCP send error: {e}")
            # Don't immediately disconnect on other errors, might be temporary
            return False
    
    def tcp_receiver(self):
        """Receive TCP messages from server with improved error handling"""
        consecutive_errors = 0
        max_errors = 3
        
        while self.running and self.connected:
            try:
                self.tcp_socket.settimeout(5.0)  # Longer timeout
                
                # Receive message length
                length_data = self.tcp_socket.recv(4)
                if not length_data:
                    print("❌ Server closed connection")
                    break
                
                message_length = struct.unpack('!I', length_data)[0]
                
                # Validate message length
                if message_length > 1024 * 1024:  # 1MB max
                    print(f"❌ Invalid message length: {message_length}")
                    break
                
                # Receive message data
                message_data = b''
                while len(message_data) < message_length:
                    remaining = message_length - len(message_data)
                    chunk = self.tcp_socket.recv(min(4096, remaining))
                    if not chunk:
                        print("❌ Connection lost while receiving message")
                        break
                    message_data += chunk
                
                if len(message_data) == message_length:
                    try:
                        message = json.loads(message_data.decode('utf-8'))
                        print(f"📥 Received message: type={message.get('type')}, size={len(message_data)} bytes")
                        self.root.after_idle(lambda msg=message: self.process_message(msg))
                        consecutive_errors = 0  # Reset error count on success
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        consecutive_errors += 1
                else:
                    print(f"❌ Incomplete message: {len(message_data)}/{message_length}")
                    break
                
            except socket.timeout:
                # Timeout is normal, just continue
                continue
            except ConnectionResetError:
                print("❌ Connection reset by server")
                break
            except Exception as e:
                consecutive_errors += 1
                if self.running:
                    print(f"❌ TCP receive error ({consecutive_errors}/{max_errors}): {e}")
                
                if consecutive_errors >= max_errors:
                    print("❌ Too many consecutive errors, disconnecting")
                    break
                    
                time.sleep(1)  # Brief pause before retry
        
        if self.connected:
            print("🔄 TCP receiver stopped, handling disconnection")
            self.root.after(0, self.handle_disconnection)
    
    def process_message(self, message):
        """Process received message"""
        msg_type = message.get('type')
        
        if msg_type == MessageTypes.LOGIN_SUCCESS:
            self.client_id = message.get('client_id')
            self.participants = message.get('clients', {})
            self.chat_history = message.get('chat_history', [])
            server_shared_files = message.get('shared_files', {})
            
            if self.client_id:
                print(f"✅ Login successful! Client ID: {self.client_id}")
                print(f"📋 Participants: {list(self.participants.keys())}")
                
                # Update shared files from server
                if server_shared_files:
                    self.shared_files.update(server_shared_files)
                    print(f"📁 Received {len(server_shared_files)} shared files from server")
                    # Refresh file manager if open
                    if hasattr(self, 'files_tree'):
                        self.refresh_files_list()
                
                # Update connection status in GUI
                if hasattr(self, 'conn_info_label'):
                    self.conn_info_label.config(text=f"✅ Connected as {self.client_name} (ID: {self.client_id})")
                
                self.update_participants_display()
                self.update_chat_display()
            else:
                print("❌ Login failed - no client ID received")
                self.handle_disconnection()
            
        elif msg_type == MessageTypes.USER_JOINED:
            client_id = message.get('client_id')
            name = message.get('name')
            if client_id and name:
                self.participants[str(client_id)] = {'name': name}
                self.update_participants_display()
                self.add_chat_message("System", f"{name} joined")
                
        elif msg_type == MessageTypes.USER_LEFT:
            client_id = str(message.get('client_id', ''))
            name = message.get('name', 'Unknown')
            if client_id in self.participants:
                del self.participants[client_id]
            self.update_participants_display()
            self.add_chat_message("System", f"{name} left")
            
        elif msg_type == MessageTypes.CHAT:
            sender = message.get('name', 'Unknown')
            text = message.get('message', '')
            if sender and text:
                self.add_chat_message(sender, text)
            
        elif msg_type == MessageTypes.PRESENT_START_BROADCAST:
            presenter_name = message.get('username', 'Unknown')
            self.add_chat_message("System", f"🎬 {presenter_name} started presentation")
            
        elif msg_type == MessageTypes.PRESENT_STOP_BROADCAST:
            presenter_name = message.get('username', 'Unknown')
            self.add_chat_message("System", f"{presenter_name} stopped presentation")
            
        elif msg_type == MessageTypes.FILE_AVAILABLE:
            fid = message.get('fid')
            filename = message.get('filename')
            uploader = message.get('uploader', 'Unknown')
            size = message.get('size', 0)
            
            if fid and filename:
                self.shared_files[fid] = {
                    'filename': filename,
                    'uploader': uploader,
                    'size': size
                }
                # Refresh file manager if open
                if hasattr(self, 'files_tree'):
                    self.refresh_files_list()
                self.add_chat_message("System", f"📁 {uploader} shared: {filename}")
                
        elif msg_type == MessageTypes.FILE_UPLOAD_PORT:
            port = message.get('port')
            if port and hasattr(self, 'pending_upload'):
                threading.Thread(target=self.upload_file_to_server, args=(port,), daemon=True).start()
                
        elif msg_type == MessageTypes.FILE_DOWNLOAD_PORT:
            port = message.get('port')
            if port and hasattr(self, 'pending_download'):
                threading.Thread(target=self.download_file_from_server, args=(port,), daemon=True).start()
                
        elif msg_type == 'files_list_update':
            # Server sent updated files list
            server_shared_files = message.get('shared_files', {})
            if server_shared_files:
                self.shared_files.update(server_shared_files)
                print(f"📁 Updated files list: {len(server_shared_files)} files from server")
                # Refresh file manager if open
                if hasattr(self, 'files_tree'):
                    self.refresh_files_list()
    
    def udp_video_receiver(self):
        """Receive UDP video streams"""
        while self.running and self.connected:
            try:
                self.udp_video_socket.settimeout(1.0)
                data, address = self.udp_video_socket.recvfrom(65536)
                
                if len(data) >= 12:
                    client_id, sequence, frame_size = struct.unpack('!III', data[:12])
                    frame_data = data[12:]
                    
                    if len(frame_data) == frame_size:
                        try:
                            nparr = np.frombuffer(frame_data, np.uint8)
                            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            
                            if frame is not None:
                                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                try:
                                    self.video_frame_queue.put_nowait(frame_rgb)
                                except queue.Full:
                                    try:
                                        self.video_frame_queue.get_nowait()
                                        self.video_frame_queue.put_nowait(frame_rgb)
                                    except queue.Empty:
                                        pass
                        except Exception as e:
                            print(f"Video decode error: {e}")
                            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"❌ UDP video error: {e}")
                break
    
    def udp_audio_receiver(self):
        """Receive UDP audio streams"""
        while self.running and self.connected:
            try:
                self.udp_audio_socket.settimeout(1.0)
                data, address = self.udp_audio_socket.recvfrom(4096)
                
                if len(data) >= 8 and self.speaker_enabled:
                    client_id, timestamp = struct.unpack('!II', data[:8])
                    audio_data = data[8:]
                    
                    if len(audio_data) > 0 and hasattr(self, 'audio_output_stream'):
                        try:
                            if self.audio_output_stream and self.audio_output_stream.is_active():
                                self.audio_output_stream.write(audio_data)
                        except Exception as e:
                            print(f"Audio playback error: {e}")
                            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"❌ UDP audio error: {e}")
                break
    
    def heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        while self.running and self.connected:
            try:
                heartbeat_msg = create_heartbeat_message()
                self.send_tcp_message(heartbeat_msg)
                
                # Sleep in small intervals for responsiveness
                for _ in range(HEARTBEAT_INTERVAL * 10):
                    if not self.running or not self.connected:
                        break
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
                break
    
    def toggle_video(self):
        """Toggle video capture"""
        if not self.video_enabled:
            self.start_video()
        else:
            self.stop_video()
    
    def start_video(self):
        """Start video capture"""
        try:
            self.video_cap = cv2.VideoCapture(0)
            if self.video_cap.isOpened():
                self.video_enabled = True
                self.video_btn.config(bg='#27ae60', text="📹\nVideo ON")
                threading.Thread(target=self.video_capture_loop, daemon=True).start()
                self.send_media_status_update()
                print("✅ Video started")
            else:
                messagebox.showerror("Video Error", "Could not access camera")
        except Exception as e:
            messagebox.showerror("Video Error", f"Failed to start video: {e}")
    
    def stop_video(self):
        """Stop video capture"""
        self.video_enabled = False
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
        self.video_btn.config(bg='#404040', text="📹\nVideo")
        self.send_media_status_update()
        print("✅ Video stopped")
    
    def video_capture_loop(self):
        """Video capture and transmission loop"""
        while self.video_enabled and self.video_cap:
            try:
                ret, frame = self.video_cap.read()
                if ret:
                    # Resize frame for efficiency
                    frame = cv2.resize(frame, (640, 480))
                    
                    # Encode frame
                    _, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    frame_data = encoded.tobytes()
                    
                    # Send via UDP to server (only if properly logged in)
                    if self.udp_video_socket and self.connected and self.client_id:
                        try:
                            header = struct.pack('!III', self.client_id, int(time.time()), len(frame_data))
                            # Send to server's UDP video port, not our own port
                            server_address = (self.server_host, self.udp_video_port)
                            bytes_sent = self.udp_video_socket.sendto(header + frame_data, server_address)
                            
                            # Log occasionally
                            if hasattr(self, 'video_frame_count'):
                                self.video_frame_count += 1
                            else:
                                self.video_frame_count = 1
                                
                            if self.video_frame_count % 50 == 0:  # Every 50 frames (less spam)
                                print(f"📹 Sent video frame {self.video_frame_count}: {len(frame_data)} bytes")
                        except Exception as e:
                            print(f"❌ Video send error: {e}")
                    elif not self.client_id and self.video_enabled:
                        # Only show this error once per second to avoid spam
                        if not hasattr(self, 'last_video_error') or time.time() - self.last_video_error > 1.0:
                            print("⏳ Waiting for login to complete before sending video...")
                            self.last_video_error = time.time()
                
                time.sleep(0.05)  # 20 FPS
                
            except Exception as e:
                print(f"❌ Video capture error: {e}")
                break
    
    def toggle_audio(self):
        """Toggle audio capture"""
        if not self.audio_enabled:
            self.start_audio()
        else:
            self.stop_audio()
    
    def start_audio(self):
        """Start audio capture"""
        try:
            import pyaudio
            
            self.audio = pyaudio.PyAudio()
            self.audio_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                frames_per_buffer=1024
            )
            
            self.audio_enabled = True
            self.audio_btn.config(bg='#27ae60', text="🎤\nMic ON")
            threading.Thread(target=self.audio_capture_loop, daemon=True).start()
            self.send_media_status_update()
            print("✅ Audio started")
            
        except Exception as e:
            messagebox.showerror("Audio Error", f"Failed to start audio: {e}")
    
    def stop_audio(self):
        """Stop audio capture"""
        self.audio_enabled = False
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        if hasattr(self, 'audio'):
            self.audio.terminate()
        self.audio_btn.config(bg='#404040', text="🎤\nMic")
        self.send_media_status_update()
        print("✅ Audio stopped")
    
    def audio_capture_loop(self):
        """Audio capture and transmission loop"""
        while self.audio_enabled and self.audio_stream:
            try:
                audio_data = self.audio_stream.read(1024, exception_on_overflow=False)
                
                if self.udp_audio_socket and self.connected and self.client_id:
                    try:
                        header = struct.pack('!II', self.client_id, int(time.time()))
                        # Send to server's UDP audio port
                        server_address = (self.server_host, self.udp_audio_port)
                        bytes_sent = self.udp_audio_socket.sendto(header + audio_data, server_address)
                        
                        # Log occasionally
                        if hasattr(self, 'audio_frame_count'):
                            self.audio_frame_count += 1
                        else:
                            self.audio_frame_count = 1
                            
                        if self.audio_frame_count % 200 == 0:  # Every 200 frames (less spam)
                            print(f"🎤 Sent audio frame {self.audio_frame_count}: {len(audio_data)} bytes")
                    except Exception as e:
                        print(f"❌ Audio send error: {e}")
                elif not self.client_id and self.audio_enabled:
                    # Only show this error once per second to avoid spam
                    if not hasattr(self, 'last_audio_error') or time.time() - self.last_audio_error > 1.0:
                        print("⏳ Waiting for login to complete before sending audio...")
                        self.last_audio_error = time.time()
                        
            except Exception as e:
                print(f"❌ Audio capture error: {e}")
                break
    
    def toggle_speaker(self):
        """Toggle speaker output"""
        if self.speaker_enabled:
            self.stop_speaker()
        else:
            self.start_speaker()
    
    def start_speaker(self):
        """Start audio output"""
        try:
            import pyaudio
            
            if not hasattr(self, 'audio'):
                self.audio = pyaudio.PyAudio()
            
            self.audio_output_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True,
                frames_per_buffer=1024
            )
            
            self.speaker_enabled = True
            self.speaker_btn.config(bg='#27ae60', text="🔊\nSpeaker ON")
            print("✅ Speaker started")
            
        except Exception as e:
            print(f"❌ Speaker error: {e}")
    
    def stop_speaker(self):
        """Stop audio output"""
        self.speaker_enabled = False
        if hasattr(self, 'audio_output_stream') and self.audio_output_stream:
            self.audio_output_stream.stop_stream()
            self.audio_output_stream.close()
            self.audio_output_stream = None
        self.speaker_btn.config(bg='#404040', text="🔊\nSpeaker")
        print("✅ Speaker stopped")
    
    def send_media_status_update(self):
        """Send media status update to server"""
        status_msg = create_media_status_update(self.video_enabled, self.audio_enabled)
        self.send_tcp_message(status_msg)
    
    def send_chat_message(self, event=None):
        """Send chat message"""
        text = self.chat_entry.get().strip()
        if text and self.connected:
            chat_msg = create_chat_message(text)
            if self.send_tcp_message(chat_msg):
                self.chat_entry.delete(0, tk.END)
    
    def add_chat_message(self, sender, message):
        """Add message to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def update_participants_display(self):
        """Update participants list"""
        self.participants_listbox.delete(0, tk.END)
        for client_id, info in self.participants.items():
            name = info.get('name', f'User_{client_id}')
            self.participants_listbox.insert(tk.END, name)
    
    def update_chat_display(self):
        """Update chat display with history"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        
        for msg in self.chat_history:
            sender = msg.get('name', 'Unknown')
            text = msg.get('message', '')
            timestamp = msg.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(timestamp)
                    time_str = dt.strftime("%H:%M")
                except:
                    time_str = "??:??"
            else:
                time_str = "??:??"
            
            self.chat_display.insert(tk.END, f"[{time_str}] {sender}: {text}\n")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def open_file_manager(self):
        """Open file management window (like server settings)"""
        if hasattr(self, 'file_manager_window') and self.file_manager_window.winfo_exists():
            self.file_manager_window.lift()
            return
            
        # Create file manager window
        self.file_manager_window = tk.Toplevel(self.root)
        self.file_manager_window.title("📁 File Manager")
        self.file_manager_window.geometry("800x600")
        self.file_manager_window.configure(bg='#2c3e50')
        
        # Make it modal-like
        self.file_manager_window.transient(self.root)
        self.file_manager_window.grab_set()
        
        # Main container
        main_frame = tk.Frame(self.file_manager_window, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="📁 File Management Center", 
                              font=('Segoe UI', 16, 'bold'), 
                              fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Upload tab
        upload_frame = tk.Frame(notebook, bg='#34495e')
        notebook.add(upload_frame, text="📤 Upload Files")
        self.create_upload_tab(upload_frame)
        
        # Download tab
        download_frame = tk.Frame(notebook, bg='#34495e')
        notebook.add(download_frame, text="📥 Download Files")
        self.create_download_tab(download_frame)
        
        # Close button
        close_btn = tk.Button(main_frame, text="✖ Close", 
                            font=('Segoe UI', 12, 'bold'),
                            bg='#e74c3c', fg='white', 
                            command=self.file_manager_window.destroy,
                            width=10, height=1)
        close_btn.pack(pady=10)
    
    def create_upload_tab(self, parent):
        """Create upload files tab"""
        # Upload section
        upload_section = tk.LabelFrame(parent, text="📤 Share Files", 
                                     font=('Segoe UI', 12, 'bold'),
                                     fg='#ecf0f1', bg='#34495e')
        upload_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Instructions
        instructions = tk.Label(upload_section, 
                              text="Select files to share with other participants.\nMax file size: 100MB per file.", 
                              font=('Segoe UI', 10), 
                              fg='#bdc3c7', bg='#34495e')
        instructions.pack(pady=10)
        
        # Upload button
        upload_btn = tk.Button(upload_section, text="📁 Select Files to Share", 
                             font=('Segoe UI', 12, 'bold'),
                             bg='#27ae60', fg='white', 
                             command=self.share_file,
                             width=20, height=2)
        upload_btn.pack(pady=10)
        
        # Upload status
        self.upload_status_label = tk.Label(upload_section, text="Ready to share files", 
                                          font=('Segoe UI', 10), 
                                          fg='#95a5a6', bg='#34495e')
        self.upload_status_label.pack(pady=5)
        
        # Upload progress
        self.upload_progress = ttk.Progressbar(upload_section, mode='determinate', maximum=100)
        self.upload_progress.pack(fill=tk.X, padx=20, pady=5)
    
    def create_download_tab(self, parent):
        """Create download files tab"""
        # Download section
        download_section = tk.LabelFrame(parent, text="📥 Available Files", 
                                       font=('Segoe UI', 12, 'bold'),
                                       fg='#ecf0f1', bg='#34495e')
        download_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Instructions
        instructions = tk.Label(download_section, 
                              text="Select a file from the list below to download it to your computer.", 
                              font=('Segoe UI', 10), 
                              fg='#bdc3c7', bg='#34495e')
        instructions.pack(pady=10)
        
        # Files list frame
        list_frame = tk.Frame(download_section, bg='#34495e')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Files treeview (like server's detailed view)
        columns = ('Filename', 'Size', 'Shared By', 'Date')
        self.files_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        self.files_tree.heading('Filename', text='📄 Filename')
        self.files_tree.heading('Size', text='📏 Size')
        self.files_tree.heading('Shared By', text='👤 Shared By')
        self.files_tree.heading('Date', text='📅 Date')
        
        self.files_tree.column('Filename', width=300)
        self.files_tree.column('Size', width=100)
        self.files_tree.column('Shared By', width=150)
        self.files_tree.column('Date', width=150)
        
        # Scrollbar for files list
        files_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Download controls
        controls_frame = tk.Frame(download_section, bg='#34495e')
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Refresh button
        refresh_btn = tk.Button(controls_frame, text="🔄 Refresh List", 
                              font=('Segoe UI', 10),
                              bg='#3498db', fg='white', 
                              command=self.refresh_files_list,
                              width=12)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Download button
        download_btn = tk.Button(controls_frame, text="📥 Download Selected", 
                               font=('Segoe UI', 10, 'bold'),
                               bg='#27ae60', fg='white', 
                               command=self.download_selected_file,
                               width=15)
        download_btn.pack(side=tk.LEFT)
        
        # Download status
        self.download_status_label = tk.Label(download_section, text="Select a file to download", 
                                            font=('Segoe UI', 10), 
                                            fg='#95a5a6', bg='#34495e')
        self.download_status_label.pack(pady=5)
        
        # Download progress
        self.download_progress = ttk.Progressbar(download_section, mode='determinate', maximum=100)
        self.download_progress.pack(fill=tk.X, padx=20, pady=5)
        
        # Initial files list update
        self.refresh_files_list()
    
    def refresh_files_list(self):
        """Refresh the files list in the download tab"""
        if not hasattr(self, 'files_tree'):
            return
        
        # Request updated file list from server
        if self.connected:
            refresh_msg = {
                'type': 'get_files_list',
                'timestamp': time.time()
            }
            self.send_tcp_message(refresh_msg)
            print("📡 Requested file list refresh from server")
            
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # Add files from shared_files
        print(f"📁 Refreshing file list: {len(self.shared_files)} files available")
        for fid, file_info in self.shared_files.items():
            filename = file_info.get('filename', 'Unknown')
            size = self.format_file_size(file_info.get('size', 0))
            uploader = file_info.get('uploader', 'Unknown')
            # Use current time as placeholder for date
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            print(f"📄 File: {filename} ({size}) by {uploader}")
            self.files_tree.insert('', 'end', values=(filename, size, uploader, date))
        
        # Update status
        file_count = len(self.shared_files)
        if hasattr(self, 'download_status_label'):
            if file_count == 0:
                self.download_status_label.config(text="No files available for download - Click Refresh")
            else:
                self.download_status_label.config(text=f"{file_count} file(s) available for download")
    
    def download_selected_file(self):
        """Download the selected file from the treeview"""
        if not hasattr(self, 'files_tree'):
            return
            
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to download")
            return
        
        # Get selected item
        item = self.files_tree.item(selection[0])
        filename = item['values'][0]
        
        # Find the file in shared_files
        selected_fid = None
        for fid, file_info in self.shared_files.items():
            if file_info.get('filename') == filename:
                selected_fid = fid
                break
        
        if not selected_fid:
            messagebox.showerror("Error", "Selected file not found")
            return
        
        # Use the existing download_file logic
        file_info = self.shared_files[selected_fid]
        
        # Choose save location
        save_path = filedialog.asksaveasfilename(
            title="Save file as",
            initialname=filename,
            filetypes=[("All files", "*.*")]
        )
        
        if not save_path:
            return
        
        # Store pending download
        self.pending_download = {
            'fid': selected_fid,
            'save_path': save_path,
            'filename': filename,
            'size': file_info['size']
        }
        
        # Send download request
        request_msg = {
            'type': MessageTypes.FILE_REQUEST,
            'fid': selected_fid,
            'timestamp': time.time()
        }
        
        if self.send_tcp_message(request_msg):
            if hasattr(self, 'download_status_label'):
                self.download_status_label.config(text=f"📥 Downloading: {filename}")
            print(f"📥 Download request sent: {filename}")
        else:
            messagebox.showerror("Download Error", "Failed to send download request")
    
    def share_file(self):
        """Share a file with other participants"""
        try:
            file_path = filedialog.askopenfilename(
                title="Select file to share",
                filetypes=[("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            # Validate file
            if not os.path.exists(file_path):
                messagebox.showerror("File Error", "Selected file does not exist.")
                return
                
            file_size = os.path.getsize(file_path)
            max_size = 100 * 1024 * 1024  # 100MB
            if file_size > max_size:
                messagebox.showerror("File Too Large", 
                                   f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes).")
                return
                
            if file_size == 0:
                messagebox.showerror("File Error", "Cannot share empty file.")
                return
                
            # Generate unique file ID
            fid = str(uuid.uuid4())
            filename = os.path.basename(file_path)
            
            # Store pending upload
            self.pending_upload = {
                'fid': fid,
                'path': file_path,
                'filename': filename,
                'size': file_size
            }
            
            # Send file offer
            offer_msg = {
                'type': MessageTypes.FILE_OFFER,
                'fid': fid,
                'filename': filename,
                'size': file_size,
                'timestamp': time.time()
            }
            
            if self.send_tcp_message(offer_msg):
                # Don't show chat message during upload - only update status
                if hasattr(self, 'upload_status_label'):
                    self.upload_status_label.config(text=f"📤 Preparing: {filename}")
                print(f"📤 File offer sent: {filename}")
            else:
                messagebox.showerror("Upload Error", "Failed to send file offer")
                if hasattr(self, 'upload_status_label'):
                    self.upload_status_label.config(text="❌ Upload failed")
                
        except Exception as e:
            messagebox.showerror("File Share Error", f"Failed to share file: {str(e)}")
    

    
    def upload_file_to_server(self, port):
        """Upload file to server on specified port"""
        try:
            if not hasattr(self, 'pending_upload'):
                return
                
            upload_info = self.pending_upload
            file_path = upload_info['path']
            filename = upload_info['filename']
            file_size = upload_info['size']
            
            # Connect to upload port
            upload_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            upload_socket.settimeout(30)
            upload_socket.connect((self.server_host, port))
            
            print(f"📤 Starting upload: {filename} ({file_size} bytes) to port {port}")
            
            # CN_project optimized file upload
            bytes_sent = 0
            chunk_size = 65536  # 64KB chunks for optimal performance
            
            # Set socket buffer for better performance
            upload_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)  # 1MB buffer
            
            with open(file_path, 'rb') as f:
                while bytes_sent < file_size:
                    remaining = file_size - bytes_sent
                    read_size = min(chunk_size, remaining)
                    data = f.read(read_size)
                    
                    if not data:
                        break
                    
                    # Use sendall to ensure complete transmission
                    upload_socket.sendall(data)
                    bytes_sent += len(data)
                    
                    # Update progress less frequently for better performance
                    progress = (bytes_sent / file_size) * 100
                    
                    # Update GUI every 512KB for better performance
                    if bytes_sent % (512 * 1024) == 0 or bytes_sent == file_size:
                        if hasattr(self, 'upload_progress'):
                            self.root.after_idle(lambda p=progress: self.upload_progress.config(value=p))
                        
                        # Only log major milestones (every 2MB)
                        if bytes_sent % (2 * 1024 * 1024) == 0 or bytes_sent == file_size:
                            print(f"📤 Upload: {progress:.1f}% ({bytes_sent}/{file_size} bytes)")
                            if hasattr(self, 'upload_status_label'):
                                self.root.after_idle(lambda p=progress: self.upload_status_label.config(
                                    text=f"📤 Uploading: {progress:.1f}% complete"))
            
            upload_socket.close()
            
            # Clean up
            del self.pending_upload
            
            # Don't show chat message - only update status
            if hasattr(self, 'upload_status_label'):
                self.root.after(0, lambda: self.upload_status_label.config(text="✅ Upload complete"))
            print(f"✅ File uploaded successfully: {filename}")
            
        except Exception as e:
            # Don't show chat message - only update status
            if hasattr(self, 'upload_status_label'):
                self.root.after(0, lambda: self.upload_status_label.config(text=f"❌ Upload failed: {str(e)}"))
            print(f"❌ Upload error: {e}")
    
    def download_file_from_server(self, port):
        """Download file from server on specified port"""
        try:
            if not hasattr(self, 'pending_download'):
                return
                
            download_info = self.pending_download
            save_path = download_info['save_path']
            filename = download_info['filename']
            file_size = download_info['size']
            
            print(f"📥 Starting download: {filename} ({file_size} bytes) from port {port}")
            
            # Connect to download port
            download_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            download_socket.settimeout(30)
            download_socket.connect((self.server_host, port))
            
            # Receive file with progress tracking
            bytes_received = 0
            chunk_size = 32768  # 32KB chunks for better performance
            
            with open(save_path, 'wb') as f:
                while bytes_received < file_size:
                    remaining = file_size - bytes_received
                    recv_size = min(chunk_size, remaining)
                    data = download_socket.recv(recv_size)
                    
                    if not data:
                        print("❌ Connection closed by server during download")
                        break
                        
                    f.write(data)
                    bytes_received += len(data)
                    
                    # Update progress
                    progress = (bytes_received / file_size) * 100
                    
                    # Update progress bar in GUI
                    if hasattr(self, 'download_progress'):
                        self.root.after_idle(lambda p=progress: self.download_progress.config(value=p))
                    
                    # Log progress every 256KB
                    if bytes_received % (256 * 1024) == 0 or bytes_received == file_size:
                        print(f"📥 Download progress: {progress:.1f}% ({bytes_received}/{file_size} bytes)")
                        if hasattr(self, 'download_status_label'):
                            self.root.after_idle(lambda p=progress: self.download_status_label.config(
                                text=f"📥 Downloading: {progress:.1f}% complete"))
            
            download_socket.close()
            
            # Clean up
            del self.pending_download
            
            # Don't show chat message - only update status
            if hasattr(self, 'download_status_label'):
                self.root.after(0, lambda: self.download_status_label.config(text="✅ Download complete"))
            print(f"✅ File downloaded successfully: {filename}")
            
        except Exception as e:
            self.root.after(0, lambda: self.add_chat_message("System", f"❌ Download failed: {str(e)}"))
            if hasattr(self, 'download_status_label'):
                self.root.after(0, lambda: self.download_status_label.config(text=f"❌ Download failed: {str(e)}"))
            print(f"❌ Download error: {e}")
    

    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def gui_update_loop(self):
        """GUI update loop for video frames"""
        try:
            # Update video display
            try:
                frame = self.video_frame_queue.get_nowait()
                
                # Convert to PhotoImage
                frame_pil = Image.fromarray(frame)
                frame_pil = frame_pil.resize((400, 300), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(frame_pil)
                
                self.video_display.config(image=photo, text="")
                self.video_display.image = photo
                
            except queue.Empty:
                pass
            
            # Schedule next update
            if self.running:
                self.root.after(50, self.gui_update_loop)  # 20 FPS
                
        except Exception as e:
            print(f"GUI update error: {e}")
            if self.running:
                self.root.after(100, self.gui_update_loop)
    
    def handle_disconnection(self):
        """Handle disconnection"""
        self.connected = False
        messagebox.showwarning("Connection Lost", "Connection to server lost")
        self.disconnect()
    
    def disconnect(self):
        """Disconnect from server"""
        print("🔄 Disconnecting...")
        
        # Send logout message
        if self.connected:
            try:
                logout_msg = create_logout_message()
                self.send_tcp_message(logout_msg)
                time.sleep(0.5)
            except:
                pass
        
        # Stop media
        if self.video_enabled:
            self.stop_video()
        if self.audio_enabled:
            self.stop_audio()
        if self.speaker_enabled:
            self.stop_speaker()
        
        # Close sockets
        self.connected = False
        self.running = False
        
        try:
            if self.tcp_socket:
                self.tcp_socket.close()
            if self.udp_video_socket:
                self.udp_video_socket.close()
            if self.udp_audio_socket:
                self.udp_audio_socket.close()
        except:
            pass
        
        # Return to connection screen
        self.show_connection_screen(self.root)
        
        print("✅ Disconnected")
    
    def run(self):
        """Run the client application"""
        try:
            # Auto-start speaker
            self.root.after(1000, self.start_speaker)
            
            # Handle window close
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Start GUI
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("\n🔄 Shutting down...")
        finally:
            self.cleanup()
    
    def on_closing(self):
        """Handle window closing"""
        if self.connected:
            self.disconnect()
        self.cleanup()
        self.root.destroy()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        self.connected = False
        
        # Stop media
        if self.video_enabled:
            self.stop_video()
        if self.audio_enabled:
            self.stop_audio()
        if self.speaker_enabled:
            self.stop_speaker()
        
        # Close sockets
        try:
            if self.tcp_socket:
                self.tcp_socket.close()
            if self.udp_video_socket:
                self.udp_video_socket.close()
            if self.udp_audio_socket:
                self.udp_audio_socket.close()
        except:
            pass
        
        print("✅ Cleanup complete")

def main():
    """Main entry point"""
    print("🚀 Starting LAN Communication Client...")
    
    try:
        client = LANCommunicationClient()
        client.run()
    except Exception as e:
        print(f"❌ Client error: {e}")
    finally:
        print("👋 Client shutdown complete")

if __name__ == "__main__":
    main()