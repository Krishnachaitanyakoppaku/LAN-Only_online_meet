#!/usr/bin/env python3
"""
LAN Communication Client - Enhanced Modern Interface
A comprehensive multi-user communication client for LAN environments

Features:
- Multi-user video conferencing (UDP)
- Multi-user audio conferencing (UDP) 
- Screen/slide sharing (TCP)
- Group text chat (TCP)
- File sharing (TCP)
- Modern UI/UX Design
- Permission Management
- Enhanced protocol handling
- Improved error recovery
- Better resource management
"""

import socket
import threading
import json
import time
import struct
import os
import cv2
import pyaudio
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from PIL import Image, ImageTk
import io
import base64
import queue
import hashlib
import uuid
import asyncio

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
    GET_HISTORY = 'get_history'
    FILE_OFFER = 'file_offer'
    FILE_REQUEST = 'file_request'
    PRESENT_START = 'present_start'
    PRESENT_STOP = 'present_stop'
    LOGOUT = 'logout'
    MEDIA_STATUS_UPDATE = 'media_status_update'
    PERMISSION_REQUEST = 'permission_request'
    
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
    HOST_STATUS_UPDATE = 'host_status_update'
    FORCE_MUTE = 'force_mute'
    FORCE_DISABLE_VIDEO = 'force_disable_video'
    FORCE_STOP_PRESENTING = 'force_stop_presenting'
    HOST_REQUEST = 'host_request'
    PERMISSION_GRANTED = 'permission_granted'
    PERMISSION_DENIED = 'permission_denied'

# Network Configuration
DEFAULT_TCP_PORT = 8888
DEFAULT_UDP_VIDEO_PORT = 8889
DEFAULT_UDP_AUDIO_PORT = 8890
CHUNK_SIZE = 8192
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
HEARTBEAT_INTERVAL = 10  # seconds
MAX_RETRY_ATTEMPTS = 3

# Protocol helper functions (matching server)
def create_login_message(username: str) -> dict:
    """Create a login message."""
    return {
        "type": MessageTypes.LOGIN,
        "username": username,
        "timestamp": datetime.now().isoformat()
    }

def create_heartbeat_message() -> dict:
    """Create a heartbeat message."""
    return {
        "type": MessageTypes.HEARTBEAT,
        "timestamp": datetime.now().isoformat()
    }

def create_chat_message(text: str) -> dict:
    """Create a chat message."""
    return {
        "type": MessageTypes.CHAT,
        "text": text,
        "timestamp": datetime.now().isoformat()
    }

def create_media_status_update(video_enabled: bool, audio_enabled: bool, screen_share_enabled: bool = False) -> dict:
    """Create a media status update message."""
    return {
        "type": MessageTypes.MEDIA_STATUS_UPDATE,
        "video_enabled": video_enabled,
        "audio_enabled": audio_enabled,
        "screen_share_enabled": screen_share_enabled,
        "timestamp": datetime.now().isoformat()
    }

def create_permission_request(request_type: str) -> dict:
    """Create a permission request message."""
    return {
        "type": MessageTypes.PERMISSION_REQUEST,
        "request_type": request_type,
        "timestamp": datetime.now().isoformat()
    }

def create_logout_message() -> dict:
    """Create a logout message."""
    return {
        "type": MessageTypes.LOGOUT,
        "timestamp": datetime.now().isoformat()
    }

class LANCommunicationClient:
    def __init__(self):
        # Network configuration
        self.server_host = ""
        self.tcp_port = 8888
        self.udp_video_port = 8889
        self.udp_audio_port = 8890
        
        # Video settings (adaptive sizing like CN_project)
        self.video_settings = {
            'default_width': 640,
            'default_height': 360,
            'max_width': 1280,
            'max_height': 720,
            'min_width': 320,
            'min_height': 240,
            'quality': 80,  # JPEG quality
            'fps': 15
        }
        
        # File transfer settings
        self.file_transfer = {
            'download_dir': 'downloads',
            'max_file_size': MAX_FILE_SIZE,
            'chunk_size': CHUNK_SIZE,
            'pending_uploads': {},  # {fid: file_path}
            'pending_downloads': {}  # {fid: save_path}
        }
        
        # Create download directory
        os.makedirs(self.file_transfer['download_dir'], exist_ok=True)
        
        # Client state
        self.connected = False
        self.client_id = None
        self.client_name = ""
        self.is_presenter = False
        
        # UI state tracking to prevent flickering
        self.current_display_mode = None  # 'screen_sharing', 'video', 'none'
        self.current_video_source = None  # client_id of current video source
        self.last_header_text = ""
        
        # Sockets
        self.tcp_socket = None
        self.udp_video_socket = None
        self.udp_audio_socket = None
        
        # Media devices
        self.video_cap = None
        self.audio_stream = None
        self.audio_output_stream = None
        self.audio = None
        
        # Media state
        self.video_enabled = False
        self.audio_enabled = False  # Keep for compatibility
        self.microphone_enabled = False
        self.speaker_enabled = True  # Speaker on by default
        self.screen_sharing = False
        
        # Session data
        self.clients_list = {}
        self.chat_history = []
        self.presenter_id = None
        self.host_id = 0  # Server/Host ID
        self.shared_files = {}  # {filename: file_info}
        
        # Threading and queues
        self.running = False
        self.video_frame_queue = queue.Queue(maxsize=2)
        self.screen_frame_queue = queue.Queue(maxsize=2)
        
        # Video display management
        self.current_photo = None
        self.video_displays = {}  # {client_id: video_label}
        
        # Permission management
        self.pending_requests = {}
        
        # GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Initialize the modern client GUI"""
        self.root = tk.Tk()
        self.root.title("LAN Meeting Client")
        self.root.geometry("1600x1000")
        self.root.minsize(1400, 900)
        self.root.configure(bg='#1e1e1e')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure modern style
        self.setup_modern_style()
        
        # Main container
        self.main_container = tk.Frame(self.root, bg='#1e1e1e')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Show connection screen initially
        self.show_connection_screen()
        
        # Video display timer will be started when meeting screen is shown
        
    def start_video_display_timer(self):
        """Start the video display update timer"""
        self.update_video_display_from_queue()
        
    def update_video_display_from_queue(self):
        """Update video display from queue in main thread - STABLE VERSION"""
        try:
            # Safety check - ensure GUI still exists and we're connected
            if not hasattr(self, 'root') or not self.root or not self.connected:
                return
                
            # Track current state to prevent unnecessary UI updates
            screen_frame_available = False
            current_video_client = None
            
            # Check for screen sharing frames first (always priority for main display)
            if hasattr(self, 'screen_frame_queue'):
                try:
                    # Get screen frame from queue with timeout
                    frame_rgb = self.screen_frame_queue.get_nowait()
                    
                    # Validate frame data
                    if frame_rgb is not None and frame_rgb.size > 0:
                        # Create photo safely
                        pil_image = Image.fromarray(frame_rgb)
                        photo = ImageTk.PhotoImage(pil_image)
                        
                        # Update main display with screen sharing
                        if hasattr(self, 'main_video_label') and self.main_video_label and self.main_video_label.winfo_exists():
                            self.main_video_label.configure(image=photo, text="🖥️ Screen Sharing")
                            self.main_video_label.image = photo  # Keep reference
                            screen_frame_available = True
                            
                except queue.Empty:
                    # No screen frame available
                    pass
                except Exception as e:
                    print(f"Screen frame error: {e}")
            
            # Check for video frames
            if hasattr(self, 'video_frame_queue'):
                try:
                    # Get frame from queue with timeout
                    frame_data = self.video_frame_queue.get_nowait()
                    
                    # Handle both old format (just frame) and new format (client_id, frame)
                    if isinstance(frame_data, tuple) and len(frame_data) == 2:
                        client_id, frame_rgb = frame_data
                    else:
                        # Old format - just the frame (local video)
                        frame_rgb = frame_data
                        client_id = None
                    
                    current_video_client = client_id
                    
                    # Validate frame data
                    if frame_rgb is not None and frame_rgb.size > 0:
                        # Create photo safely
                        pil_image = Image.fromarray(frame_rgb)
                        photo = ImageTk.PhotoImage(pil_image)
                        
                        # Determine where to display the video
                        if screen_frame_available:
                            # Screen sharing is active, show video in small preview area
                            if (hasattr(self, 'your_video_label') and self.your_video_label and 
                                hasattr(self.your_video_label, 'winfo_exists') and self.your_video_label.winfo_exists()):
                                if client_id == 0:  # Host video
                                    display_text = "📹 Host Video"
                                    header_text = "📹 Host Video"
                                elif client_id in self.clients_list:
                                    display_text = f"📹 {self.clients_list[client_id]['name']}"
                                    header_text = f"📹 {self.clients_list[client_id]['name']}"
                                else:
                                    display_text = "📹 Remote Video"
                                    header_text = "📹 Remote Video"
                                    
                                self.your_video_label.configure(image=photo, text=display_text)
                                self.your_video_label.image = photo  # Keep reference
                                
                                # Only update header if it changed (prevent flickering)
                                if hasattr(self, 'your_video_header') and self.your_video_header and self.last_header_text != header_text:
                                    self.your_video_header.configure(text=header_text)
                                    self.last_header_text = header_text
                        else:
                            # No screen sharing, show video in main display
                            if (hasattr(self, 'main_video_label') and self.main_video_label and 
                                hasattr(self.main_video_label, 'winfo_exists') and self.main_video_label.winfo_exists()):
                                if client_id == 0:  # Host video
                                    display_text = "📹 Host Video"
                                elif client_id in self.clients_list:
                                    display_text = f"📹 {self.clients_list[client_id]['name']}"
                                else:
                                    display_text = "📹 Remote Video"
                                    
                                self.main_video_label.configure(image=photo, text=display_text)
                                self.main_video_label.image = photo  # Keep reference
                            
                except queue.Empty:
                    # No video frame available, skip this update
                    pass
                except Exception as e:
                    print(f"Video frame error: {e}")
            
            # Update UI state only when mode changes (prevent flickering)
            new_display_mode = 'screen_sharing' if screen_frame_available else ('video' if current_video_client is not None else 'none')
            
            if self.current_display_mode != new_display_mode or self.current_video_source != current_video_client:
                self.current_display_mode = new_display_mode
                self.current_video_source = current_video_client
                
                # Update UI elements only when state changes
                if new_display_mode != 'screen_sharing':
                    # Reset header to "Your Video" when no screen sharing (only if changed)
                    if hasattr(self, 'your_video_header') and self.your_video_header and self.last_header_text != "📹 Your Video":
                        self.your_video_header.configure(text="📹 Your Video")
                        self.last_header_text = "📹 Your Video"
                        
                    # Reset your video label to show local status (only if changed)
                    if hasattr(self, 'your_video_label') and self.your_video_label:
                        expected_text = "📹 Camera On" if self.video_enabled else "📹 Camera Off"
                        current_text = self.your_video_label.cget('text')
                        if current_text != expected_text and not current_text.startswith('📹 Host') and not current_text.startswith('📹 Remote'):
                            self.your_video_label.configure(text=expected_text)
                    
        except Exception as e:
            print(f"Critical display error: {e}")
        
        # Schedule next update with safety checks and adaptive frequency
        try:
            if hasattr(self, 'root') and self.root and self.connected:
                # Use adaptive refresh rate - slower when display is stable
                if new_display_mode == 'screen_sharing':
                    # Screen sharing is stable, can use lower refresh rate
                    self.root.after(100, self.update_video_display_from_queue)  # 10 FPS for screen sharing
                else:
                    # Video mode needs higher refresh rate
                    self.root.after(50, self.update_video_display_from_queue)  # 20 FPS for video
        except:
            # GUI might be destroyed, stop scheduling
            pass
        
    def setup_modern_style(self):
        """Setup modern dark theme styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors for modern dark theme
        style.configure('Modern.TFrame', background='#2d2d2d', relief='flat')
        style.configure('Header.TFrame', background='#1e1e1e', relief='flat')
        style.configure('Sidebar.TFrame', background='#252525', relief='flat')
        
        # Modern buttons
        style.configure('Modern.TButton',
                       background='#0078d4',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        style.configure('Success.TButton',
                       background='#28a745',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        style.configure('Danger.TButton',
                       background='#dc3545',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        style.configure('Warning.TButton',
                       background='#fd7e14',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        # Modern labels
        style.configure('Modern.TLabel',
                       background='#2d2d2d',
                       foreground='white',
                       font=('Segoe UI', 10))
        
        style.configure('Title.TLabel',
                       background='#2d2d2d',
                       foreground='white',
                       font=('Segoe UI', 16, 'bold'))
        
        # Modern entry
        style.configure('Modern.TEntry',
                       fieldbackground='#3d3d3d',
                       foreground='white',
                       borderwidth=0,
                       insertcolor='white')
        
        # Modern treeview
        style.configure('Modern.Treeview',
                       background='#2d2d2d',
                       foreground='white',
                       fieldbackground='#2d2d2d',
                       borderwidth=0)
        
        style.configure('Modern.Treeview.Heading',
                       background='#404040',
                       foreground='white',
                       borderwidth=0)
    
    def test_connection(self):
        """Test connection to server"""
        server_ip = self.server_ip_entry.get().strip()
        if not server_ip:
            self.conn_status_label.config(text="❌ Please enter server IP", fg='#dc3545')
            return
            
        self.conn_status_label.config(text="🔍 Testing connection...", fg='#fd7e14')
        self.root.update()
        
        try:
            # Test TCP connection
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            test_socket.connect((server_ip, self.tcp_port))
            test_socket.close()
            
            self.conn_status_label.config(text="✅ Server is reachable!", fg='#28a745')
        except socket.timeout:
            self.conn_status_label.config(text="❌ Connection timeout - Check server IP", fg='#dc3545')
        except ConnectionRefusedError:
            self.conn_status_label.config(text="❌ Server not running on this IP", fg='#dc3545')
        except Exception as e:
            self.conn_status_label.config(text=f"❌ Test failed: {str(e)}", fg='#dc3545')
    
    def show_connection_screen(self):
        """Show the enhanced modern connection screen"""
        # Clear main container
        for widget in self.main_container.winfo_children():
            widget.destroy()
            
        # Main background with gradient effect
        main_bg = tk.Frame(self.main_container, bg='#0f0f0f')
        main_bg.pack(fill=tk.BOTH, expand=True)
        
        # Create gradient effect with multiple frames
        gradient_frame = tk.Frame(main_bg, bg='#1a1a1a')
        gradient_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Center container with glass morphism effect
        center_container = tk.Frame(gradient_frame, bg='#1e1e1e')
        center_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Main card with rounded corners effect
        main_card = tk.Frame(center_container, bg='#2d2d2d', padx=50, pady=40)
        main_card.pack(padx=20, pady=20)
        
        # Add glow effect border
        glow_frame = tk.Frame(main_card, bg='#0078d4', height=3)
        glow_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Header section with logo and title
        header_section = tk.Frame(main_card, bg='#2d2d2d')
        header_section.pack(pady=(0, 40))
        
        # App logo/icon
        logo_frame = tk.Frame(header_section, bg='#0078d4', width=80, height=80)
        logo_frame.pack(pady=(0, 20))
        logo_frame.pack_propagate(False)
        
        logo_label = tk.Label(logo_frame, text="🎥", 
                             font=('Segoe UI', 36), 
                             fg='white', bg='#0078d4')
        logo_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title and subtitle
        title_label = tk.Label(header_section, text="LAN Meeting Client", 
                              font=('Segoe UI', 32, 'bold'), 
                              fg='#ffffff', bg='#2d2d2d')
        title_label.pack()
        
        subtitle_label = tk.Label(header_section, text="Connect to your team's video conference", 
                                 font=('Segoe UI', 14), 
                                 fg='#b0b0b0', bg='#2d2d2d')
        subtitle_label.pack(pady=(8, 0))
        
        # Connection form
        form_container = tk.Frame(main_card, bg='#2d2d2d')
        form_container.pack(pady=(0, 30))
        
        # Server IP section with enhanced styling
        ip_container = tk.Frame(form_container, bg='#363636', padx=25, pady=20)
        ip_container.pack(fill=tk.X, pady=(0, 20))
        
        ip_header = tk.Frame(ip_container, bg='#363636')
        ip_header.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(ip_header, text="🌐", 
                font=('Segoe UI', 18), 
                fg='#0078d4', bg='#363636').pack(side=tk.LEFT)
        
        tk.Label(ip_header, text="Server IP Address", 
                font=('Segoe UI', 14, 'bold'), 
                fg='white', bg='#363636').pack(side=tk.LEFT, padx=(10, 0))
        
        self.server_ip_entry = tk.Entry(ip_container, 
                                       font=('Segoe UI', 16),
                                       bg='#4a4a4a', fg='white',
                                       relief='flat', borderwidth=0,
                                       insertbackground='#0078d4',
                                       width=30)
        self.server_ip_entry.pack(fill=tk.X, ipady=15)
        self.server_ip_entry.insert(0, "192.168.1.100")
        
        # Add placeholder text effect
        self.add_placeholder_effect(self.server_ip_entry, "Enter server IP address (e.g., 192.168.1.100)")
        
        # Name section with enhanced styling
        name_container = tk.Frame(form_container, bg='#363636', padx=25, pady=20)
        name_container.pack(fill=tk.X, pady=(0, 20))
        
        name_header = tk.Frame(name_container, bg='#363636')
        name_header.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(name_header, text="👤", 
                font=('Segoe UI', 18), 
                fg='#28a745', bg='#363636').pack(side=tk.LEFT)
        
        tk.Label(name_header, text="Your Display Name", 
                font=('Segoe UI', 14, 'bold'), 
                fg='white', bg='#363636').pack(side=tk.LEFT, padx=(10, 0))
        
        self.name_entry = tk.Entry(name_container, 
                                  font=('Segoe UI', 16),
                                  bg='#4a4a4a', fg='white',
                                  relief='flat', borderwidth=0,
                                  insertbackground='#28a745',
                                  width=30)
        self.name_entry.pack(fill=tk.X, ipady=15)
        self.name_entry.insert(0, f"User_{int(time.time()) % 1000}")
        
        # Add placeholder text effect
        self.add_placeholder_effect(self.name_entry, "Enter your name for the meeting")
        
        # Pre-meeting settings section
        settings_container = tk.Frame(form_container, bg='#363636', padx=25, pady=20)
        settings_container.pack(fill=tk.X, pady=(0, 30))
        
        settings_header = tk.Label(settings_container, text="⚙️ Join Settings", 
                                  font=('Segoe UI', 14, 'bold'), 
                                  fg='white', bg='#363636')
        settings_header.pack(anchor=tk.W, pady=(0, 15))
        
        # Settings checkboxes
        settings_frame = tk.Frame(settings_container, bg='#363636')
        settings_frame.pack(fill=tk.X)
        
        self.join_with_video = tk.BooleanVar(value=False)
        self.join_with_audio = tk.BooleanVar(value=False)
        
        video_check = tk.Checkbutton(settings_frame, text="📹 Join with camera on", 
                                    variable=self.join_with_video,
                                    font=('Segoe UI', 12), 
                                    fg='white', bg='#363636',
                                    selectcolor='#4a4a4a',
                                    activebackground='#363636',
                                    activeforeground='white')
        video_check.pack(anchor=tk.W, pady=(0, 8))
        
        audio_check = tk.Checkbutton(settings_frame, text="🎤 Join with microphone on", 
                                    variable=self.join_with_audio,
                                    font=('Segoe UI', 12), 
                                    fg='white', bg='#363636',
                                    selectcolor='#4a4a4a',
                                    activebackground='#363636',
                                    activeforeground='white')
        audio_check.pack(anchor=tk.W)
        
        # Action buttons with enhanced styling
        button_container = tk.Frame(form_container, bg='#2d2d2d')
        button_container.pack(pady=(20, 0))
        
        # Test connection button
        test_btn = tk.Button(button_container, text="🔍 Test Connection", 
                            command=self.test_connection,
                            bg='#6c757d', fg='white', 
                            font=('Segoe UI', 12, 'bold'),
                            relief='flat', borderwidth=0,
                            padx=25, pady=12,
                            cursor='hand2')
        test_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Main connect button with gradient effect
        connect_frame = tk.Frame(button_container, bg='#0056b3', padx=2, pady=2)
        connect_frame.pack(side=tk.LEFT)
        
        self.connect_btn = tk.Button(connect_frame, text="🚀 Join Meeting", 
                                    command=self.connect_to_server,
                                    bg='#0078d4', fg='white', 
                                    font=('Segoe UI', 16, 'bold'),
                                    relief='flat', borderwidth=0,
                                    padx=35, pady=15,
                                    cursor='hand2')
        self.connect_btn.pack()
        
        # Status display
        status_container = tk.Frame(main_card, bg='#2d2d2d')
        status_container.pack(pady=(20, 0))
        
        self.conn_status_label = tk.Label(status_container, text="Ready to connect", 
                                         font=('Segoe UI', 12), 
                                         fg='#b0b0b0', bg='#2d2d2d')
        self.conn_status_label.pack()
        
        # Quick tips section
        tips_container = tk.Frame(main_card, bg='#1a1a1a', padx=20, pady=15)
        tips_container.pack(fill=tk.X, pady=(30, 0))
        
        tips_title = tk.Label(tips_container, text="💡 Quick Tips", 
                             font=('Segoe UI', 12, 'bold'), 
                             fg='#ffd43b', bg='#1a1a1a')
        tips_title.pack(anchor=tk.W, pady=(0, 8))
        
        tips_text = """• Ensure the meeting server is running before connecting
• Use your local network IP (192.168.x.x) for LAN meetings
• Test your connection first to verify server availability
• Choose a clear display name for easy identification"""
        
        tips_label = tk.Label(tips_container, text=tips_text, 
                             font=('Segoe UI', 10), 
                             fg='#cccccc', bg='#1a1a1a',
                             justify=tk.LEFT)
        tips_label.pack(anchor=tk.W)
        
        # Bind Enter key to connect
        self.server_ip_entry.bind('<Return>', lambda e: self.connect_to_server())
        self.name_entry.bind('<Return>', lambda e: self.connect_to_server())
        
        # Add hover effects to buttons
        self.add_button_hover_effects()
        
    def add_placeholder_effect(self, entry, placeholder_text):
        """Add placeholder text effect to entry widgets"""
        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END)
                entry.config(fg='white')
        
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder_text)
                entry.config(fg='#888888')
        
        # Don't apply placeholder effect if entry already has content
        if not entry.get() or entry.get() in ["192.168.1.100", "127.0.0.1"]:
            return
            
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        
    def add_button_hover_effects(self):
        """Add hover effects to buttons"""
        def on_enter(event, button, hover_color):
            button.config(bg=hover_color)
        
        def on_leave(event, button, normal_color):
            button.config(bg=normal_color)
        
        # Connect button hover effect
        self.connect_btn.bind('<Enter>', lambda e: on_enter(e, self.connect_btn, '#0056b3'))
        self.connect_btn.bind('<Leave>', lambda e: on_leave(e, self.connect_btn, '#0078d4'))
        
        # Add hover effect to connect button
        def on_enter(event):
            self.connect_btn.configure(bg='#106ebe')
        def on_leave(event):
            self.connect_btn.configure(bg='#0078d4')
            
        self.connect_btn.bind("<Enter>", on_enter)
        self.connect_btn.bind("<Leave>", on_leave)
        
        # Bind Enter key to connect
        self.root.bind('<Return>', lambda e: self.connect_to_server())
        
    def show_meeting_screen(self):
        """Show the main meeting interface"""
        # Clear main container
        for widget in self.main_container.winfo_children():
            widget.destroy()
            
        # Main meeting interface
        meeting_frame = tk.Frame(self.main_container, bg='#1e1e1e')
        meeting_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top header
        self.create_meeting_header(meeting_frame)
        
        # Main content area
        content_area = tk.Frame(meeting_frame, bg='#1e1e1e')
        content_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Video area
        self.create_meeting_video_section(content_area)
        
        # Bottom controls
        self.create_meeting_controls(content_area)
        
        # Start video display timer now that meeting screen is ready
        self.start_video_display_timer()
        
    def create_meeting_header(self, parent):
        """Create meeting header"""
        header = tk.Frame(parent, bg='#1e1e1e', height=70)
        header.pack(fill=tk.X, padx=20, pady=(20, 0))
        header.pack_propagate(False)
        
        # Left side - Meeting info
        left_header = tk.Frame(header, bg='#1e1e1e')
        left_header.pack(side=tk.LEFT, fill=tk.Y)
        
        meeting_title = tk.Label(left_header, text="LAN Meeting", 
                                font=('Segoe UI', 18, 'bold'), 
                                fg='white', bg='#1e1e1e')
        meeting_title.pack(anchor=tk.W)
        
        self.meeting_status = tk.Label(left_header, text="● Connected", 
                                      font=('Segoe UI', 11), 
                                      fg='#51cf66', bg='#1e1e1e')
        self.meeting_status.pack(anchor=tk.W, pady=(2, 0))
        
        # Right side - Leave button
        right_header = tk.Frame(header, bg='#1e1e1e')
        right_header.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.leave_btn = tk.Button(right_header, text="📞 Leave Meeting", 
                                  command=self.disconnect,
                                  bg='#d13438', fg='white', 
                                  font=('Segoe UI', 11, 'bold'),
                                  relief='flat', borderwidth=0,
                                  padx=25, pady=12,
                                  cursor='hand2')
        self.leave_btn.pack(side=tk.RIGHT, pady=10)
        
    def create_meeting_video_section(self, parent):
        """Create the video conference area"""
        video_container = tk.Frame(parent, bg='#1e1e1e')
        video_container.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Main video area
        main_video_frame = tk.Frame(video_container, bg='#000000', relief='solid', bd=1)
        main_video_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Main video display
        self.main_video_label = tk.Label(main_video_frame, 
                                        text="🎥 Waiting for video...",
                                        font=('Segoe UI', 16),
                                        fg='#888888', bg='#000000')
        self.main_video_label.pack(expand=True)
        
        # Right sidebar (increased width for better visibility)
        sidebar = tk.Frame(video_container, bg='#2d2d2d', width=400)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Your video preview
        self.create_your_video_section(sidebar)
        
        # Participants section
        self.create_meeting_participants_section(sidebar)
        
        # Chat section
        self.create_meeting_chat_section(sidebar)
        
        # File sharing section
        self.create_file_sharing_section(sidebar)
        
    def create_your_video_section(self, parent):
        """Create your video preview section"""
        your_video_frame = tk.Frame(parent, bg='#2d2d2d')
        your_video_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Header (will be updated dynamically)
        self.your_video_header = tk.Label(your_video_frame, text="📹 Your Video", 
                                         font=('Segoe UI', 12, 'bold'), 
                                         fg='white', bg='#2d2d2d')
        self.your_video_header.pack(anchor=tk.W, pady=(0, 10))
        
        # Video preview
        preview_frame = tk.Frame(your_video_frame, bg='#000000', height=120)
        preview_frame.pack(fill=tk.X)
        preview_frame.pack_propagate(False)
        
        self.your_video_label = tk.Label(preview_frame, 
                                        text="📹 Camera Off",
                                        font=('Segoe UI', 10),
                                        fg='#888888', bg='#000000')
        self.your_video_label.pack(expand=True)
        
    def create_meeting_participants_section(self, parent):
        """Create participants section"""
        participants_frame = tk.Frame(parent, bg='#2d2d2d')
        participants_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Header
        header_frame = tk.Frame(participants_frame, bg='#2d2d2d')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="👥 Participants", 
                font=('Segoe UI', 12, 'bold'), 
                fg='white', bg='#2d2d2d').pack(side=tk.LEFT)
        
        self.participant_count_label = tk.Label(header_frame, text="0", 
                                               font=('Segoe UI', 11, 'bold'), 
                                               fg='#0078d4', bg='#2d2d2d')
        self.participant_count_label.pack(side=tk.RIGHT)
        
        # Participants list
        self.participants_listbox = tk.Listbox(participants_frame, 
                                              bg='#3d3d3d', fg='white',
                                              selectbackground='#0078d4',
                                              font=('Segoe UI', 9),
                                              relief='flat', borderwidth=0,
                                              height=4)
        self.participants_listbox.pack(fill=tk.X)
        
    def create_meeting_chat_section(self, parent):
        """Create enhanced chat section with unicast/broadcast support"""
        chat_frame = tk.Frame(parent, bg='#2d2d2d')
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Chat header with message type selector
        header_frame = tk.Frame(chat_frame, bg='#2d2d2d')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="💬 Messages", 
                font=('Segoe UI', 12, 'bold'), 
                fg='white', bg='#2d2d2d').pack(side=tk.LEFT)
        
        # Message type selector
        self.message_type = tk.StringVar(value="chat")
        type_frame = tk.Frame(header_frame, bg='#2d2d2d')
        type_frame.pack(side=tk.RIGHT)
        
        tk.Radiobutton(type_frame, text="Public", variable=self.message_type, value="chat",
                      bg='#2d2d2d', fg='white', selectcolor='#0078d4',
                      font=('Segoe UI', 8), relief='flat').pack(side=tk.LEFT, padx=2)
        
        tk.Radiobutton(type_frame, text="Broadcast", variable=self.message_type, value="broadcast",
                      bg='#2d2d2d', fg='white', selectcolor='#0078d4',
                      font=('Segoe UI', 8), relief='flat').pack(side=tk.LEFT, padx=2)
        
        tk.Radiobutton(type_frame, text="Private", variable=self.message_type, value="unicast",
                      bg='#2d2d2d', fg='white', selectcolor='#0078d4',
                      font=('Segoe UI', 8), relief='flat').pack(side=tk.LEFT, padx=2)
        
        # Chat display
        self.chat_display = tk.Text(chat_frame, 
                                   bg='#3d3d3d', fg='white',
                                   font=('Segoe UI', 9),
                                   relief='flat', borderwidth=0,
                                   wrap=tk.WORD, state=tk.DISABLED,
                                   height=8)
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Private message target selection (hidden by default)
        self.target_frame = tk.Frame(chat_frame, bg='#2d2d2d')
        
        tk.Label(self.target_frame, text="To:", 
                font=('Segoe UI', 9), 
                fg='white', bg='#2d2d2d').pack(side=tk.LEFT, padx=(0, 5))
        
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(self.target_frame, textvariable=self.target_var,
                                        font=('Segoe UI', 9), width=15, state="readonly")
        self.target_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Bind message type change to show/hide target selection
        self.message_type.trace('w', self.on_message_type_change)
        
        # Chat input
        input_frame = tk.Frame(chat_frame, bg='#2d2d2d')
        input_frame.pack(fill=tk.X)
        
        self.chat_entry = tk.Entry(input_frame, 
                                  bg='#3d3d3d', fg='white',
                                  font=('Segoe UI', 9),
                                  relief='flat', borderwidth=0,
                                  insertbackground='white')
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", self.send_chat_message)
        
        self.chat_send_btn = tk.Button(input_frame, text="Send", 
                                      command=self.send_chat_message,
                                      bg='#0078d4', fg='white', 
                                      font=('Segoe UI', 9, 'bold'),
                                      relief='flat', borderwidth=0,
                                      padx=15, pady=6,
                                      cursor='hand2')
        self.chat_send_btn.pack(side=tk.RIGHT)
        
    def on_message_type_change(self, *args):
        """Handle message type change"""
        if self.message_type.get() == "unicast":
            self.target_frame.pack(fill=tk.X, pady=(0, 5))
            self.update_target_list()
        else:
            self.target_frame.pack_forget()
            
    def update_target_list(self):
        """Update the target list for private messages"""
        targets = ["Host"]
        for client_id, client_info in self.clients_list.items():
            if int(client_id) != self.client_id:  # Don't include self
                targets.append(f"{client_info['name']} (ID: {client_id})")
        
        self.target_combo['values'] = targets
        if targets and not self.target_var.get():
            self.target_combo.set(targets[0])
        
    def create_file_sharing_section(self, parent):
        """Create file sharing section"""
        file_frame = tk.Frame(parent, bg='#2d2d2d')
        file_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # File sharing header
        tk.Label(file_frame, text="📁 File Sharing", 
                font=('Segoe UI', 12, 'bold'), 
                fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=(0, 10))
        
        # Shared files list
        files_list_frame = tk.Frame(file_frame, bg='#2d2d2d')
        files_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.shared_files_listbox = tk.Listbox(files_list_frame, 
                                             bg='#3d3d3d', fg='white',
                                             selectbackground='#0078d4',
                                             font=('Segoe UI', 9),
                                             relief='flat', borderwidth=0,
                                             height=4)
        self.shared_files_listbox.pack(fill=tk.BOTH, expand=True)
        
        # File sharing controls (improved layout)
        file_controls_frame = tk.Frame(file_frame, bg='#2d2d2d')
        file_controls_frame.pack(fill=tk.X, pady=(5, 0))
        
        # First row of buttons
        first_row = tk.Frame(file_controls_frame, bg='#2d2d2d')
        first_row.pack(fill=tk.X, pady=(0, 5))
        
        self.share_file_btn = tk.Button(first_row, text="📤 Share File", 
                                       command=self.share_file,
                                       bg='#0078d4', fg='white', 
                                       font=('Segoe UI', 10, 'bold'),
                                       relief='flat', borderwidth=0,
                                       padx=15, pady=8,
                                       cursor='hand2')
        self.share_file_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.download_file_btn = tk.Button(first_row, text="📥 Download", 
                                          command=self.download_selected_file,
                                          bg='#107c10', fg='white', 
                                          font=('Segoe UI', 10, 'bold'),
                                          relief='flat', borderwidth=0,
                                          padx=15, pady=8,
                                          cursor='hand2')
        self.download_file_btn.pack(side=tk.LEFT)
        
        # Second row - File Manager button (full width for visibility)
        second_row = tk.Frame(file_controls_frame, bg='#2d2d2d')
        second_row.pack(fill=tk.X)
        
        self.file_manager_btn = tk.Button(second_row, text="📁 Open File Manager", 
                                         command=self.open_file_manager,
                                         bg='#6c757d', fg='white', 
                                         font=('Segoe UI', 11, 'bold'),
                                         relief='flat', borderwidth=0,
                                         padx=20, pady=10,
                                         cursor='hand2')
        self.file_manager_btn.pack(fill=tk.X)
        
    def create_meeting_controls(self, parent):
        """Create bottom meeting controls"""
        controls_frame = tk.Frame(parent, bg='#2d2d2d', height=100)
        controls_frame.pack(fill=tk.X, pady=(20, 0))
        controls_frame.pack_propagate(False)
        
        # Center the controls
        center_controls = tk.Frame(controls_frame, bg='#2d2d2d')
        center_controls.pack(expand=True)
        
        # Media controls
        media_frame = tk.Frame(center_controls, bg='#2d2d2d')
        media_frame.pack(pady=20)
        
        # Video button
        self.video_btn = tk.Button(media_frame, text="📹\nVideo", 
                                  command=self.toggle_video,
                                  bg='#404040', fg='white', 
                                  font=('Segoe UI', 10, 'bold'),
                                  relief='flat', borderwidth=0,
                                  width=8, height=3,
                                  cursor='hand2')
        self.video_btn.pack(side=tk.LEFT, padx=10)
        
        # Microphone button
        self.mic_btn = tk.Button(media_frame, text="🎤\nMic", 
                                command=self.toggle_microphone,
                                bg='#404040', fg='white', 
                                font=('Segoe UI', 10, 'bold'),
                                relief='flat', borderwidth=0,
                                width=8, height=3,
                                cursor='hand2')
        self.mic_btn.pack(side=tk.LEFT, padx=5)
        
        # Speaker button (starts enabled by default)
        self.speaker_btn = tk.Button(media_frame, text="🔊\nSpeaker On", 
                                    command=self.toggle_speaker,
                                    bg='#28a745', fg='white', 
                                    font=('Segoe UI', 10, 'bold'),
                                    relief='flat', borderwidth=0,
                                    width=8, height=3,
                                    cursor='hand2')
        self.speaker_btn.pack(side=tk.LEFT, padx=5)
        
        # Present button
        self.present_btn = tk.Button(media_frame, text="🖥️\nPresent", 
                                    command=self.toggle_presentation,
                                    bg='#404040', fg='white', 
                                    font=('Segoe UI', 10, 'bold'),
                                    relief='flat', borderwidth=0,
                                    width=8, height=3,
                                    cursor='hand2')
        self.present_btn.pack(side=tk.LEFT, padx=10)
        
    def connect_to_server(self):
        """Connect to the communication server with enhanced join settings"""
        try:
            self.server_host = self.server_ip_entry.get().strip()
            self.client_name = self.name_entry.get().strip()
            
            # Validate input
            if not self.server_host or not self.client_name:
                self.conn_status_label.config(text="❌ Please fill in all fields", fg='#dc3545')
                return
                
            # Check for placeholder text
            if self.client_name.startswith("User_") and len(self.client_name) <= 8:
                response = messagebox.askyesno("Default Name", 
                                             "You're using a default name. Continue with this name?")
                if not response:
                    return
                    
            self.conn_status_label.config(text="🔄 Connecting to server...", fg='#ffd43b')
            self.connect_btn.config(state=tk.DISABLED, text="Connecting...")
            self.root.update()
            
            # Create TCP socket
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(10)  # 10 second timeout
            self.tcp_socket.connect((self.server_host, self.tcp_port))
            
            # Create UDP sockets
            self.udp_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Bind UDP sockets to receive data
            self.udp_video_socket.bind(('', self.udp_video_port))
            self.udp_audio_socket.bind(('', self.udp_audio_port))
            
            self.connected = True
            self.running = True
            
            self.conn_status_label.config(text="✅ Connected! Joining meeting...", fg='#28a745')
            self.root.update()
            
            # Start communication threads
            threading.Thread(target=self.tcp_receiver, daemon=True).start()
            threading.Thread(target=self.udp_video_receiver, daemon=True).start()
            threading.Thread(target=self.udp_audio_receiver, daemon=True).start()
            
            # Send join message using enhanced protocol
            join_msg = create_login_message(self.client_name)
            self.send_tcp_message(join_msg)
            
            # Start heartbeat thread
            threading.Thread(target=self.heartbeat_loop, daemon=True).start()
            
            # Switch to meeting screen
            self.show_meeting_screen()
            
            # File sharing controls are already enabled
            
            # Auto-start speaker for receiving audio (always enabled by default)
            self.root.after(1000, self.start_speaker)  # Start speaker after 1 second
            
            # Auto-start media based on join settings (with longer delay to ensure GUI is ready)
            if hasattr(self, 'join_with_video') and self.join_with_video.get():
                self.root.after(2000, self.toggle_video)  # Start video after 2 seconds
                
            if hasattr(self, 'join_with_audio') and self.join_with_audio.get():
                self.root.after(2500, self.toggle_microphone)  # Start microphone after 2.5 seconds
            
        except socket.timeout:
            self.conn_status_label.config(text="❌ Connection timeout", fg='#dc3545')
            self.connect_btn.config(state=tk.NORMAL, text="🚀 Join Meeting")
            messagebox.showerror("Connection Error", "Connection timed out. Please check the server IP and ensure the server is running.")
        except ConnectionRefusedError:
            self.conn_status_label.config(text="❌ Connection refused", fg='#dc3545')
            self.connect_btn.config(state=tk.NORMAL, text="🚀 Join Meeting")
            messagebox.showerror("Connection Error", "Connection refused. Please ensure the server is running and accessible.")
        except Exception as e:
            self.conn_status_label.config(text="❌ Connection failed", fg='#dc3545')
            self.connect_btn.config(state=tk.NORMAL, text="🚀 Join Meeting")
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            
    def send_tcp_message(self, message):
        """Send TCP message to server with enhanced error handling"""
        try:
            if not self.connected or not self.tcp_socket:
                return False
                
            message_data = json.dumps(message).encode('utf-8')
            message_length = struct.pack('!I', len(message_data))
            self.tcp_socket.send(message_length + message_data)
            return True
        except Exception as e:
            print(f"Error sending TCP message: {e}")
            self.handle_connection_lost()
            return False
            
    def heartbeat_loop(self):
        """Send periodic heartbeat messages to server"""
        while self.running and self.connected:
            try:
                heartbeat_msg = create_heartbeat_message()
                if not self.send_tcp_message(heartbeat_msg):
                    break
                time.sleep(HEARTBEAT_INTERVAL)
            except Exception as e:
                print(f"Heartbeat error: {e}")
                break
            
    def tcp_receiver(self):
        """Receive TCP messages from server with improved error handling"""
        consecutive_errors = 0
        max_errors = 5
        last_activity = time.time()
        
        while self.running and self.connected:
            try:
                # Set socket timeout to prevent hanging (shorter timeout for better responsiveness)
                self.tcp_socket.settimeout(10.0)  # 10 second timeout
                
                # Receive message length
                length_data = self.tcp_socket.recv(4)
                if not length_data:
                    print("TCP connection closed by server")
                    break
                    
                message_length = struct.unpack('!I', length_data)[0]
                
                # Validate message length
                if message_length > 1024 * 1024:  # 1MB max message size
                    print(f"Message too large: {message_length} bytes")
                    break
                
                # Receive message data
                message_data = b''
                while len(message_data) < message_length:
                    remaining = message_length - len(message_data)
                    chunk = self.tcp_socket.recv(min(remaining, 8192))  # 8KB chunks
                    if not chunk:
                        print("Connection lost while receiving message")
                        break
                    message_data += chunk
                    
                if len(message_data) != message_length:
                    print(f"Incomplete message received: {len(message_data)}/{message_length}")
                    break
                    
                # Parse message
                try:
                    message = json.loads(message_data.decode('utf-8'))
                    self.process_server_message(message)
                    consecutive_errors = 0  # Reset error counter on success
                    last_activity = time.time()  # Update activity timestamp
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    consecutive_errors += 1
                
            except socket.timeout:
                # Check if we've been inactive for too long
                if time.time() - last_activity > 60:  # 60 seconds of inactivity
                    print("TCP connection inactive for too long, disconnecting")
                    break
                # Timeout is normal during periods of no activity, just continue
                continue
            except ConnectionResetError:
                print("TCP connection reset by server")
                break
            except Exception as e:
                consecutive_errors += 1
                if self.running:
                    print(f"TCP receiver error ({consecutive_errors}/{max_errors}): {e}")
                
                # If too many consecutive errors, disconnect
                if consecutive_errors >= max_errors:
                    print("Too many TCP errors, disconnecting")
                    break
                    
                time.sleep(1)  # Brief pause before retrying
        
        # Connection lost - handle cleanup
        if self.running and self.connected:
            print("TCP connection lost")
            self.root.after(0, self.handle_connection_lost)
            
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
            if file_size > self.file_transfer['max_file_size']:
                messagebox.showerror("File Too Large", 
                                   f"File size ({file_size} bytes) exceeds maximum allowed size ({self.file_transfer['max_file_size']} bytes).")
                return
                
            if file_size == 0:
                messagebox.showerror("File Error", "Cannot share empty file.")
                return
                
            # Generate unique file ID
            fid = str(uuid.uuid4())
            filename = os.path.basename(file_path)
            
            # Store pending upload
            self.file_transfer['pending_uploads'][fid] = file_path
            
            # Send file offer
            offer_msg = {
                'type': MessageTypes.FILE_OFFER,
                'fid': fid,
                'filename': filename,
                'size': file_size
            }
            
            if self.send_tcp_message(offer_msg):
                self.add_chat_message("System", f"Offering to share: {filename} ({file_size} bytes)")
            else:
                messagebox.showerror("Upload Failed", "Failed to send file offer.")
                del self.file_transfer['pending_uploads'][fid]
                
        except Exception as e:
            messagebox.showerror("Share Error", f"Error sharing file: {str(e)}")
            
    def download_selected_file(self):
        """Download selected file"""
        try:
            selection = self.shared_files_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a file to download.")
                return
                
            # Get selected file info using index mapping
            selected_index = selection[0]
            
            # Use the mapping to get full fid and filename
            if not hasattr(self, 'file_list_mapping') or selected_index not in self.file_list_mapping:
                messagebox.showerror("Selection Error", "Could not find file information. Please refresh the file list.")
                return
                
            file_mapping = self.file_list_mapping[selected_index]
            fid = file_mapping['fid']
            filename = file_mapping['filename']
                
            # Ask where to save
            save_path = filedialog.asksaveasfilename(
                title="Save file as",
                initialfile=filename,
                defaultextension=os.path.splitext(filename)[1]
            )
            
            if not save_path:
                return
                
            # Store pending download
            self.file_transfer['pending_downloads'][fid] = save_path
            
            # Send file request
            request_msg = {
                'type': MessageTypes.FILE_REQUEST,
                'fid': fid
            }
            
            if self.send_tcp_message(request_msg):
                self.add_chat_message("System", f"Requesting download: {filename}")
            else:
                messagebox.showerror("Download Failed", "Failed to send download request.")
                del self.file_transfer['pending_downloads'][fid]
                
        except Exception as e:
            messagebox.showerror("Download Error", f"Error downloading file: {str(e)}")
            
    def open_file_manager(self):
        """Open file manager for downloads directory"""
        try:
            download_dir = self.file_transfer['download_dir']
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
                
            # Open file manager (platform-specific)
            import platform
            system = platform.system()
            
            if system == "Windows":
                os.startfile(download_dir)
            elif system == "Darwin":  # macOS
                os.system(f"open '{download_dir}'")
            else:  # Linux and others
                os.system(f"xdg-open '{download_dir}'")
                
        except Exception as e:
            messagebox.showerror("File Manager Error", f"Could not open file manager: {str(e)}")
            
    def update_shared_files_list(self):
        """Update the shared files list display"""
        try:
            self.shared_files_listbox.delete(0, tk.END)
            
            # Create a mapping from list index to full fid for easy retrieval
            if not hasattr(self, 'file_list_mapping'):
                self.file_list_mapping = {}
            self.file_list_mapping.clear()
            
            index = 0
            for fid, file_info in self.shared_files.items():
                filename = file_info.get('filename', 'Unknown')
                size = file_info.get('size', 0)
                uploader = file_info.get('uploader', 'Unknown')
                
                # Format size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                    
                # Display truncated fid for readability
                display_text = f"{filename} ({size_str}) - {uploader} [{fid[:8]}...]"
                self.shared_files_listbox.insert(tk.END, display_text)
                
                # Store mapping from list index to full fid and filename
                self.file_list_mapping[index] = {'fid': fid, 'filename': filename}
                index += 1
                
        except Exception as e:
            print(f"Error updating shared files list: {e}")
            
    def handle_file_upload_port(self, message):
        """Handle file upload port response"""
        try:
            fid = message.get('fid')
            port = message.get('port')
            
            if fid not in self.file_transfer['pending_uploads']:
                print(f"No pending upload for fid: {fid}")
                return
                
            file_path = self.file_transfer['pending_uploads'][fid]
            
            # Start upload in background thread
            upload_thread = threading.Thread(
                target=self.do_file_upload,
                args=(fid, file_path, port),
                daemon=True
            )
            upload_thread.start()
            
            # Remove from pending
            del self.file_transfer['pending_uploads'][fid]
            
        except Exception as e:
            print(f"Error handling upload port: {e}")
            
    def handle_file_download_port(self, message):
        """Handle file download port response"""
        try:
            fid = message.get('fid')
            filename = message.get('filename')
            size = message.get('size')
            port = message.get('port')
            
            save_path = self.file_transfer['pending_downloads'].get(fid)
            
            # Start download in background thread
            download_thread = threading.Thread(
                target=self.do_file_download,
                args=(fid, filename, size, port, save_path),
                daemon=True
            )
            download_thread.start()
            
            # Remove from pending
            if fid in self.file_transfer['pending_downloads']:
                del self.file_transfer['pending_downloads'][fid]
                
        except Exception as e:
            print(f"Error handling download port: {e}")
            
    def do_file_upload(self, fid, file_path, port):
        """Perform actual file upload"""
        try:
            if not os.path.exists(file_path):
                self.root.after(0, lambda: self.add_chat_message("System", f"Upload failed: File not found"))
                return
                
            # Connect to upload port
            upload_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            upload_socket.settimeout(30)
            upload_socket.connect((self.server_host, port))
            
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            bytes_sent = 0
            
            self.root.after(0, lambda: self.add_chat_message("System", f"Uploading {filename}..."))
            
            with open(file_path, 'rb') as f:
                while bytes_sent < file_size:
                    data = f.read(self.file_transfer['chunk_size'])
                    if not data:
                        break
                        
                    upload_socket.send(data)
                    bytes_sent += len(data)
                    
                    # Update progress
                    if bytes_sent % (1024 * 1024) < self.file_transfer['chunk_size']:  # Every 1MB
                        progress = (bytes_sent / file_size) * 100
                        self.root.after(0, lambda p=progress: self.add_chat_message("System", f"Upload progress: {p:.1f}%"))
            
            upload_socket.close()
            self.root.after(0, lambda: self.add_chat_message("System", f"Upload completed: {filename}"))
            
        except Exception as e:
            self.root.after(0, lambda: self.add_chat_message("System", f"Upload failed: {str(e)}"))
            
    def do_file_download(self, fid, filename, size, port, save_path):
        """Perform actual file download"""
        try:
            if not save_path:
                save_path = os.path.join(self.file_transfer['download_dir'], filename)
                
            # Connect to download port
            download_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            download_socket.settimeout(30)
            download_socket.connect((self.server_host, port))
            
            bytes_received = 0
            
            self.root.after(0, lambda: self.add_chat_message("System", f"Downloading {filename}..."))
            
            with open(save_path, 'wb') as f:
                while bytes_received < size:
                    data = download_socket.recv(min(self.file_transfer['chunk_size'], size - bytes_received))
                    if not data:
                        break
                        
                    f.write(data)
                    bytes_received += len(data)
                    
                    # Update progress
                    if bytes_received % (1024 * 1024) < self.file_transfer['chunk_size']:  # Every 1MB
                        progress = (bytes_received / size) * 100
                        self.root.after(0, lambda p=progress: self.add_chat_message("System", f"Download progress: {p:.1f}%"))
            
            download_socket.close()
            
            if bytes_received == size:
                self.root.after(0, lambda: self.add_chat_message("System", f"Download completed: {save_path}"))
            else:
                self.root.after(0, lambda: self.add_chat_message("System", f"Download incomplete: {bytes_received}/{size} bytes"))
                
        except Exception as e:
            self.root.after(0, lambda: self.add_chat_message("System", f"Download failed: {str(e)}"))
                
    def process_server_message(self, message):
        """Process message from server with enhanced protocol handling"""
        msg_type = message.get('type')
        
        # Validate message type
        if not msg_type or not isinstance(msg_type, str):
            print(f"Invalid message type received: {msg_type}")
            return
        
        if msg_type == MessageTypes.LOGIN_SUCCESS or msg_type == 'welcome':
            self.client_id = message.get('client_id')
            self.clients_list = message.get('clients', {})
            self.chat_history = message.get('chat_history', [])
            self.presenter_id = message.get('presenter_id')
            self.host_id = message.get('host_id', 0)
            
            # Update GUI
            self.root.after(0, self.update_participants_list)
            self.root.after(0, self.update_chat_display)
            
        elif msg_type == MessageTypes.USER_JOINED or msg_type == 'user_joined':
            client_id = message.get('client_id') or message.get('uid')
            name = message.get('name') or message.get('username')
            if client_id and name:
                self.clients_list[str(client_id)] = {'name': name, 'status': 'Active'}
                self.root.after(0, self.update_participants_list)
                self.root.after(0, lambda: self.add_chat_message("System", f"{name} joined the session"))
            
        elif msg_type == MessageTypes.USER_LEFT or msg_type == 'user_left':
            client_id = str(message.get('client_id') or message.get('uid', ''))
            name = message.get('name') or message.get('username', 'Unknown')
            if client_id in self.clients_list:
                del self.clients_list[client_id]
            self.root.after(0, self.update_participants_list)
            self.root.after(0, lambda: self.add_chat_message("System", f"{name} left the session"))
            
        elif msg_type == MessageTypes.CHAT or msg_type == 'chat':
            sender_name = message.get('name') or message.get('username', 'Unknown')
            chat_message = message.get('message') or message.get('text', '')
            if sender_name and chat_message:
                self.root.after(0, lambda: self.add_chat_message(sender_name, chat_message))
                
        elif msg_type == MessageTypes.BROADCAST or msg_type == 'broadcast':
            sender_name = message.get('username', 'Unknown')
            broadcast_text = message.get('text', '')
            if sender_name and broadcast_text:
                self.root.after(0, lambda: self.add_chat_message(f"[BROADCAST] {sender_name}", broadcast_text))
                
        elif msg_type == MessageTypes.UNICAST or msg_type == 'unicast':
            from_name = message.get('from_username', 'Unknown')
            unicast_text = message.get('text', '')
            if from_name and unicast_text:
                self.root.after(0, lambda: self.add_chat_message(f"[PRIVATE] {from_name}", unicast_text))
                
        elif msg_type == MessageTypes.UNICAST_SENT or msg_type == 'unicast_sent':
            to_name = message.get('to_username', 'Unknown')
            self.root.after(0, lambda: self.add_chat_message("System", f"Private message sent to {to_name}"))
            
        elif msg_type == MessageTypes.FILE_UPLOAD_PORT or msg_type == 'file_upload_port':
            self.handle_file_upload_port(message)
            
        elif msg_type == MessageTypes.FILE_DOWNLOAD_PORT or msg_type == 'file_download_port':
            self.handle_file_download_port(message)
            
        elif msg_type == MessageTypes.FILE_AVAILABLE or msg_type == 'file_available':
            fid = message.get('fid')
            filename = message.get('filename')
            size = message.get('size')
            uploader = message.get('uploader')
            
            if fid and filename:
                self.shared_files[fid] = {
                    'filename': filename,
                    'size': size,
                    'uploader': uploader
                }
                self.root.after(0, self.update_shared_files_list)
                self.root.after(0, lambda: self.add_chat_message("System", f"File available: {filename} from {uploader}"))
                
        elif msg_type == MessageTypes.HEARTBEAT_ACK or msg_type == 'heartbeat_ack':
            # Heartbeat acknowledged - connection is healthy
            pass
            
        elif msg_type == 'presenter_granted':
            self.is_presenter = True
            self.root.after(0, lambda: self.present_btn.config(text="🖥️\nPresenting", bg='#fd7e14'))
            # Start screen sharing
            self.root.after(100, self.start_screen_sharing)
            
        elif msg_type == 'screen_frame':
            # Received screen frame from server/presenter
            try:
                frame_data = base64.b64decode(message.get('frame_data', ''))
                if frame_data:
                    # Convert to image
                    img = Image.open(io.BytesIO(frame_data))
                    frame_rgb = np.array(img)
                    
                    # Put frame in queue for display
                    try:
                        # Clear old frames if queue is full
                        while self.screen_frame_queue.qsize() > 1:
                            try:
                                self.screen_frame_queue.get_nowait()
                            except queue.Empty:
                                break
                        self.screen_frame_queue.put_nowait(frame_rgb)
                    except queue.Full:
                        pass
            except Exception as e:
                print(f"Error processing screen frame: {e}")
            self.root.after(0, lambda: self.add_chat_message("System", "You are now the presenter"))
            
        elif msg_type == 'presenter_denied':
            reason = message.get('reason', 'Unknown reason')
            self.root.after(0, lambda: messagebox.showwarning("Presenter Request Denied", reason))
            
        elif msg_type == 'presenter_changed':
            presenter_name = message.get('presenter_name')
            self.presenter_id = message.get('presenter_id')
            self.root.after(0, lambda: self.add_chat_message("System", f"{presenter_name} is now presenting"))
            
        elif msg_type == 'presentation_stopped':
            if self.is_presenter:
                self.is_presenter = False
                self.root.after(0, lambda: self.present_btn.config(text="🖥️\nPresent", bg='#404040'))
            self.presenter_id = None
            self.root.after(0, lambda: self.add_chat_message("System", "Presentation stopped"))
            
        # Handle force commands from server
        elif msg_type == 'force_mute':
            self.root.after(0, self.handle_force_mute)
            
        elif msg_type == 'force_mute_all':
            self.root.after(0, self.handle_force_mute)
            
        elif msg_type == 'force_disable_video':
            self.root.after(0, self.handle_force_disable_video)
            
        elif msg_type == 'force_disable_video_all':
            self.root.after(0, self.handle_force_disable_video)
            
        elif msg_type == 'force_stop_presenting':
            self.root.after(0, self.handle_force_stop_presenting)
            
        elif msg_type == 'force_stop_screen_sharing':
            self.root.after(0, self.handle_force_stop_screen_sharing)
            
        elif msg_type == 'host_request':
            request_type = message.get('request_type')
            request_message = message.get('message', '')
            self.root.after(0, lambda: self.handle_host_request(request_type, request_message))
            
        elif msg_type == 'host_status_update':
            # Update Host status in clients list
            host_id = str(message.get('host_id', 0))
            if host_id in self.clients_list:
                self.clients_list[host_id]['video_enabled'] = message.get('video_enabled', False)
                self.clients_list[host_id]['audio_enabled'] = message.get('audio_enabled', False)
                self.root.after(0, self.update_participants_list)
                
        elif msg_type == 'file_shared':
            # New file shared
            file_info = message.get('file_info', {})
            if file_info:
                self.shared_files[file_info['name']] = file_info
                self.root.after(0, self.update_shared_files_list)
                self.root.after(0, lambda: self.add_chat_message("System", f"File '{file_info['name']}' shared by {file_info['shared_by']}"))
                
        elif msg_type == 'file_removed':
            # File removed
            file_name = message.get('file_name')
            if file_name in self.shared_files:
                del self.shared_files[file_name]
                self.root.after(0, self.update_shared_files_list)
                self.root.after(0, lambda: self.add_chat_message("System", f"File '{file_name}' removed"))
                
        elif msg_type == 'files_cleared':
            # All files cleared
            self.shared_files.clear()
            self.root.after(0, self.update_shared_files_list)
            self.root.after(0, lambda: self.add_chat_message("System", "All shared files cleared"))
            
        elif msg_type == 'chat_history_cleared':
            # Chat history cleared
            self.chat_history.clear()
            self.root.after(0, self.update_chat_display)
            self.root.after(0, lambda: self.add_chat_message("System", "Chat history cleared by host"))
            
        elif msg_type == 'cn_present_start':
            # CN_project style presentation start
            presenter_id = message.get('presenter_id')
            presenter_name = message.get('presenter_name', 'Unknown')
            viewer_port = message.get('viewer_port')
            topic = message.get('topic', 'Screen Share')
            
            if presenter_id != self.client_id:  # Not the presenter
                print(f"[CN_SCREEN] {presenter_name} started presentation: {topic}")
                self.root.after(0, lambda: self.add_chat_message("System", f"🎬 {presenter_name} started presentation: {topic}"))
                
                # Store presentation info for viewing
                self.current_presentation = {
                    'presenter_name': presenter_name,
                    'viewer_port': viewer_port,
                    'topic': topic
                }
                
                # Auto-start viewing if screen display is available
                if hasattr(self, 'screen_display') and self.screen_display:
                    threading.Thread(target=lambda: self.cn_view_presentation(viewer_port, presenter_name), daemon=True).start()
            else:
                print(f"[CN_SCREEN] Your presentation '{topic}' is now live!")
                self.root.after(0, lambda: self.add_chat_message("System", f"Your presentation '{topic}' is now live!"))
                
        elif msg_type == 'cn_present_stop':
            # CN_project style presentation stop
            presenter_name = message.get('presenter_name', 'Unknown')
            print(f"[CN_SCREEN] {presenter_name} stopped presentation")
            self.root.after(0, lambda: self.add_chat_message("System", f"{presenter_name} stopped presentation"))
            self.current_presentation = None
                
    def udp_video_receiver(self):
        """Receive UDP video streams with timeout handling"""
        consecutive_errors = 0
        max_errors = 5
        
        # Set socket timeout to prevent hanging
        if hasattr(self, 'udp_video_socket') and self.udp_video_socket:
            self.udp_video_socket.settimeout(5.0)  # 5 second timeout
        
        while self.running and self.connected:
            try:
                data, address = self.udp_video_socket.recvfrom(65536)
                
                # Parse video packet header
                if len(data) < 12:
                    continue
                    
                client_id, sequence, frame_size = struct.unpack('!III', data[:12])
                frame_data = data[12:]
                
                # Process video frame
                if len(frame_data) == frame_size:
                    try:
                        # Decode frame
                        nparr = np.frombuffer(frame_data, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            # Convert BGR to RGB for display
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            
                            # Put frame in queue for display
                            try:
                                # Clear old frames if queue is full
                                while self.video_frame_queue.qsize() > 1:
                                    try:
                                        self.video_frame_queue.get_nowait()
                                    except queue.Empty:
                                        break
                                self.video_frame_queue.put_nowait((client_id, frame_rgb))
                            except queue.Full:
                                pass  # Skip frame if queue is full
                                
                        # Reset error counter on success
                        consecutive_errors = 0
                        
                    except Exception as e:
                        print(f"Error processing video frame: {e}")
                        consecutive_errors += 1
                        
            except socket.timeout:
                # Timeout is normal when no video is being sent
                continue
            except Exception as e:
                consecutive_errors += 1
                if self.running and self.connected:
                    print(f"UDP video receiver error ({consecutive_errors}/{max_errors}): {e}")
                
                # If too many consecutive errors, stop the receiver
                if consecutive_errors >= max_errors:
                    print("Too many UDP video errors, stopping receiver")
                    break
                    
                time.sleep(0.1)  # Brief pause before retrying
                
    def handle_connection_lost(self):
        """Handle connection lost scenario"""
        if not self.connected:
            return
            
        self.connected = False
        self.running = False
        
        # Update GUI to show disconnected state
        if hasattr(self, 'meeting_status'):
            self.meeting_status.config(text="● Disconnected", fg='#dc3545')
        
        # Show reconnection dialog
        response = messagebox.askyesno(
            "Connection Lost", 
            "Connection to server was lost. Would you like to try reconnecting?"
        )
        
        if response:
            self.attempt_reconnection()
        else:
            self.disconnect()
            
    def attempt_reconnection(self):
        """Attempt to reconnect to the server"""
        max_attempts = MAX_RETRY_ATTEMPTS
        
        for attempt in range(max_attempts):
            try:
                # Close existing sockets
                self.cleanup_sockets()
                
                # Wait before retry
                time.sleep(2 ** attempt)  # Exponential backoff
                
                # Try to reconnect
                self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcp_socket.settimeout(10)
                self.tcp_socket.connect((self.server_host, self.tcp_port))
                
                # Recreate UDP sockets
                self.udp_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.udp_audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.udp_video_socket.bind(('', self.udp_video_port))
                self.udp_audio_socket.bind(('', self.udp_audio_port))
                
                # Restart communication threads
                self.connected = True
                self.running = True
                
                threading.Thread(target=self.tcp_receiver, daemon=True).start()
                threading.Thread(target=self.udp_video_receiver, daemon=True).start()
                threading.Thread(target=self.udp_audio_receiver, daemon=True).start()
                threading.Thread(target=self.heartbeat_loop, daemon=True).start()
                
                # Rejoin the session
                join_msg = create_login_message(self.client_name)
                self.send_tcp_message(join_msg)
                
                # Update GUI
                if hasattr(self, 'meeting_status'):
                    self.meeting_status.config(text="● Reconnected", fg='#51cf66')
                
                messagebox.showinfo("Reconnected", "Successfully reconnected to the server!")
                return True
                
            except Exception as e:
                print(f"Reconnection attempt {attempt + 1} failed: {e}")
                
        # All attempts failed
        messagebox.showerror("Reconnection Failed", 
                           f"Failed to reconnect after {max_attempts} attempts. Please restart the application.")
        self.disconnect()
        return False
        
    def cleanup_sockets(self):
        """Clean up all socket connections"""
        try:
            if hasattr(self, 'tcp_socket') and self.tcp_socket:
                self.tcp_socket.close()
        except:
            pass
            
        try:
            if hasattr(self, 'udp_video_socket') and self.udp_video_socket:
                self.udp_video_socket.close()
        except:
            pass
            
        try:
            if hasattr(self, 'udp_audio_socket') and self.udp_audio_socket:
                self.udp_audio_socket.close()
        except:
            pass
        
    def udp_audio_receiver(self):
        """Receive UDP audio streams with timeout handling"""
        consecutive_errors = 0
        max_errors = 5
        
        # Set socket timeout to prevent hanging
        if hasattr(self, 'udp_audio_socket') and self.udp_audio_socket:
            self.udp_audio_socket.settimeout(5.0)  # 5 second timeout
        
        while self.running and self.connected:
            try:
                data, address = self.udp_audio_socket.recvfrom(4096)
                
                # Parse audio packet
                if len(data) < 8:
                    continue
                    
                client_id, timestamp = struct.unpack('!II', data[:8])
                audio_data = data[8:]
                
                # Play received audio (from other clients or host)
                if len(audio_data) > 0:
                    try:
                        # Play audio if we have an audio output stream and speaker is enabled
                        if (self.speaker_enabled and hasattr(self, 'audio_output_stream') and 
                            self.audio_output_stream and self.audio_output_stream.is_active()):
                            self.audio_output_stream.write(audio_data)
                            print(f"Playing audio from client/host {client_id}, {len(audio_data)} bytes")
                        else:
                            if not self.speaker_enabled:
                                print(f"Received audio from {client_id} but speaker is disabled")
                            elif not hasattr(self, 'audio_output_stream'):
                                print(f"Received audio from {client_id} but no output stream")
                            elif not self.audio_output_stream:
                                print(f"Received audio from {client_id} but output stream is None")
                        
                        # Reset error counter on success
                        consecutive_errors = 0
                        
                    except Exception as e:
                        print(f"Error playing received audio: {e}")
                        consecutive_errors += 1
                        
            except socket.timeout:
                # Timeout is normal when no audio is being sent
                continue
            except Exception as e:
                consecutive_errors += 1
                if self.running and self.connected:
                    print(f"UDP audio receiver error ({consecutive_errors}/{max_errors}): {e}")
                
                # If too many consecutive errors, stop the receiver
                if consecutive_errors >= max_errors:
                    print("Too many UDP audio errors, stopping receiver")
                    break
                    
                time.sleep(0.1)  # Brief pause before retrying
        

        
    def toggle_video(self):
        """Toggle video on/off"""
        if not self.video_enabled:
            self.start_video()
        else:
            self.stop_video()
    
    def start_video(self):
        """Start video capture"""
        try:
            self.video_cap = cv2.VideoCapture(0)
            if not self.video_cap.isOpened():
                messagebox.showerror("Camera Error", "Cannot access camera")
                return
                
            self.video_enabled = True
            self.video_btn.config(text="📹\nVideo On", bg='#28a745')
            
            # Clear local video preview placeholder (NEW FEATURE)
            self.prepare_local_video_preview()
            
            # Start video streaming thread
            threading.Thread(target=self.video_loop, daemon=True).start()
            
            # Notify server
            self.send_media_status_update()
            
        except Exception as e:
            messagebox.showerror("Video Error", f"Failed to start video: {str(e)}")
    
    def stop_video(self):
        """Stop video capture"""
        self.video_enabled = False
        self.video_btn.config(text="📹\nVideo", bg='#404040')
        
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
        
        # Clear local video preview (NEW FEATURE)
        self.clear_local_video_preview()
        
        # Notify server
        self.send_media_status_update()
    
    def video_loop(self):
        """Video capture and streaming loop"""
        while self.video_enabled and self.video_cap and self.connected:
            try:
                ret, frame = self.video_cap.read()
                if not ret:
                    break
                
                # Adaptive resize for local display
                original_height, original_width = frame.shape[:2]
                target_width = 200
                target_height = 150
                
                # Maintain aspect ratio
                aspect_ratio = original_width / original_height
                if aspect_ratio > (target_width / target_height):
                    new_width = target_width
                    new_height = int(target_width / aspect_ratio)
                else:
                    new_height = target_height
                    new_width = int(target_height * aspect_ratio)
                
                display_frame = cv2.resize(frame, (new_width, new_height))
                display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                
                # Update local video preview directly (NEW FEATURE - doesn't interfere with existing)
                self.update_local_video_preview(display_frame_rgb)
                
                # Send to server only if connected (existing functionality unchanged)
                if self.connected:
                    self.send_video_frame(frame)
                
                time.sleep(0.05)  # 20 FPS
                
            except Exception as e:
                print(f"Video loop error: {e}")
                break
    
    def update_local_video_preview(self, frame_rgb):
        """Update local video preview (NEW FEATURE - independent of main video system)"""
        try:
            # Only update if the your_video_label exists and meeting screen is active
            if (hasattr(self, 'your_video_label') and self.your_video_label and 
                hasattr(self.your_video_label, 'winfo_exists') and self.your_video_label.winfo_exists()):
                
                # Create photo from frame
                pil_image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(pil_image)
                
                # Update the local video preview
                self.your_video_label.configure(image=photo, text="")
                self.your_video_label.image = photo  # Keep reference
                
                # Debug: Uncomment to see local video updates
                # print("Local video preview updated")
                
        except Exception as e:
            # Silently handle errors to not interfere with main video functionality
            pass
    
    def clear_local_video_preview(self):
        """Clear local video preview when camera is turned off (NEW FEATURE)"""
        try:
            if (hasattr(self, 'your_video_label') and self.your_video_label and 
                hasattr(self.your_video_label, 'winfo_exists') and self.your_video_label.winfo_exists()):
                
                # Show camera off message
                self.your_video_label.configure(image="", text="📹 Camera Off")
                self.your_video_label.image = None  # Clear image reference
                
        except Exception as e:
            # Silently handle errors
            pass
    
    def prepare_local_video_preview(self):
        """Prepare local video preview when camera is turned on (NEW FEATURE)"""
        try:
            if (hasattr(self, 'your_video_label') and self.your_video_label and 
                hasattr(self.your_video_label, 'winfo_exists') and self.your_video_label.winfo_exists()):
                
                # Clear placeholder text - video will appear shortly
                self.your_video_label.configure(text="📹 Starting...", image="")
                self.your_video_label.image = None
                
        except Exception as e:
            # Silently handle errors
            pass
    
    def send_video_frame(self, frame):
        """Send video frame to server"""
        try:
            if hasattr(self, 'udp_video_socket') and self.connected and self.client_id is not None:
                # Adaptive resize for network transmission
                original_height, original_width = frame.shape[:2]
                target_width = self.video_settings['default_width'] // 2  # Half resolution for network
                target_height = self.video_settings['default_height'] // 2
                
                # Maintain aspect ratio
                aspect_ratio = original_width / original_height
                if aspect_ratio > (target_width / target_height):
                    new_width = target_width
                    new_height = int(target_width / aspect_ratio)
                else:
                    new_height = target_height
                    new_width = int(target_height * aspect_ratio)
                
                # Ensure minimum size for network transmission
                new_width = max(new_width, 160)
                new_height = max(new_height, 120)
                
                frame_resized = cv2.resize(frame, (new_width, new_height))
                
                # Adaptive quality based on frame size
                quality = max(20, min(60, self.video_settings['quality'] - 20))  # Lower quality for network
                _, encoded = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, quality])
                
                # Check packet size before sending (UDP has ~65KB limit, but we use much smaller)
                if len(encoded) > 8000:  # 8KB limit to ensure no UDP issues
                    # If still too large, reduce quality further
                    _, encoded = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 10])
                    if len(encoded) > 8000:
                        print(f"Frame still too large ({len(encoded)} bytes), skipping")
                        return
                
                # Create packet
                sequence = int(time.time() * 1000) % (2**32)
                packet = struct.pack('!III', self.client_id, sequence, len(encoded)) + encoded.tobytes()
                
                # Final packet size check
                if len(packet) > 65000:  # 65KB UDP limit
                    print(f"Packet too large ({len(packet)} bytes), skipping")
                    return
                
                # Send to server
                self.udp_video_socket.sendto(packet, (self.server_host, self.udp_video_port))
                # print(f"Video frame sent to server - Client ID: {self.client_id}, Size: {len(encoded)}")
                
        except Exception as e:
            print(f"Error sending video frame: {e}")
    
    def toggle_microphone(self):
        """Toggle microphone on/off"""
        if not self.microphone_enabled:
            self.start_microphone()
        else:
            self.stop_microphone()
            
    def toggle_speaker(self):
        """Toggle speaker on/off"""
        if not self.speaker_enabled:
            self.start_speaker()
        else:
            self.stop_speaker()
            
    def toggle_audio(self):
        """Legacy method for compatibility - toggles microphone"""
        self.toggle_microphone()
            
    def start_microphone(self):
        """Start microphone capture and streaming"""
        try:
            if not hasattr(self, 'audio') or not self.audio:
                self.audio = pyaudio.PyAudio()
            
            # Audio configuration
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = 44100
            
            # Input stream for microphone
            self.audio_stream = self.audio.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk
            )
            
            self.microphone_enabled = True
            self.audio_enabled = True  # For compatibility
            self.mic_btn.config(text="🎤\nMic On", bg='#28a745')
            
            # Start audio streaming thread
            threading.Thread(target=self.audio_stream_loop, daemon=True).start()
            
            # Notify server
            self.send_media_status_update()
            
        except Exception as e:
            messagebox.showerror("Microphone Error", f"Failed to start microphone: {str(e)}")
            
    def start_speaker(self):
        """Start speaker for playing received audio"""
        try:
            if not hasattr(self, 'audio') or not self.audio:
                self.audio = pyaudio.PyAudio()
            
            # Audio configuration
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = 44100
            
            # Output stream for playing received audio
            self.audio_output_stream = self.audio.open(
                format=format,
                channels=channels,
                rate=rate,
                output=True,
                frames_per_buffer=chunk
            )
            
            self.speaker_enabled = True
            self.speaker_btn.config(text="🔊\nSpeaker On", bg='#28a745')
            
        except Exception as e:
            messagebox.showerror("Speaker Error", f"Failed to start speaker: {str(e)}")
            
    def start_audio(self):
        """Legacy method for compatibility - starts both mic and speaker"""
        self.start_microphone()
        if not self.speaker_enabled:
            self.start_speaker()
            
    def stop_microphone(self):
        """Stop microphone capture and streaming"""
        self.microphone_enabled = False
        self.mic_btn.config(text="🎤\nMic", bg='#404040')
        
        if hasattr(self, 'audio_stream') and self.audio_stream:
            try:
                if self.audio_stream.is_active():
                    self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception as e:
                print(f"Error stopping microphone stream: {e}")
            finally:
                self.audio_stream = None
        
        # Update compatibility flag
        self.audio_enabled = self.microphone_enabled
        
        # Notify server
        self.send_media_status_update()
        
    def stop_speaker(self):
        """Stop speaker output"""
        self.speaker_enabled = False
        self.speaker_btn.config(text="🔊\nSpeaker", bg='#404040')
        
        if hasattr(self, 'audio_output_stream') and self.audio_output_stream:
            try:
                if self.audio_output_stream.is_active():
                    self.audio_output_stream.stop_stream()
                self.audio_output_stream.close()
            except Exception as e:
                print(f"Error stopping speaker stream: {e}")
            finally:
                self.audio_output_stream = None
                
    def stop_audio(self):
        """Legacy method for compatibility - stops both mic and speaker"""
        self.stop_microphone()
        self.stop_speaker()
        
        # Clean up PyAudio if both are stopped
        if not self.microphone_enabled and not self.speaker_enabled:
            if hasattr(self, 'audio') and self.audio:
                try:
                    self.audio.terminate()
                except Exception as e:
                    print(f"Error terminating PyAudio: {e}")
                finally:
                    self.audio = None
        
    def audio_stream_loop(self):
        """Audio streaming loop with error handling"""
        consecutive_errors = 0
        max_errors = 5
        
        while self.microphone_enabled and self.audio_stream and self.connected:
            try:
                # Check if stream is still active
                if not self.audio_stream.is_active():
                    print("Audio stream is not active, stopping loop")
                    break
                
                # Read audio data with exception handling for overflow
                try:
                    data = self.audio_stream.read(1024, exception_on_overflow=False)
                except Exception as read_error:
                    if "Input overflowed" in str(read_error):
                        # Handle input overflow by clearing buffer and continuing
                        print("Audio input overflow, clearing buffer...")
                        try:
                            # Try to read and discard overflow data
                            self.audio_stream.read(1024, exception_on_overflow=False)
                        except:
                            pass
                        time.sleep(0.1)  # Brief pause to let buffer clear
                        continue
                    else:
                        raise read_error
                
                # Send audio to server via UDP
                if hasattr(self, 'udp_audio_socket') and self.connected and self.client_id is not None:
                    try:
                        # Create audio packet
                        timestamp = int(time.time() * 1000) % (2**32)
                        packet = struct.pack('!II', self.client_id, timestamp) + data
                        
                        # Send to server
                        self.udp_audio_socket.sendto(packet, (self.server_host, self.udp_audio_port))
                        # Debug: Uncomment to see audio being sent
                        # print(f"Audio sent: Client {self.client_id}, {len(data)} bytes")
                        
                        # Reset error counter on successful operation
                        consecutive_errors = 0
                        
                    except Exception as e:
                        print(f"Error sending audio: {e}")
                        consecutive_errors += 1
                
                time.sleep(0.02)  # Small delay to prevent overwhelming
                
            except Exception as e:
                consecutive_errors += 1
                print(f"Audio streaming error ({consecutive_errors}/{max_errors}): {e}")
                
                # If too many consecutive errors, stop the loop
                if consecutive_errors >= max_errors:
                    print("Too many audio errors, stopping audio stream")
                    self.root.after(0, self.stop_audio)
                    break
                    
                time.sleep(0.1)  # Brief pause before retrying
    
    def send_media_status_update(self):
        """Send media status update to server using enhanced protocol"""
        if self.connected:
            # Use enhanced protocol message creation
            status_msg = create_media_status_update(
                self.video_enabled,
                self.microphone_enabled,  # Use microphone_enabled instead of audio_enabled
                getattr(self, 'screen_sharing', False)
            )
            self.send_tcp_message(status_msg)
                
    def toggle_presentation(self):
        """Toggle presentation mode"""
        if not self.is_presenter:
            # Request presenter role
            request_msg = {'type': 'request_presenter'}
            self.send_tcp_message(request_msg)
        else:
            # Stop presenting
            self.stop_screen_sharing()
            
    def start_screen_sharing(self):
        """Start screen sharing"""
        if not MSS_AVAILABLE:
            messagebox.showerror("Screen Share Error", "Screen sharing not available. Please install 'mss' package.")
            return
            
        try:
            self.screen_sharing = True
            self.present_btn.config(text="🖥️\nSharing", bg='#fd7e14')
            
            # Ensure all buttons remain visible and responsive
            self.ensure_buttons_visible()
            
            # Start screen sharing thread
            threading.Thread(target=self.screen_sharing_loop, daemon=True).start()
            
            # Start GUI responsiveness monitor
            self.start_gui_monitor()
            
            # Notify server
            self.send_media_status_update()
            
        except Exception as e:
            messagebox.showerror("Screen Share Error", f"Failed to start screen sharing: {str(e)}")
            
    def stop_screen_sharing(self):
        """Stop screen sharing"""
        self.screen_sharing = False
        self.is_presenter = False
        self.present_btn.config(text="🖥️\nPresent", bg='#404040')
        
        # Notify server
        stop_msg = {'type': 'stop_presenting'}
        self.send_tcp_message(stop_msg)
        self.send_media_status_update()
        
    def ensure_buttons_visible(self):
        """Ensure all buttons remain visible and responsive"""
        try:
            # Force update all button states to ensure visibility
            if hasattr(self, 'video_btn') and self.video_btn:
                self.video_btn.update_idletasks()
            if hasattr(self, 'mic_btn') and self.mic_btn:
                self.mic_btn.update_idletasks()
            if hasattr(self, 'speaker_btn') and self.speaker_btn:
                self.speaker_btn.update_idletasks()
            if hasattr(self, 'present_btn') and self.present_btn:
                self.present_btn.update_idletasks()
            if hasattr(self, 'leave_btn') and self.leave_btn:
                self.leave_btn.update_idletasks()
            if hasattr(self, 'share_file_btn') and self.share_file_btn:
                self.share_file_btn.update_idletasks()
            if hasattr(self, 'download_file_btn') and self.download_file_btn:
                self.download_file_btn.update_idletasks()
            if hasattr(self, 'file_manager_btn') and self.file_manager_btn:
                self.file_manager_btn.update_idletasks()
        except Exception as e:
            print(f"Error ensuring button visibility: {e}")
    
    def cn_view_presentation(self, viewer_port, presenter_name):
        """CN_project style presentation viewing - Threading version"""
        try:
            import socket
            import struct
            from PIL import Image as PILImage
            from io import BytesIO
            
            print(f"[CN_VIEWER] Connecting to presentation on port {viewer_port}")
            
            # Wait a moment for server to be ready
            time.sleep(0.5)
            
            # Connect to viewer port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # 10 second timeout for connection
            
            try:
                sock.connect(('localhost', viewer_port))
            except Exception as e:
                print(f"[CN_VIEWER] Failed to connect to port {viewer_port}: {e}")
                self.root.after(0, lambda: self.add_chat_message("System", f"Failed to connect to presentation: {str(e)}"))
                return
            
            print(f"[CN_VIEWER] Connected! Viewing {presenter_name}'s screen...")
            self.root.after(0, lambda: self.add_chat_message("System", f"Now viewing {presenter_name}'s screen"))
            
            frame_count = 0
            sock.settimeout(5)  # 5 second timeout for frame reception
            
            while self.current_presentation and self.connected:
                try:
                    # Read 4-byte frame length header
                    length_data = b''
                    while len(length_data) < 4:
                        try:
                            chunk = sock.recv(4 - len(length_data))
                            if not chunk:
                                raise ConnectionError("Connection closed by server")
                            length_data += chunk
                        except socket.timeout:
                            # Check if presentation is still active
                            if not self.current_presentation:
                                break
                            continue
                    
                    if len(length_data) < 4:
                        break
                        
                    frame_length = struct.unpack('!I', length_data)[0]
                    
                    # Validate frame length
                    if frame_length > 10 * 1024 * 1024:  # 10MB max frame size
                        print(f"[CN_VIEWER] Invalid frame length: {frame_length}")
                        break
                    
                    # Read frame data
                    frame_data = b''
                    while len(frame_data) < frame_length:
                        try:
                            chunk = sock.recv(min(8192, frame_length - len(frame_data)))
                            if not chunk:
                                raise ConnectionError("Connection closed by server")
                            frame_data += chunk
                        except socket.timeout:
                            if not self.current_presentation:
                                break
                            continue
                    
                    if len(frame_data) < frame_length:
                        break
                    
                    frame_count += 1
                    
                    # Decode and display frame
                    try:
                        img = PILImage.open(BytesIO(frame_data))
                        
                        # Convert to PhotoImage for display
                        display_photo = ImageTk.PhotoImage(img)
                        
                        # Update screen display in main thread
                        self.root.after_idle(lambda photo=display_photo: self.update_cn_screen_display(photo))
                        
                        # Log every 30 frames
                        if frame_count % 30 == 0:
                            frame_size_kb = len(frame_data) / 1024
                            print(f"[CN_VIEWER] Frames: {frame_count}, Size: {frame_size_kb:.1f} KB")
                    
                    except Exception as decode_error:
                        print(f"[CN_VIEWER] Frame decode error: {decode_error}")
                        continue
                
                except socket.timeout:
                    # Timeout is normal, just continue if presentation is still active
                    if not self.current_presentation:
                        break
                    continue
                except ConnectionError as e:
                    print(f"[CN_VIEWER] Connection error: {e}")
                    break
                except Exception as e:
                    print(f"[CN_VIEWER] Frame receive error: {e}")
                    continue
            
            try:
                sock.close()
            except:
                pass
            print(f"[CN_VIEWER] Viewing stopped. Total frames: {frame_count}")
            
        except Exception as e:
            print(f"[CN_VIEWER] Failed to view presentation: {e}")
            self.root.after(0, lambda: self.add_chat_message("System", f"Failed to view presentation: {str(e)}"))
    
    def update_cn_screen_display(self, photo):
        """Update CN_project style screen display"""
        try:
            if hasattr(self, 'screen_display') and self.screen_display:
                self.screen_display.config(image=photo)
                self.screen_display.image = photo  # Keep a reference
            elif hasattr(self, 'video_display') and self.video_display:
                # Fallback to video display if screen display not available
                self.video_display.config(image=photo)
                self.video_display.image = photo
        except Exception as e:
            print(f"Error updating CN screen display: {e}")
            
    def start_gui_monitor(self):
        """Start GUI responsiveness monitor during screen sharing"""
        def monitor_gui():
            while self.screen_sharing and self.connected:
                try:
                    # Ensure GUI remains responsive
                    if hasattr(self, 'root') and self.root:
                        self.root.update_idletasks()
                        self.ensure_buttons_visible()
                    time.sleep(1.0)  # Check every second
                except Exception as e:
                    print(f"GUI monitor error: {e}")
                    break
                    
        # Start monitor thread
        monitor_thread = threading.Thread(target=monitor_gui, daemon=True)
        monitor_thread.start()
        
    def screen_sharing_loop(self):
        """Screen sharing capture and transmission loop"""
        while self.screen_sharing and self.connected:
            try:
                # Capture screen
                if MSS_AVAILABLE:
                    with mss.mss() as sct:
                        # Capture primary monitor
                        monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                        screenshot = sct.grab(monitor)
                        
                        # Convert to PIL Image
                        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                        
                        # Resize for transmission
                        img.thumbnail((1024, 768), Image.Resampling.LANCZOS)
                        
                        # Convert to numpy array
                        frame_rgb = np.array(img)
                        
                        # Put frame in queue for transmission
                        try:
                            # Clear old frames if queue is full
                            while self.screen_frame_queue.qsize() > 1:
                                try:
                                    self.screen_frame_queue.get_nowait()
                                except queue.Empty:
                                    break
                            self.screen_frame_queue.put_nowait(frame_rgb)
                        except queue.Full:
                            pass
                        
                        # Send to server via TCP
                        self.send_screen_frame(frame_rgb)
                        
                        # Ensure GUI remains responsive during screen sharing
                        try:
                            if hasattr(self, 'root') and self.root:
                                self.root.update_idletasks()
                        except:
                            pass
                        
                time.sleep(0.2)  # Reduced to 5 FPS for better GUI responsiveness
                
            except Exception as e:
                print(f"Screen sharing error: {e}")
                break
                
    def send_screen_frame(self, frame):
        """Send screen frame to server via TCP"""
        try:
            if self.connected and self.client_id is not None:
                # Compress frame
                img = Image.fromarray(frame)
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=60)
                frame_data = buffer.getvalue()
                
                # Create screen frame message
                screen_msg = {
                    'type': 'screen_frame',
                    'client_id': self.client_id,
                    'frame_data': base64.b64encode(frame_data).decode('utf-8')
                }
                
                self.send_tcp_message(screen_msg)
                
        except Exception as e:
            print(f"Error sending screen frame: {e}")
            
    def handle_force_mute(self):
        """Handle force mute command from server"""
        if self.microphone_enabled:
            self.stop_microphone()
            messagebox.showwarning("Host Action", "Your microphone has been muted by the host")
            self.add_chat_message("System", "You have been muted by the host")
            
    def handle_force_disable_video(self):
        """Handle force disable video command from server"""
        if self.video_enabled:
            self.stop_video()
            messagebox.showwarning("Host Action", "Your video has been disabled by the host")
            self.add_chat_message("System", "Your video has been disabled by the host")
            
    def handle_force_stop_presenting(self):
        """Handle force stop presenting command from server"""
        if self.is_presenter or self.screen_sharing:
            self.stop_screen_sharing()
            messagebox.showwarning("Host Action", "Your presentation has been stopped by the host")
            self.add_chat_message("System", "Your presentation has been stopped by the host")
            
    def handle_force_stop_screen_sharing(self):
        """Handle force stop screen sharing command from server"""
        if self.screen_sharing:
            self.stop_screen_sharing()
            messagebox.showwarning("Host Action", "Your screen sharing has been stopped by the host")
            self.add_chat_message("System", "Your screen sharing has been stopped by the host")
            
    def handle_host_request(self, request_type, message):
        """Handle host request for audio/video"""
        response = messagebox.askyesno("Host Request", message + "\n\nWould you like to comply?")
        
        if response:
            if request_type == 'audio' and not self.microphone_enabled:
                self.toggle_microphone()
                self.add_chat_message("System", "You enabled your microphone at host's request")
            elif request_type == 'video' and not self.video_enabled:
                self.toggle_video()
                self.add_chat_message("System", "You enabled your camera at host's request")
        else:
            self.add_chat_message("System", f"You declined the host's {request_type} request")
            
    def send_chat_message(self, event=None):
        """Send chat message using enhanced protocol with unicast/broadcast support"""
        message = self.chat_entry.get().strip()
        if not message or not self.connected:
            return
            
        msg_type = self.message_type.get()
        
        try:
            if msg_type == "chat":
                # Regular public chat
                chat_msg = create_chat_message(message)
                success = self.send_tcp_message(chat_msg)
                display_prefix = ""
                
            elif msg_type == "broadcast":
                # Broadcast message
                broadcast_msg = {
                    'type': MessageTypes.BROADCAST,
                    'text': message,
                    'timestamp': datetime.now().isoformat()
                }
                success = self.send_tcp_message(broadcast_msg)
                display_prefix = "[BROADCAST] "
                
            elif msg_type == "unicast":
                # Private message
                target_text = self.target_var.get()
                if not target_text:
                    messagebox.showwarning("No Target", "Please select a recipient for private message.")
                    return
                    
                # Parse target
                if target_text == "Host":
                    target_uid = 0  # Host ID
                else:
                    # Extract ID from "Name (ID: X)" format
                    try:
                        target_uid = int(target_text.split("ID: ")[1].rstrip(")"))
                    except (IndexError, ValueError):
                        messagebox.showerror("Invalid Target", "Could not parse target user ID.")
                        return
                
                unicast_msg = {
                    'type': MessageTypes.UNICAST,
                    'target_uid': target_uid,
                    'text': message,
                    'timestamp': datetime.now().isoformat()
                }
                success = self.send_tcp_message(unicast_msg)
                display_prefix = f"[PRIVATE to {target_text}] "
                
            else:
                messagebox.showerror("Invalid Type", "Unknown message type selected.")
                return
            
            if success:
                self.chat_entry.delete(0, tk.END)
                # Add to local display with appropriate prefix
                self.add_chat_message("You", f"{display_prefix}{message}")
            else:
                messagebox.showerror("Send Failed", "Failed to send message. Connection may be lost.")
                
        except Exception as e:
            messagebox.showerror("Send Error", f"Error sending message: {str(e)}")
            
    def add_chat_message(self, sender, message):
        """Add message to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        
        # Add sender icon
        sender_icon = "🏠" if sender == "Host" else "👤"
        if sender == "System":
            sender_icon = "ℹ️"
        elif sender == "You":
            sender_icon = "👤"
            
        chat_line = f"{sender_icon} {sender} • {timestamp}\n{message}\n\n"
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, chat_line)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def update_chat_display(self):
        """Update chat display with history"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        
        for msg in self.chat_history:
            timestamp = msg.get('timestamp', '')
            sender = msg.get('name', 'Unknown')
            message = msg.get('message', '')
            
            if timestamp:
                try:
                    time_obj = datetime.fromisoformat(timestamp)
                    time_str = time_obj.strftime("%H:%M")
                except:
                    time_str = "??:??"
            else:
                time_str = "??:??"
            
            # Add sender icon
            sender_icon = "🏠" if sender == "Host" else "👤"
            if sender == "System":
                sender_icon = "ℹ️"
                
            chat_line = f"{sender_icon} {sender} • {time_str}\n{message}\n\n"
            self.chat_display.insert(tk.END, chat_line)
            
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def update_participants_list(self):
        """Update participants list and target selection"""
        self.participants_listbox.delete(0, tk.END)
        
        # Sort participants with Host first
        sorted_participants = sorted(self.clients_list.items(), 
                                   key=lambda x: (int(x[0]) != getattr(self, 'host_id', 0), int(x[0])))
        
        for client_id, client_info in sorted_participants:
            name = client_info.get('name', f'Client_{client_id}')
            
            # Add status indicators
            status_icons = []
            if client_info.get('video_enabled'):
                status_icons.append("📹")
            if client_info.get('audio_enabled'):
                status_icons.append("🎤")
            if status_icons:
                name += f" {' '.join(status_icons)}"
            
            if client_id == str(self.client_id):
                name += " (You)"
            elif client_id == str(getattr(self, 'host_id', 0)):
                name = f"🏠 {name}"  # Host indicator
            if client_id == str(self.presenter_id):
                name += " [Presenter]"
                
            self.participants_listbox.insert(tk.END, name)
        
        # Update participant count
        if hasattr(self, 'participant_count_label'):
            self.participant_count_label.config(text=str(len(self.clients_list)))
            
        # Update target list for private messages if visible
        if hasattr(self, 'target_frame') and self.target_frame.winfo_viewable():
            self.update_target_list()
        
        # Update participant count
        total_participants = len(self.clients_list)
        self.participant_count_label.config(text=str(total_participants))
        
    def update_shared_files_list(self):
        """Update shared files list"""
        if hasattr(self, 'shared_files_listbox'):
            self.shared_files_listbox.delete(0, tk.END)
            
            for file_name, file_info in self.shared_files.items():
                size_mb = f"{file_info['size'] / (1024*1024):.2f} MB"
                shared_by = file_info.get('shared_by', 'Unknown')
                display_text = f"{file_name} ({size_mb}) - {shared_by}"
                self.shared_files_listbox.insert(tk.END, display_text)
                
    def share_file(self):
        """Share a file with the group"""
        try:
            filename = filedialog.askopenfilename(
                title="Select file to share",
                filetypes=[("All files", "*.*")]
            )
            
            if filename:
                file_info = {
                    'name': os.path.basename(filename),
                    'size': os.path.getsize(filename),
                    'shared_by': self.client_name,
                    'share_time': datetime.now().isoformat(),
                    'downloads': 0,
                    'path': filename
                }
                
                # Send file info to server
                share_msg = {
                    'type': 'share_file',
                    'file_info': file_info
                }
                self.send_tcp_message(share_msg)
                
                # Add to local list
                self.shared_files[file_info['name']] = file_info
                self.update_shared_files_list()
                
                self.add_chat_message("You", f"Shared file: {file_info['name']}")
                
        except Exception as e:
            messagebox.showerror("File Share Error", f"Failed to share file: {str(e)}")
            
    def download_selected_file(self):
        """Download selected file"""
        selection = self.shared_files_listbox.curselection()
        if selection:
            file_name = list(self.shared_files.keys())[selection[0]]
            file_info = self.shared_files[file_name]
            
            try:
                # Open file dialog to choose download location
                download_path = filedialog.asksaveasfilename(
                    initialfile=file_name,
                    title="Save File As"
                )
                
                if download_path:
                    # Copy file to chosen location
                    import shutil
                    shutil.copy2(file_info['path'], download_path)
                    
                    # Notify server about download
                    download_msg = {
                        'type': 'file_downloaded',
                        'file_name': file_name
                    }
                    self.send_tcp_message(download_msg)
                    
                    self.add_chat_message("You", f"Downloaded: {file_name}")
                    messagebox.showinfo("Download Complete", f"File saved to {download_path}")
                    
            except Exception as e:
                messagebox.showerror("Download Error", f"Failed to download file: {str(e)}")
        else:
            messagebox.showwarning("No Selection", "Please select a file first")
            
    def open_file_manager(self):
        """Open dedicated file management interface"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to a meeting first")
            return
            
        # Create file manager window
        file_manager_window = tk.Toplevel(self.root)
        file_manager_window.title("File Manager - Upload & Download")
        file_manager_window.geometry("800x600")
        file_manager_window.configure(bg='#2d2d2d')
        file_manager_window.transient(self.root)
        file_manager_window.grab_set()
        
        # Header
        header_frame = tk.Frame(file_manager_window, bg='#1e1e1e', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📁 File Manager", 
                font=('Segoe UI', 18, 'bold'), 
                fg='white', bg='#1e1e1e').pack(pady=15)
        
        # Main content
        main_frame = tk.Frame(file_manager_window, bg='#2d2d2d')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Upload section
        upload_frame = tk.LabelFrame(main_frame, text="📤 Upload Files", 
                                    bg='#2d2d2d', fg='white',
                                    font=('Segoe UI', 14, 'bold'))
        upload_frame.pack(fill=tk.X, pady=(0, 20))
        
        upload_inner = tk.Frame(upload_frame, bg='#2d2d2d')
        upload_inner.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(upload_inner, text="Share files with all meeting participants", 
                font=('Segoe UI', 11), 
                fg='#cccccc', bg='#2d2d2d').pack(anchor=tk.W, pady=(0, 15))
        
        upload_buttons_frame = tk.Frame(upload_inner, bg='#2d2d2d')
        upload_buttons_frame.pack(fill=tk.X)
        
        tk.Button(upload_buttons_frame, text="📤 Select & Upload File", 
                 command=self.share_file,
                 bg='#0078d4', fg='white', 
                 font=('Segoe UI', 12, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=25, pady=12,
                 cursor='hand2').pack(side=tk.LEFT)
        
        tk.Button(upload_buttons_frame, text="📁 Upload Multiple Files", 
                 command=self.upload_multiple_files,
                 bg='#6c757d', fg='white', 
                 font=('Segoe UI', 12, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=25, pady=12,
                 cursor='hand2').pack(side=tk.LEFT, padx=(15, 0))
        
        # Download section
        download_frame = tk.LabelFrame(main_frame, text="📥 Available Files", 
                                      bg='#2d2d2d', fg='white',
                                      font=('Segoe UI', 14, 'bold'))
        download_frame.pack(fill=tk.BOTH, expand=True)
        
        download_inner = tk.Frame(download_frame, bg='#2d2d2d')
        download_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(download_inner, text="Files shared by meeting participants", 
                font=('Segoe UI', 11), 
                fg='#cccccc', bg='#2d2d2d').pack(anchor=tk.W, pady=(0, 15))
        
        # Files list with details
        files_list_frame = tk.Frame(download_inner, bg='#2d2d2d')
        files_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create treeview for better file display
        columns = ('Name', 'Size', 'Shared By', 'Time')
        self.files_tree = ttk.Treeview(files_list_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        self.files_tree.heading('Name', text='File Name')
        self.files_tree.heading('Size', text='Size')
        self.files_tree.heading('Shared By', text='Shared By')
        self.files_tree.heading('Time', text='Share Time')
        
        self.files_tree.column('Name', width=250)
        self.files_tree.column('Size', width=100)
        self.files_tree.column('Shared By', width=120)
        self.files_tree.column('Time', width=120)
        
        # Scrollbar for treeview
        files_scrollbar = ttk.Scrollbar(files_list_frame, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_scrollbar.set)
        
        self.files_tree.pack(side="left", fill="both", expand=True)
        files_scrollbar.pack(side="right", fill="y")
        
        # Download controls
        download_controls_frame = tk.Frame(download_inner, bg='#2d2d2d')
        download_controls_frame.pack(fill=tk.X)
        
        tk.Button(download_controls_frame, text="📥 Download Selected", 
                 command=lambda: self.download_from_tree(self.files_tree),
                 bg='#107c10', fg='white', 
                 font=('Segoe UI', 12, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=25, pady=12,
                 cursor='hand2').pack(side=tk.LEFT)
        
        tk.Button(download_controls_frame, text="📥 Download All", 
                 command=self.download_all_files,
                 bg='#28a745', fg='white', 
                 font=('Segoe UI', 12, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=25, pady=12,
                 cursor='hand2').pack(side=tk.LEFT, padx=(15, 0))
        
        tk.Button(download_controls_frame, text="🔄 Refresh List", 
                 command=lambda: self.update_file_manager_list(self.files_tree),
                 bg='#6c757d', fg='white', 
                 font=('Segoe UI', 12, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=25, pady=12,
                 cursor='hand2').pack(side=tk.RIGHT)
        
        # Populate the files list
        self.update_file_manager_list(self.files_tree)
        
    def upload_multiple_files(self):
        """Upload multiple files at once"""
        try:
            filenames = filedialog.askopenfilenames(
                title="Select files to share",
                filetypes=[("All files", "*.*")]
            )
            
            if filenames:
                success_count = 0
                for filename in filenames:
                    try:
                        # Get file info
                        file_size = os.path.getsize(filename)
                        file_name = os.path.basename(filename)
                        
                        # Create file info
                        file_info = {
                            'name': file_name,
                            'size': file_size,
                            'path': filename,
                            'shared_by': self.client_name,
                            'share_time': datetime.now().isoformat()
                        }
                        
                        # Send to server
                        share_msg = {
                            'type': 'file_share',
                            'client_id': self.client_id,
                            'file_info': file_info
                        }
                        self.send_tcp_message(share_msg)
                        success_count += 1
                        
                    except Exception as e:
                        print(f"Error sharing file {filename}: {e}")
                        
                messagebox.showinfo("Upload Complete", f"Successfully shared {success_count} out of {len(filenames)} files")
                
        except Exception as e:
            messagebox.showerror("Upload Error", f"Failed to upload files: {str(e)}")
            
    def download_from_tree(self, tree):
        """Download selected file from tree view"""
        selection = tree.selection()
        if selection:
            item = tree.item(selection[0])
            file_name = item['values'][0]
            
            if file_name in self.shared_files:
                file_info = self.shared_files[file_name]
                
                try:
                    # Open file dialog to choose download location
                    download_path = filedialog.asksaveasfilename(
                        initialfile=file_name,
                        title="Save file as",
                        filetypes=[("All files", "*.*")]
                    )
                    
                    if download_path:
                        # Copy file to chosen location
                        import shutil
                        shutil.copy2(file_info['path'], download_path)
                        
                        # Notify server about download
                        download_msg = {
                            'type': 'file_downloaded',
                            'client_id': self.client_id,
                            'file_name': file_name
                        }
                        self.send_tcp_message(download_msg)
                        
                        self.add_chat_message("You", f"Downloaded: {file_name}")
                        messagebox.showinfo("Download Complete", f"File saved to {download_path}")
                        
                except Exception as e:
                    messagebox.showerror("Download Error", f"Failed to download file: {str(e)}")
        else:
            messagebox.showwarning("No Selection", "Please select a file first")
            
    def download_all_files(self):
        """Download all available files"""
        if not self.shared_files:
            messagebox.showinfo("No Files", "No files available for download")
            return
            
        # Choose download directory
        download_dir = filedialog.askdirectory(title="Choose download directory")
        if not download_dir:
            return
            
        success_count = 0
        for file_name, file_info in self.shared_files.items():
            try:
                import shutil
                download_path = os.path.join(download_dir, file_name)
                shutil.copy2(file_info['path'], download_path)
                
                # Notify server about download
                download_msg = {
                    'type': 'file_downloaded',
                    'client_id': self.client_id,
                    'file_name': file_name
                }
                self.send_tcp_message(download_msg)
                success_count += 1
                
            except Exception as e:
                print(f"Error downloading {file_name}: {e}")
                
        messagebox.showinfo("Download Complete", f"Downloaded {success_count} out of {len(self.shared_files)} files to {download_dir}")
        self.add_chat_message("You", f"Downloaded {success_count} files")
        
    def update_file_manager_list(self, tree):
        """Update the file manager list"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Add files
        for file_name, file_info in self.shared_files.items():
            size_mb = f"{file_info['size'] / (1024*1024):.2f} MB"
            shared_by = file_info.get('shared_by', 'Unknown')
            share_time = file_info.get('share_time', '')
            
            if share_time:
                try:
                    share_time = datetime.fromisoformat(share_time).strftime("%H:%M:%S")
                except:
                    share_time = "Unknown"
            
            tree.insert('', 'end', values=(file_name, size_mb, shared_by, share_time))
            
    def handle_connection_lost(self):
        """Handle lost connection to server"""
        if not self.connected:
            return  # Already handled
            
        print("Connection to server lost")
        
        # Update meeting status if in meeting
        if hasattr(self, 'meeting_status'):
            self.meeting_status.config(text="● Connection Lost", fg='#dc3545')
        
        # Show reconnection dialog
        response = messagebox.askyesno("Connection Lost", 
                                     "Connection to the server was lost.\n\n"
                                     "Would you like to return to the connection screen?")
        
        if response:
            self.disconnect()
        else:
            # Try to reconnect automatically
            self.attempt_reconnection()
    
    def attempt_reconnection(self):
        """Attempt to reconnect to the server"""
        try:
            print("Attempting to reconnect...")
            
            # Update status
            if hasattr(self, 'meeting_status'):
                self.meeting_status.config(text="● Reconnecting...", fg='#ffd43b')
            
            # Close existing sockets
            self.cleanup_sockets()
            
            # Try to reconnect
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(10)
            self.tcp_socket.connect((self.server_host, self.tcp_port))
            
            # Recreate UDP sockets
            self.udp_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_video_socket.bind(('', self.udp_video_port))
            self.udp_audio_socket.bind(('', self.udp_audio_port))
            
            # Restart communication threads
            threading.Thread(target=self.tcp_receiver, daemon=True).start()
            threading.Thread(target=self.udp_video_receiver, daemon=True).start()
            threading.Thread(target=self.udp_audio_receiver, daemon=True).start()
            
            # Rejoin the session
            join_msg = {
                'type': 'join',
                'name': self.client_name
            }
            self.send_tcp_message(join_msg)
            
            # Update status
            if hasattr(self, 'meeting_status'):
                self.meeting_status.config(text="● Reconnected", fg='#51cf66')
            
            print("Reconnection successful")
            
        except Exception as e:
            print(f"Reconnection failed: {e}")
            if hasattr(self, 'meeting_status'):
                self.meeting_status.config(text="● Reconnection Failed", fg='#dc3545')
            
            # Show error and disconnect
            messagebox.showerror("Reconnection Failed", 
                               f"Could not reconnect to server: {str(e)}\n\n"
                               "Returning to connection screen.")
            self.disconnect()
    
    def cleanup_sockets(self):
        """Clean up existing sockets"""
        try:
            if hasattr(self, 'tcp_socket') and self.tcp_socket:
                self.tcp_socket.close()
                self.tcp_socket = None
        except:
            pass
            
        try:
            if hasattr(self, 'udp_video_socket') and self.udp_video_socket:
                self.udp_video_socket.close()
                self.udp_video_socket = None
        except:
            pass
            
        try:
            if hasattr(self, 'udp_audio_socket') and self.udp_audio_socket:
                self.udp_audio_socket.close()
                self.udp_audio_socket = None
        except:
            pass

    def disconnect(self):
        """Disconnect from server with proper cleanup and enhanced protocol"""
        if self.connected:
            # Send logout message using enhanced protocol
            try:
                logout_msg = create_logout_message()
                self.send_tcp_message(logout_msg)
                time.sleep(0.5)  # Give server time to process logout
            except Exception as e:
                print(f"Error sending logout message: {e}")
        
        self.running = False
        self.connected = False
        
        # Stop media with error handling
        try:
            if self.video_enabled:
                self.stop_video()
        except Exception as e:
            print(f"Error stopping video during disconnect: {e}")
            
        try:
            if self.microphone_enabled or self.speaker_enabled:
                self.stop_audio()  # This will stop both mic and speaker
        except Exception as e:
            print(f"Error stopping audio during disconnect: {e}")
            
        # Close sockets with individual error handling
        self.cleanup_sockets()
            
        # Show connection screen
        try:
            self.show_connection_screen()
        except Exception as e:
            print(f"Error showing connection screen: {e}")
        
    def on_closing(self):
        """Handle window closing"""
        if self.connected:
            self.disconnect()
        self.root.destroy()
        
    def run(self):
        """Run the client application"""
        self.root.mainloop()

# Main execution
if __name__ == "__main__":
    client = LANCommunicationClient()
    client.run()
