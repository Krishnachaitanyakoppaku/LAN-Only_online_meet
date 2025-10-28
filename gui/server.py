#!/usr/bin/env python3
"""
LAN Communication Server - Enhanced Version
A comprehensive multi-user communication system for LAN environments

Features:
- Multi-user video conferencing (UDP)
- Multi-user audio conferencing (UDP) 
- Screen/slide sharing (TCP)
- Group text chat (TCP)
- File sharing (TCP)
- Session management
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
import io
import base64
import asyncio
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import queue
import cv2
import pyaudio
from PIL import Image, ImageTk
import numpy as np
import hashlib
import uuid

# Optional imports
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    print("Warning: mss module not available. Screen sharing will be disabled.")

# Protocol constants (inspired by CN_project)
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
DEFAULT_HOST = '0.0.0.0'
DEFAULT_TCP_PORT = 8888
DEFAULT_UDP_VIDEO_PORT = 8889
DEFAULT_UDP_AUDIO_PORT = 8890
CHUNK_SIZE = 8192
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
HEARTBEAT_INTERVAL = 10  # seconds
MAX_RETRY_ATTEMPTS = 3

# Protocol helper functions (inspired by CN_project)
def create_login_success_message(uid: int, username: str) -> dict:
    """Create a login success message."""
    return {
        "type": MessageTypes.LOGIN_SUCCESS,
        "uid": uid,
        "username": username,
        "timestamp": datetime.now().isoformat()
    }

def create_participant_list_message(participants: list) -> dict:
    """Create a participant list message."""
    return {
        "type": MessageTypes.PARTICIPANT_LIST,
        "participants": participants,
        "timestamp": datetime.now().isoformat()
    }

def create_user_joined_message(uid: int, username: str) -> dict:
    """Create a user joined message."""
    return {
        "type": MessageTypes.USER_JOINED,
        "uid": uid,
        "username": username,
        "timestamp": datetime.now().isoformat()
    }

def create_user_left_message(uid: int, username: str) -> dict:
    """Create a user left message."""
    return {
        "type": MessageTypes.USER_LEFT,
        "uid": uid,
        "username": username,
        "timestamp": datetime.now().isoformat()
    }

def create_chat_message(uid: int, username: str, text: str) -> dict:
    """Create a chat message."""
    return {
        "type": MessageTypes.CHAT,
        "uid": uid,
        "username": username,
        "text": text,
        "timestamp": datetime.now().isoformat()
    }

def create_error_message(message: str) -> dict:
    """Create an error message."""
    return {
        "type": MessageTypes.ERROR,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

def create_heartbeat_ack_message() -> dict:
    """Create a heartbeat acknowledgment message."""
    return {
        "type": MessageTypes.HEARTBEAT_ACK,
        "timestamp": datetime.now().isoformat()
    }

class LANCommunicationServer:
    def __init__(self):
        # Network configuration
        self.host = '0.0.0.0'
        self.tcp_port = 8888  # Main TCP port for control, chat, files
        self.udp_video_port = 8889  # UDP port for video streams
        self.udp_audio_port = 8890  # UDP port for audio streams
        
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
            'upload_dir': 'uploads',
            'download_dir': 'downloads',
            'max_file_size': MAX_FILE_SIZE,
            'chunk_size': CHUNK_SIZE,
            'next_ephemeral_port': 9001
        }
        
        # Create directories
        os.makedirs(self.file_transfer['upload_dir'], exist_ok=True)
        os.makedirs(self.file_transfer['download_dir'], exist_ok=True)
        
        # Server state
        self.running = False
        self.clients = {}  # {client_id: client_info}
        self.next_client_id = 1
        
        # Host participant info
        self.host_id = 0  # Server acts as participant with ID 0
        self.host_name = "Host"
        self.host_video_enabled = False
        self.host_audio_enabled = False  # Keep for compatibility
        self.host_microphone_enabled = False
        self.host_speaker_enabled = True  # Speaker on by default
        self.host_screen_share_enabled = False
        
        # CN_project style advanced screen sharing system
        self.presentation_active = False
        self.presenter_id = None
        self.presenter_username = None
        self.presenter_port = None  # Dedicated TCP port for presenter frames
        self.viewer_port = None     # Dedicated TCP port for viewer connections
        self.presenter_server = None
        self.viewer_server = None
        self.presenter_writer = None
        self.frame_viewers = {}     # client_id -> writer mapping for frame relay
        self.frame_relay_task = None
        self.next_screen_port = 9000  # Starting port for screen sharing
        
        # Optimized screen settings (CN_project inspired)
        self.screen_settings = {
            'fps': 5,  # Stable 5 FPS for reliability
            'quality': 70,  # Higher quality like CN_project
            'scale_factor': 0.5,  # 50% scaling like CN_project
            'frame_header_size': 4,  # 4-byte frame length header
            'buffer_size': 8192,     # Network buffer size
            'connection_timeout': 30,  # Connection timeout
            'adaptive_quality': True,
            'min_quality': 40,
            'max_quality': 85
        }
        
        # Sockets
        self.tcp_socket = None
        self.udp_video_socket = None
        self.udp_audio_socket = None
        
        # Session management
        self.presenter_id = None
        self.chat_history = []
        self.shared_files = {}  # {fid: file_info}
        self.file_sessions = {}  # {port: session_info} for file transfers
        
        # Enhanced messaging system
        self.message_history = []  # All messages (chat, broadcast, unicast)
        self.private_messages = {}  # {client_id: [messages]} for unicast history
        
        # Meeting logs and analytics
        self.activity_logs = []
        self.participant_logs = {}  # {client_id: {join_time, leave_time, etc}}
        
        # Video display
        self.current_photo = None
        self.video_frame_queue = queue.Queue(maxsize=2)
        self.screen_frame_queue = queue.Queue(maxsize=2)
        
        # UI state tracking to prevent flickering
        self.current_display_mode = None  # 'screen_sharing', 'video', 'none'
        
        # Permission requests
        self.pending_requests = {}  # {client_id: {'audio': bool, 'video': bool, 'screen': bool}}
        self.file_transfer_logs = []
        self.meeting_settings = {
            'allow_video': True,
            'allow_audio': True,
            'allow_screen_share': True,
            'allow_file_sharing': True,
            'allow_chat': True,
            'max_participants': 50,
            'meeting_password': '',
            'waiting_room': False,
            'mute_on_join': False,
            'video_off_on_join': False
        }
        
        # Threading
        self.client_threads = []
        self.message_queue = queue.Queue()
        
        # Media devices for Host
        self.video_cap = None
        self.audio_stream = None
        self.audio = None
        
        # Screen sharing
        self.screen_frame_queue = queue.Queue(maxsize=2)
        
        # GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Initialize the server GUI"""
        self.root = tk.Tk()
        self.root.title("LAN Meeting Server - Host")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.configure(bg='#1e1e1e')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure modern style
        self.setup_modern_style()
        
        # Create main interface
        self.create_main_interface()
        
        # Start video display timer
        self.start_video_display_timer()
        
        # Initialize requests display
        self.update_requests_display()
        
    def setup_modern_style(self):
        """Setup modern dark theme styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors for modern dark theme
        style.configure('Modern.TFrame', background='#2d2d2d', relief='flat')
        style.configure('Header.TFrame', background='#1e1e1e', relief='flat')
        style.configure('Video.TFrame', background='#000000', relief='flat')
        
        # Notebook styling
        style.configure('TNotebook', background='#1e1e1e', borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background='#2d2d2d', 
                       foreground='white',
                       padding=[20, 10],
                       font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', '#0078d4'), ('active', '#3d3d3d')])
        
        # Modern buttons
        style.configure('Modern.TButton',
                       background='#0078d4',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        style.map('Modern.TButton',
                 background=[('active', '#106ebe'), ('pressed', '#005a9e')])
        
        # Danger button (red)
        style.configure('Danger.TButton',
                       background='#d13438',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        style.map('Danger.TButton',
                 background=[('active', '#b71c1c'), ('pressed', '#8b0000')])
        
        # Success button (green)
        style.configure('Success.TButton',
                       background='#107c10',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        style.map('Success.TButton',
                 background=[('active', '#0e6e0e'), ('pressed', '#0c5d0c')])
        
        # Warning button (orange)
        style.configure('Warning.TButton',
                       background='#fd7e14',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        style.map('Warning.TButton',
                 background=[('active', '#e8590c'), ('pressed', '#d63384')])
        
        # Modern labels
        style.configure('Modern.TLabel',
                       background='#2d2d2d',
                       foreground='white',
                       font=('Segoe UI', 10))
        
        style.configure('Header.TLabel',
                       background='#2d2d2d',
                       foreground='white',
                       font=('Segoe UI', 12, 'bold'))
        
        style.configure('Title.TLabel',
                       background='#2d2d2d',
                       foreground='white',
                       font=('Segoe UI', 16, 'bold'))
        
        # Treeview styling
        style.configure('Modern.Treeview',
                       background='#3d3d3d',
                       foreground='white',
                       fieldbackground='#3d3d3d',
                       borderwidth=0)
        style.configure('Modern.Treeview.Heading',
                       background='#2d2d2d',
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'))
        
        # Text widget styling
        style.configure('Modern.TText',
                       background='#3d3d3d',
                       foreground='white',
                       borderwidth=0)
        
    def create_main_interface(self):
        """Create the main server interface"""
        # Main container
        main_container = tk.Frame(self.root, bg='#1e1e1e')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header with server controls
        header_frame = tk.Frame(main_container, bg='#2d2d2d', height=80)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # Left side - Title and status
        left_header = tk.Frame(header_frame, bg='#2d2d2d')
        left_header.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=15)
        
        tk.Label(left_header, text="LAN Meeting Server", 
                font=('Segoe UI', 18, 'bold'), 
                fg='white', bg='#2d2d2d').pack(anchor=tk.W)
        
        self.server_status_label = tk.Label(left_header, text="● Server Stopped", 
                                           font=('Segoe UI', 12), 
                                           fg='#ff6b6b', bg='#2d2d2d')
        self.server_status_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Right side - Server controls
        right_header = tk.Frame(header_frame, bg='#2d2d2d')
        right_header.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=15)
        
        self.start_server_btn = tk.Button(right_header, text="🚀 Start Server", 
                                         command=self.start_server,
                                         bg='#107c10', fg='white', 
                                         font=('Segoe UI', 12, 'bold'),
                                         relief='flat', borderwidth=0,
                                         padx=25, pady=10,
                                         cursor='hand2')
        self.start_server_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_server_btn = tk.Button(right_header, text="⏹ Stop Server", 
                                        command=self.stop_server,
                                        bg='#d13438', fg='white', 
                                        font=('Segoe UI', 12, 'bold'),
                                        relief='flat', borderwidth=0,
                                        padx=25, pady=10,
                                        cursor='hand2', state=tk.DISABLED)
        self.stop_server_btn.pack(side=tk.LEFT)
        
        # Settings button
        self.settings_btn = tk.Button(right_header, text="⚙️ Settings", 
                                     command=self.open_settings,
                                     bg='#0078d4', fg='white', 
                                     font=('Segoe UI', 12, 'bold'),
                                     relief='flat', borderwidth=0,
                                     padx=25, pady=10,
                                     cursor='hand2')
        self.settings_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Main content area
        content_frame = tk.Frame(main_container, bg='#1e1e1e')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Host video and controls
        left_panel = tk.Frame(content_frame, bg='#2d2d2d', width=600)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Dynamic video conference area
        video_frame = tk.LabelFrame(left_panel, text="📹 Video Conference", 
                                   bg='#2d2d2d', fg='white',
                                   font=('Segoe UI', 12, 'bold'))
        video_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Video grid container
        self.video_grid_frame = tk.Frame(video_frame, bg='#000000')
        self.video_grid_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Host video (main video)
        self.host_video_label = tk.Label(self.video_grid_frame, 
                                        text="📹 Host Video\n\nClick 'Start Video' to begin",
                                        font=('Segoe UI', 14),
                                        fg='#888888', bg='#000000')
        self.host_video_label.pack(expand=True, fill=tk.BOTH)
        
        # Initialize video grid
        self.video_labels = {}  # {client_id: video_label}
        self.video_grid_columns = 3  # Default grid columns
        
        # Host controls
        controls_frame = tk.LabelFrame(left_panel, text="🎛️ Host Controls", 
                                      bg='#2d2d2d', fg='white',
                                      font=('Segoe UI', 12, 'bold'))
        controls_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        controls_inner = tk.Frame(controls_frame, bg='#2d2d2d')
        controls_inner.pack(fill=tk.X, padx=15, pady=15)
        
        # Media control buttons
        self.host_video_btn = tk.Button(controls_inner, text="📹 Start Video", 
                                       command=self.toggle_host_video,
                                       bg='#404040', fg='white', 
                                       font=('Segoe UI', 11, 'bold'),
                                       relief='flat', borderwidth=0,
                                       padx=20, pady=8,
                                       cursor='hand2', state=tk.DISABLED)
        self.host_video_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Microphone button
        self.host_mic_btn = tk.Button(controls_inner, text="🎤 Mic", 
                                     command=self.toggle_host_microphone,
                                     bg='#404040', fg='white', 
                                     font=('Segoe UI', 11, 'bold'),
                                     relief='flat', borderwidth=0,
                                     padx=15, pady=8,
                                     cursor='hand2', state=tk.DISABLED)
        self.host_mic_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Speaker button
        self.host_speaker_btn = tk.Button(controls_inner, text="🔊 Speaker", 
                                         command=self.toggle_host_speaker,
                                         bg='#404040', fg='white', 
                                         font=('Segoe UI', 11, 'bold'),
                                         relief='flat', borderwidth=0,
                                         padx=15, pady=8,
                                         cursor='hand2', state=tk.DISABLED)
        self.host_speaker_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.host_present_btn = tk.Button(controls_inner, text="🖥️ Present", 
                                         command=self.toggle_host_presentation,
                                         bg='#fd7e14', fg='white', 
                                         font=('Segoe UI', 11, 'bold'),
                                         relief='flat', borderwidth=0,
                                         padx=20, pady=8,
                                         cursor='hand2', state=tk.DISABLED)
        self.host_present_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop screen sharing button
        self.host_stop_screen_btn = tk.Button(controls_inner, text="⏹️ Stop Screen", 
                                             command=self.stop_host_screen_share,
                                             bg='#dc3545', fg='white', 
                                             font=('Segoe UI', 11, 'bold'),
                                             relief='flat', borderwidth=0,
                                             padx=20, pady=8,
                                             cursor='hand2', state=tk.DISABLED)
        self.host_stop_screen_btn.pack(side=tk.LEFT)
        
        # Right panel - Simple info and chat only
        right_panel = tk.Frame(content_frame, bg='#2d2d2d', width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        # Simple server info
        info_frame = tk.LabelFrame(right_panel, text="📊 Server Info", 
                                  bg='#2d2d2d', fg='white',
                                  font=('Segoe UI', 12, 'bold'))
        info_frame.pack(fill=tk.X, padx=15, pady=15)
        
        info_inner = tk.Frame(info_frame, bg='#2d2d2d')
        info_inner.pack(fill=tk.X, padx=15, pady=10)
        
        self.server_info_label = tk.Label(info_inner, text="🌐 Server: Not Running", 
                                         font=('Segoe UI', 10), 
                                         fg='white', bg='#2d2d2d')
        self.server_info_label.pack(anchor=tk.W)
        
        self.participants_count_label = tk.Label(info_inner, text="👥 Participants: 0", 
                                                font=('Segoe UI', 10), 
                                                fg='white', bg='#2d2d2d')
        self.participants_count_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Simple group chat
        chat_frame = tk.LabelFrame(right_panel, text="💬 Group Chat", 
                                  bg='#2d2d2d', fg='white',
                                  font=('Segoe UI', 12, 'bold'))
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        chat_inner = tk.Frame(chat_frame, bg='#2d2d2d')
        chat_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat display
        self.chat_display = tk.Text(chat_inner, 
                                   bg='#3d3d3d', fg='white',
                                   font=('Segoe UI', 9),
                                   relief='flat', borderwidth=0,
                                   wrap=tk.WORD, state=tk.DISABLED,
                                   height=12)
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat input
        chat_input_frame = tk.Frame(chat_inner, bg='#2d2d2d')
        chat_input_frame.pack(fill=tk.X)
        
        self.chat_entry = tk.Entry(chat_input_frame, 
                                  bg='#3d3d3d', fg='white',
                                  font=('Segoe UI', 10),
                                  relief='flat', borderwidth=0,
                                  insertbackground='white',
                                  state=tk.DISABLED)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", self.send_host_chat_message)
        
        self.chat_send_btn = tk.Button(chat_input_frame, text="Send", 
                                      command=self.send_host_chat_message,
                                      bg='#0078d4', fg='white', 
                                      font=('Segoe UI', 10, 'bold'),
                                      relief='flat', borderwidth=0,
                                      padx=15, pady=6,
                                      cursor='hand2', state=tk.DISABLED)
        self.chat_send_btn.pack(side=tk.RIGHT)
        
        # Add hover effects
        self.add_button_hover_effects()
        
    def add_button_hover_effects(self):
        """Add hover effects to buttons"""
        def on_enter(event, color):
            event.widget.configure(bg=color)
        
        def on_leave(event, original_color):
            event.widget.configure(bg=original_color)
        
        # Start button hover
        self.start_server_btn.bind("<Enter>", lambda e: on_enter(e, '#0e6e0e'))
        self.start_server_btn.bind("<Leave>", lambda e: on_leave(e, '#107c10'))
        
        # Stop button hover
        self.stop_server_btn.bind("<Enter>", lambda e: on_enter(e, '#b71c1c'))
        self.stop_server_btn.bind("<Leave>", lambda e: on_leave(e, '#d13438'))
        
        # Settings button hover
        self.settings_btn.bind("<Enter>", lambda e: on_enter(e, '#106ebe'))
        self.settings_btn.bind("<Leave>", lambda e: on_leave(e, '#0078d4'))
        
    def open_settings(self):
        """Open comprehensive settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Meeting Settings & Management")
        settings_window.geometry("1000x700")
        settings_window.configure(bg='#2d2d2d')
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # General Settings Tab
        self.create_general_settings_tab(notebook)
        
        # Participants Management Tab
        self.create_participants_management_tab(notebook)
        
        # Chat Management Tab
        self.create_chat_management_tab(notebook)
        
        # File Transfer Management Tab
        self.create_file_management_tab(notebook)
        
        # Apply button
        apply_frame = tk.Frame(settings_window, bg='#2d2d2d')
        apply_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(apply_frame, text="💾 Apply All Settings", 
                 command=lambda: self.apply_all_settings_and_close(settings_window),
                 bg='#107c10', fg='white', 
                 font=('Segoe UI', 12, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=25, pady=10,
                 cursor='hand2').pack(side=tk.RIGHT)
        
    def create_general_settings_tab(self, notebook):
        """Create general settings tab"""
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="⚙️ General Settings")
        
        # General settings
        general_settings_frame = tk.LabelFrame(general_frame, text="Meeting Configuration", 
                                              bg='#2d2d2d', fg='white',
                                              font=('Segoe UI', 12, 'bold'))
        general_settings_frame.pack(fill=tk.X, padx=15, pady=15)
        
        general_inner = tk.Frame(general_settings_frame, bg='#2d2d2d')
        general_inner.pack(fill=tk.X, padx=15, pady=15)
        
        # Max participants
        tk.Label(general_inner, text="Max Participants:", 
                font=('Segoe UI', 10), fg='white', bg='#2d2d2d').grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.max_participants_var = tk.StringVar(value="50")
        max_participants_spinbox = tk.Spinbox(general_inner, from_=2, to=100, 
                                             textvariable=self.max_participants_var,
                                             bg='#3d3d3d', fg='white', 
                                             font=('Segoe UI', 10), relief='flat', borderwidth=0,
                                             insertbackground='white', width=10)
        max_participants_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Permissions
        permissions_frame = tk.LabelFrame(general_frame, text="Participant Permissions", 
                                         bg='#2d2d2d', fg='white',
                                         font=('Segoe UI', 12, 'bold'))
        permissions_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        permissions_inner = tk.Frame(permissions_frame, bg='#2d2d2d')
        permissions_inner.pack(fill=tk.X, padx=15, pady=15)
        
        # Permission checkboxes
        self.allow_video_var = tk.BooleanVar(value=True)
        self.allow_audio_var = tk.BooleanVar(value=True)
        self.allow_chat_var = tk.BooleanVar(value=True)
        self.allow_file_sharing_var = tk.BooleanVar(value=True)
        self.allow_screen_share_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(permissions_inner, text="📹 Allow Video", variable=self.allow_video_var,
                      bg='#2d2d2d', fg='white', selectcolor='#3d3d3d',
                      font=('Segoe UI', 10), relief='flat', borderwidth=0).pack(anchor=tk.W, pady=2)
        
        tk.Checkbutton(permissions_inner, text="🎤 Allow Audio", variable=self.allow_audio_var,
                      bg='#2d2d2d', fg='white', selectcolor='#3d3d3d',
                      font=('Segoe UI', 10), relief='flat', borderwidth=0).pack(anchor=tk.W, pady=2)
        
        tk.Checkbutton(permissions_inner, text="💬 Allow Chat", variable=self.allow_chat_var,
                      bg='#2d2d2d', fg='white', selectcolor='#3d3d3d',
                      font=('Segoe UI', 10), relief='flat', borderwidth=0).pack(anchor=tk.W, pady=2)
        
        tk.Checkbutton(permissions_inner, text="📁 Allow File Sharing", variable=self.allow_file_sharing_var,
                      bg='#2d2d2d', fg='white', selectcolor='#3d3d3d',
                      font=('Segoe UI', 10), relief='flat', borderwidth=0).pack(anchor=tk.W, pady=2)
        
        tk.Checkbutton(permissions_inner, text="🖥️ Allow Screen Sharing", variable=self.allow_screen_share_var,
                      bg='#2d2d2d', fg='white', selectcolor='#3d3d3d',
                      font=('Segoe UI', 10), relief='flat', borderwidth=0).pack(anchor=tk.W, pady=2)
        
    def create_participants_management_tab(self, notebook):
        """Create participants management tab"""
        participants_frame = ttk.Frame(notebook)
        notebook.add(participants_frame, text="👥 Participants")
        
        # Participants list with detailed info
        participants_list_frame = tk.LabelFrame(participants_frame, text="Active Participants", 
                                              bg='#2d2d2d', fg='white',
                                              font=('Segoe UI', 12, 'bold'))
        participants_list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Participants treeview
        tree_frame = tk.Frame(participants_list_frame, bg='#2d2d2d')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.detailed_participants_tree = ttk.Treeview(tree_frame, 
                                                      columns=('ID', 'Name', 'IP', 'Join Time', 'Status', 'Video', 'Audio', 'Screen', 'Actions'), 
                                                      show='headings',
                                                      style='Modern.Treeview')
        
        # Configure columns
        self.detailed_participants_tree.heading('ID', text='ID')
        self.detailed_participants_tree.heading('Name', text='Name')
        self.detailed_participants_tree.heading('IP', text='IP Address')
        self.detailed_participants_tree.heading('Join Time', text='Join Time')
        self.detailed_participants_tree.heading('Status', text='Status')
        self.detailed_participants_tree.heading('Video', text='Video')
        self.detailed_participants_tree.heading('Audio', text='Audio')
        self.detailed_participants_tree.heading('Screen', text='Screen')
        self.detailed_participants_tree.heading('Actions', text='Actions')
        
        self.detailed_participants_tree.column('ID', width=50)
        self.detailed_participants_tree.column('Name', width=120)
        self.detailed_participants_tree.column('IP', width=120)
        self.detailed_participants_tree.column('Join Time', width=100)
        self.detailed_participants_tree.column('Status', width=80)
        self.detailed_participants_tree.column('Video', width=60)
        self.detailed_participants_tree.column('Audio', width=60)
        self.detailed_participants_tree.column('Screen', width=60)
        self.detailed_participants_tree.column('Actions', width=100)
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", 
                                      command=self.detailed_participants_tree.yview)
        self.detailed_participants_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.detailed_participants_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")
        
        # Participant management buttons
        management_frame = tk.Frame(participants_list_frame, bg='#2d2d2d')
        management_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(management_frame, text="🔇 Mute Selected", 
                 command=self.mute_selected_participant,
                 bg='#fd7e14', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(management_frame, text="📹 Disable Video", 
                 command=self.disable_selected_video,
                 bg='#fd7e14', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(management_frame, text="🖥️ Stop Presenting", 
                 command=self.stop_selected_presenting,
                 bg='#fd7e14', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(management_frame, text="🚫 Force Stop Screen", 
                 command=self.force_stop_screen_sharing,
                 bg='#dc3545', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(management_frame, text="❌ Remove Participant", 
                 command=self.remove_selected_participant,
                 bg='#d13438', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT)
        
        # Second row for permission controls
        permission_frame = tk.Frame(participants_list_frame, bg='#2d2d2d')
        permission_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(permission_frame, text="🎤 Request Audio", 
                 command=self.request_client_audio,
                 bg='#28a745', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(permission_frame, text="📹 Request Video", 
                 command=self.request_client_video,
                 bg='#28a745', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(permission_frame, text="✅ Grant Permissions", 
                 command=self.grant_client_permissions,
                 bg='#17a2b8', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(permission_frame, text="❌ Deny Permissions", 
                 command=self.deny_client_permissions,
                 bg='#dc3545', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT)
        
        # Pending requests section
        requests_frame = tk.LabelFrame(participants_list_frame, text="🔔 Pending Permission Requests", 
                                      bg='#2d2d2d', fg='white',
                                      font=('Segoe UI', 11, 'bold'))
        requests_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        self.requests_text = tk.Text(requests_frame, height=4, 
                                    bg='#1e1e1e', fg='white',
                                    font=('Segoe UI', 10),
                                    state=tk.DISABLED)
        self.requests_text.pack(fill=tk.X, padx=10, pady=10)
        
        # Bulk actions
        bulk_frame = tk.Frame(participants_list_frame, bg='#2d2d2d')
        bulk_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(bulk_frame, text="🔇 Mute All", 
                 command=self.mute_all_participants,
                 bg='#ff6b6b', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(bulk_frame, text="📹 Disable All Video", 
                 command=self.disable_all_video,
                 bg='#ff6b6b', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(bulk_frame, text="❌ Remove All", 
                 command=self.remove_all_participants,
                 bg='#d13438', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT)
        
        # Update participants display
        self.update_detailed_participants_display()
        
    def create_chat_management_tab(self, notebook):
        """Create chat management tab"""
        chat_frame = ttk.Frame(notebook)
        notebook.add(chat_frame, text="💬 Chat Management")
        
        # Chat history and monitoring
        chat_monitor_frame = tk.LabelFrame(chat_frame, text="Chat History & Monitoring", 
                                          bg='#2d2d2d', fg='white',
                                          font=('Segoe UI', 12, 'bold'))
        chat_monitor_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Chat display
        chat_display_frame = tk.Frame(chat_monitor_frame, bg='#2d2d2d')
        chat_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_monitor_text = tk.Text(chat_display_frame, 
                                        bg='#3d3d3d', fg='white',
                                        font=('Segoe UI', 10),
                                        relief='flat', borderwidth=0,
                                        wrap=tk.WORD, state=tk.DISABLED,
                                        height=15)
        
        chat_scrollbar = ttk.Scrollbar(chat_display_frame, orient="vertical", 
                                      command=self.chat_monitor_text.yview)
        self.chat_monitor_text.configure(yscrollcommand=chat_scrollbar.set)
        
        self.chat_monitor_text.pack(side="left", fill="both", expand=True)
        chat_scrollbar.pack(side="right", fill="y")
        
        # Chat management controls
        chat_controls_frame = tk.Frame(chat_monitor_frame, bg='#2d2d2d')
        chat_controls_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(chat_controls_frame, text="📥 Export Chat Log", 
                 command=self.export_chat_log,
                 bg='#0078d4', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(chat_controls_frame, text="🗑️ Clear Chat History", 
                 command=self.clear_chat_history,
                 bg='#d13438', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(chat_controls_frame, text="📊 Chat Statistics", 
                 command=self.show_chat_statistics,
                 bg='#107c10', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT)
        
        # Update chat display
        self.update_chat_monitor_display()
        
    def create_file_management_tab(self, notebook):
        """Create file management tab"""
        file_frame = ttk.Frame(notebook)
        notebook.add(file_frame, text="📁 File Management")
        
        # File sharing management
        file_management_frame = tk.LabelFrame(file_frame, text="Shared Files Management", 
                                             bg='#2d2d2d', fg='white',
                                             font=('Segoe UI', 12, 'bold'))
        file_management_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Files treeview
        files_tree_frame = tk.Frame(file_management_frame, bg='#2d2d2d')
        files_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.files_tree = ttk.Treeview(files_tree_frame, 
                                      columns=('Name', 'Size', 'Shared By', 'Share Time', 'Downloads'), 
                                      show='headings',
                                      style='Modern.Treeview')
        
        # Configure columns
        self.files_tree.heading('Name', text='File Name')
        self.files_tree.heading('Size', text='Size')
        self.files_tree.heading('Shared By', text='Shared By')
        self.files_tree.heading('Share Time', text='Share Time')
        self.files_tree.heading('Downloads', text='Downloads')
        
        self.files_tree.column('Name', width=200)
        self.files_tree.column('Size', width=100)
        self.files_tree.column('Shared By', width=120)
        self.files_tree.column('Share Time', width=120)
        self.files_tree.column('Downloads', width=80)
        
        # Scrollbar for files treeview
        files_scrollbar = ttk.Scrollbar(files_tree_frame, orient="vertical", 
                                       command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_scrollbar.set)
        
        self.files_tree.pack(side="left", fill="both", expand=True)
        files_scrollbar.pack(side="right", fill="y")
        
        # File management controls
        file_controls_frame = tk.Frame(file_management_frame, bg='#2d2d2d')
        file_controls_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(file_controls_frame, text="📤 Share File as Host", 
                 command=self.share_file_as_host,
                 bg='#0078d4', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(file_controls_frame, text="📥 Download Selected", 
                 command=self.download_selected_file,
                 bg='#107c10', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(file_controls_frame, text="🗑️ Remove Selected", 
                 command=self.remove_selected_file,
                 bg='#d13438', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(file_controls_frame, text="🗑️ Clear All Files", 
                 command=self.clear_all_files,
                 bg='#ff6b6b', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', borderwidth=0,
                 padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT)
        
        # Update files display
        self.update_files_display()
        
    def apply_all_settings_and_close(self, window):
        """Apply all settings and close window"""
        try:
            # Update meeting settings
            self.meeting_settings.update({
                'max_participants': int(self.max_participants_var.get()),
                'allow_video': self.allow_video_var.get(),
                'allow_audio': self.allow_audio_var.get(),
                'allow_chat': self.allow_chat_var.get(),
                'allow_file_sharing': self.allow_file_sharing_var.get(),
                'allow_screen_share': self.allow_screen_share_var.get()
            })
            
            self.log_message("All meeting settings updated successfully")
            messagebox.showinfo("Settings Applied", "All meeting settings have been updated!")
            window.destroy()
            
        except Exception as e:
            self.log_message(f"Error applying settings: {str(e)}")
            messagebox.showerror("Settings Error", f"Failed to apply settings: {str(e)}")
            
    def update_detailed_participants_display(self):
        """Update detailed participants display in settings"""
        if hasattr(self, 'detailed_participants_tree'):
            # Clear existing items
            for item in self.detailed_participants_tree.get_children():
                self.detailed_participants_tree.delete(item)
            
            # Add Host
            self.detailed_participants_tree.insert('', 'end', values=(
                self.host_id,
                "Host",
                "Server",
                datetime.now().strftime("%H:%M:%S") if self.running else "N/A",
                "Active",
                "✅" if self.host_video_enabled else "❌",
                "✅" if self.host_audio_enabled else "❌",
                "✅" if self.host_screen_share_enabled else "❌",
                "Host Controls"
            ))
            
            # Add clients
            for client_id, client_info in self.clients.items():
                self.detailed_participants_tree.insert('', 'end', values=(
                    client_id,
                    client_info['name'],
                    client_info['address'][0],
                    client_info.get('join_time', 'Unknown'),
                    client_info['status'],
                    "✅" if client_info.get('video_enabled') else "❌",
                    "✅" if client_info.get('audio_enabled') else "❌",
                    "Available"
                ))
                
    def update_chat_monitor_display(self):
        """Update chat monitor display"""
        if hasattr(self, 'chat_monitor_text'):
            self.chat_monitor_text.config(state=tk.NORMAL)
            self.chat_monitor_text.delete(1.0, tk.END)
            
            for msg in self.chat_history:
                timestamp = msg.get('timestamp', '')
                sender = msg.get('name', 'Unknown')
                message = msg.get('message', '')
                
                if timestamp:
                    try:
                        time_obj = datetime.fromisoformat(timestamp)
                        time_str = time_obj.strftime("%H:%M:%S")
                    except:
                        time_str = "??:??:??"
                else:
                    time_str = "??:??:??"
                
                # Add sender icon
                sender_icon = "🏠" if sender == "Host" else "👤"
                if sender == "System":
                    sender_icon = "ℹ️"
                    
                chat_line = f"[{time_str}] {sender_icon} {sender}: {message}\n"
                self.chat_monitor_text.insert(tk.END, chat_line)
                
            self.chat_monitor_text.see(tk.END)
            self.chat_monitor_text.config(state=tk.DISABLED)
            
    def export_chat_log(self):
        """Export chat log to file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Chat Log"
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write("LAN Meeting Server - Chat Log\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for msg in self.chat_history:
                        timestamp = msg.get('timestamp', '')
                        sender = msg.get('name', 'Unknown')
                        message = msg.get('message', '')
                        
                        if timestamp:
                            try:
                                time_obj = datetime.fromisoformat(timestamp)
                                time_str = time_obj.strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                time_str = timestamp
                        else:
                            time_str = "Unknown time"
                            
                        f.write(f"[{time_str}] {sender}: {message}\n")
                        
                self.log_message(f"Chat log exported to {filename}")
                messagebox.showinfo("Export Complete", f"Chat log exported to {filename}")
                
        except Exception as e:
            self.log_message(f"Error exporting chat log: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export chat log: {str(e)}")
            
    def clear_chat_history(self):
        """Clear chat history"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all chat history?"):
            try:
                self.chat_history.clear()
                self.update_chat_monitor_display()
                self.update_chat_display()
                
                # Notify clients
                clear_msg = {'type': 'chat_history_cleared'}
                self.broadcast_message(clear_msg)
                
                self.log_message("Chat history cleared by host")
                messagebox.showinfo("Chat Cleared", "Chat history has been cleared")
            except Exception as e:
                self.log_message(f"Error clearing chat history: {str(e)}")
                
    def show_chat_statistics(self):
        """Show chat statistics"""
        try:
            total_messages = len(self.chat_history)
            participants = {}
            
            for msg in self.chat_history:
                sender = msg.get('name', 'Unknown')
                if sender not in participants:
                    participants[sender] = 0
                participants[sender] += 1
            
            stats_window = tk.Toplevel(self.root)
            stats_window.title("Chat Statistics")
            stats_window.geometry("400x300")
            stats_window.configure(bg='#2d2d2d')
            stats_window.transient(self.root)
            
            stats_frame = tk.Frame(stats_window, bg='#2d2d2d')
            stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            tk.Label(stats_frame, text="Chat Statistics", 
                    font=('Segoe UI', 16, 'bold'), 
                    fg='white', bg='#2d2d2d').pack(pady=(0, 20))
            
            tk.Label(stats_frame, text=f"Total Messages: {total_messages}", 
                    font=('Segoe UI', 12), 
                    fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=5)
            
            tk.Label(stats_frame, text=f"Active Participants: {len(participants)}", 
                    font=('Segoe UI', 12), 
                    fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=5)
            
            tk.Label(stats_frame, text="Messages per Participant:", 
                    font=('Segoe UI', 12, 'bold'), 
                    fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=(20, 10))
            
            for sender, count in sorted(participants.items(), key=lambda x: x[1], reverse=True):
                tk.Label(stats_frame, text=f"  {sender}: {count} messages", 
                        font=('Segoe UI', 10), 
                        fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=2)
                
        except Exception as e:
            self.log_message(f"Error showing chat statistics: {str(e)}")
            messagebox.showerror("Statistics Error", f"Failed to show statistics: {str(e)}")
            
    def download_selected_file(self):
        """Download selected file"""
        selection = self.files_tree.selection()
        if selection:
            item = self.files_tree.item(selection[0])
            file_name = item['values'][0]
            
            if file_name in self.shared_files:
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
                        
                        # Update download count
                        file_info['downloads'] += 1
                        self.update_files_display()
                        
                        self.log_message(f"File '{file_name}' downloaded to {download_path}")
                        messagebox.showinfo("Download Complete", f"File saved to {download_path}")
                        
                except Exception as e:
                    self.log_message(f"Error downloading file: {str(e)}")
                    messagebox.showerror("Download Error", f"Failed to download file: {str(e)}")
        else:
            messagebox.showwarning("No Selection", "Please select a file first")
            
    def remove_selected_file(self):
        """Remove selected file"""
        selection = self.files_tree.selection()
        if selection:
            item = self.files_tree.item(selection[0])
            file_name = item['values'][0]
            
            if messagebox.askyesno("Confirm Removal", f"Remove file '{file_name}'?"):
                try:
                    if file_name in self.shared_files:
                        del self.shared_files[file_name]
                        self.update_files_display()
                        
                        # Notify clients
                        remove_msg = {'type': 'file_removed', 'file_name': file_name}
                        self.broadcast_message(remove_msg)
                        
                        self.log_message(f"File '{file_name}' removed by host")
                        messagebox.showinfo("File Removed", f"File '{file_name}' has been removed")
                        
                except Exception as e:
                    self.log_message(f"Error removing file: {str(e)}")
                    messagebox.showerror("Removal Error", f"Failed to remove file: {str(e)}")
        else:
            messagebox.showwarning("No Selection", "Please select a file first")
            
    def create_main_meeting_tab(self):
        """Create the main meeting interface tab"""
        main_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(main_frame, text="🏠 Main Meeting")
        
        # Top control bar
        control_bar = ttk.Frame(main_frame, style='Header.TFrame')
        control_bar.pack(fill=tk.X, padx=20, pady=20)
        
        # Left side - Server status
        left_controls = ttk.Frame(control_bar, style='Header.TFrame')
        left_controls.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(left_controls, text="LAN Meeting Server", 
                 style='Title.TLabel').pack(anchor=tk.W)
        
        self.server_status_label = ttk.Label(left_controls, text="● Server Stopped", 
                                           style='Modern.TLabel')
        self.server_status_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Right side - Server controls
        right_controls = ttk.Frame(control_bar, style='Header.TFrame')
        right_controls.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.start_server_btn = ttk.Button(right_controls, text="🚀 Start Server", 
                                          command=self.start_server,
                                          style='Success.TButton')
        self.start_server_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_server_btn = ttk.Button(right_controls, text="⏹ Stop Server", 
                                         command=self.stop_server,
                                         style='Danger.TButton',
                                         state=tk.DISABLED)
        self.stop_server_btn.pack(side=tk.LEFT)
        
        # Main content area
        content_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        content_paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Left panel - Video and controls
        left_panel = ttk.Frame(content_paned, style='Modern.TFrame')
        content_paned.add(left_panel, weight=2)
        
        # Host video section
        video_frame = ttk.LabelFrame(left_panel, text="📹 Host Video", style='Modern.TLabelframe')
        video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.host_video_label = tk.Label(video_frame, 
                                        text="📹 Host Video\n\nClick 'Start Video' to begin",
                                        font=('Segoe UI', 14),
                                        fg='#888888', bg='#000000')
        self.host_video_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Host controls
        host_controls_frame = ttk.LabelFrame(left_panel, text="🎛️ Host Controls", style='Modern.TLabelframe')
        host_controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        controls_inner = ttk.Frame(host_controls_frame, style='Modern.TFrame')
        controls_inner.pack(fill=tk.X, padx=15, pady=15)
        
        # Media control buttons
        media_buttons = ttk.Frame(controls_inner, style='Modern.TFrame')
        media_buttons.pack(fill=tk.X)
        
        self.host_video_btn = ttk.Button(media_buttons, text="📹 Start Video", 
                                        command=self.toggle_host_video,
                                        style='Modern.TButton',
                                        state=tk.DISABLED)
        self.host_video_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Microphone button
        self.host_mic_btn = ttk.Button(media_buttons, text="🎤 Mic", 
                                      command=self.toggle_host_microphone,
                                      style='Modern.TButton',
                                      state=tk.DISABLED)
        self.host_mic_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Speaker button
        self.host_speaker_btn = ttk.Button(media_buttons, text="🔊 Speaker", 
                                          command=self.toggle_host_speaker,
                                          style='Modern.TButton',
                                          state=tk.DISABLED)
        self.host_speaker_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.host_present_btn = ttk.Button(media_buttons, text="🖥️ Present", 
                                          command=self.toggle_host_presentation,
                                          style='Warning.TButton',
                                          state=tk.DISABLED)
        self.host_present_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop screen sharing button
        self.host_stop_screen_btn = ttk.Button(media_buttons, text="⏹️ Stop Screen", 
                                             command=self.stop_host_screen_share,
                                             style='Danger.TButton',
                                             state=tk.DISABLED)
        self.host_stop_screen_btn.pack(side=tk.LEFT)
        
        # Right panel - Participants and chat
        right_panel = ttk.Frame(content_paned, style='Modern.TFrame')
        content_paned.add(right_panel, weight=1)
        
        # Quick stats
        stats_frame = ttk.LabelFrame(right_panel, text="📊 Quick Stats", style='Modern.TLabelframe')
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        stats_inner = ttk.Frame(stats_frame, style='Modern.TFrame')
        stats_inner.pack(fill=tk.X, padx=15, pady=10)
        
        self.participants_count_label = ttk.Label(stats_inner, text="👥 Participants: 0", 
                                                 style='Modern.TLabel')
        self.participants_count_label.pack(anchor=tk.W)
        
        self.server_info_label = ttk.Label(stats_inner, text="🌐 Server: Not Running", 
                                          style='Modern.TLabel')
        self.server_info_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Participants list
        participants_frame = ttk.LabelFrame(right_panel, text="👥 Active Participants", style='Modern.TLabelframe')
        participants_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Participants treeview
        participants_inner = ttk.Frame(participants_frame, style='Modern.TFrame')
        participants_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.participants_tree = ttk.Treeview(participants_inner, 
                                             columns=('Name', 'Status', 'Join Time'), 
                                             show='headings',
                                             style='Modern.Treeview')
        self.participants_tree.heading('Name', text='Name')
        self.participants_tree.heading('Status', text='Status')
        self.participants_tree.heading('Join Time', text='Join Time')
        
        self.participants_tree.column('Name', width=150)
        self.participants_tree.column('Status', width=100)
        self.participants_tree.column('Join Time', width=100)
        
        participants_scrollbar = ttk.Scrollbar(participants_inner, orient="vertical", 
                                              command=self.participants_tree.yview)
        self.participants_tree.configure(yscrollcommand=participants_scrollbar.set)
        
        self.participants_tree.pack(side="left", fill="both", expand=True)
        participants_scrollbar.pack(side="right", fill="y")
        
        # Group chat
        chat_frame = ttk.LabelFrame(right_panel, text="💬 Group Chat", style='Modern.TLabelframe')
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        chat_inner = ttk.Frame(chat_frame, style='Modern.TFrame')
        chat_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat display
        self.chat_display = tk.Text(chat_inner, 
                                   bg='#3d3d3d', fg='white',
                                   font=('Segoe UI', 10),
                                   relief='flat', borderwidth=0,
                                   wrap=tk.WORD, state=tk.DISABLED,
                                   height=8)
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat input
        chat_input_frame = ttk.Frame(chat_inner, style='Modern.TFrame')
        chat_input_frame.pack(fill=tk.X)
        
        self.chat_entry = tk.Entry(chat_input_frame, 
                                  bg='#3d3d3d', fg='white',
                                  font=('Segoe UI', 10),
                                  relief='flat', borderwidth=0,
                                  insertbackground='white',
                                  state=tk.DISABLED)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", self.send_host_chat_message)
        
        self.chat_send_btn = ttk.Button(chat_input_frame, text="Send", 
                                       command=self.send_host_chat_message,
                                       style='Modern.TButton',
                                       state=tk.DISABLED)
        self.chat_send_btn.pack(side=tk.RIGHT)
        


        
    def create_video_section(self, parent):
        """Create the main video conference area"""
        video_container = tk.Frame(parent, bg='#1e1e1e')
        video_container.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Main video area
        main_video_frame = tk.Frame(video_container, bg='#000000', relief='solid', bd=1)
        main_video_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Host video display
        self.host_video_label = tk.Label(main_video_frame, 
                                        text="📹 Host Video\n\nClick 'Start Video' to begin",
                                        font=('Segoe UI', 16),
                                        fg='#888888', bg='#000000')
        self.host_video_label.pack(expand=True)
        
        # Right sidebar
        sidebar = tk.Frame(video_container, bg='#2d2d2d', width=350)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Participants section
        self.create_participants_section(sidebar)
        
        # Chat section
        self.create_chat_section(sidebar)
        
    def create_participants_section(self, parent):
        """Create participants list section"""
        participants_frame = tk.Frame(parent, bg='#2d2d2d')
        participants_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Header
        header_frame = tk.Frame(participants_frame, bg='#2d2d2d')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="👥 Participants", 
                font=('Segoe UI', 14, 'bold'), 
                fg='white', bg='#2d2d2d').pack(side=tk.LEFT)
        
        self.participant_count = tk.Label(header_frame, text="1", 
                                         font=('Segoe UI', 12, 'bold'), 
                                         fg='#0078d4', bg='#2d2d2d')
        self.participant_count.pack(side=tk.RIGHT)
        
        # Participants list
        list_frame = tk.Frame(participants_frame, bg='#2d2d2d')
        list_frame.pack(fill=tk.X)
        
        self.participants_listbox = tk.Listbox(list_frame, 
                                              bg='#3d3d3d', fg='white',
                                              selectbackground='#0078d4',
                                              font=('Segoe UI', 10),
                                              relief='flat', borderwidth=0,
                                              height=8)
        self.participants_listbox.pack(fill=tk.X)
        
    def create_chat_section(self, parent):
        """Create chat section"""
        chat_frame = tk.Frame(parent, bg='#2d2d2d')
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Chat header
        chat_header = tk.Frame(chat_frame, bg='#2d2d2d')
        chat_header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(chat_header, text="💬 Group Chat", 
                font=('Segoe UI', 14, 'bold'), 
                fg='white', bg='#2d2d2d').pack(side=tk.LEFT)
        
        # Chat display
        self.chat_display = tk.Text(chat_frame, 
                                   bg='#3d3d3d', fg='white',
                                   font=('Segoe UI', 10),
                                   relief='flat', borderwidth=0,
                                   wrap=tk.WORD, state=tk.DISABLED,
                                   height=12)
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat input
        input_frame = tk.Frame(chat_frame, bg='#2d2d2d')
        input_frame.pack(fill=tk.X)
        
        self.chat_entry = tk.Entry(input_frame, 
                                  bg='#3d3d3d', fg='white',
                                  font=('Segoe UI', 10),
                                  relief='flat', borderwidth=0,
                                  insertbackground='white',
                                  state=tk.DISABLED)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", self.send_host_chat_message)
        
        self.chat_send_btn = tk.Button(input_frame, text="Send", 
                                      command=self.send_host_chat_message,
                                      bg='#0078d4', fg='white', 
                                      font=('Segoe UI', 10, 'bold'),
                                      relief='flat', borderwidth=0,
                                      padx=15, pady=8,
                                      cursor='hand2', state=tk.DISABLED)
        self.chat_send_btn.pack(side=tk.RIGHT)
        
    def create_bottom_section(self, parent):
        """Create bottom controls section"""
        bottom_frame = tk.Frame(parent, bg='#2d2d2d', height=100)
        bottom_frame.pack(fill=tk.X, pady=(20, 0))
        bottom_frame.pack_propagate(False)
        
        # Host controls
        controls_frame = tk.Frame(bottom_frame, bg='#2d2d2d')
        controls_frame.pack(expand=True)
        
        # Media controls
        media_frame = tk.Frame(controls_frame, bg='#2d2d2d')
        media_frame.pack(pady=20)
        
        # Video button
        self.host_video_btn = tk.Button(media_frame, text="📹\nVideo", 
                                       command=self.toggle_host_video,
                                       bg='#404040', fg='white', 
                                       font=('Segoe UI', 10, 'bold'),
                                       relief='flat', borderwidth=0,
                                       width=8, height=3,
                                       cursor='hand2', state=tk.DISABLED)
        self.host_video_btn.pack(side=tk.LEFT, padx=10)
        
        # Microphone button
        self.host_mic_btn = tk.Button(media_frame, text="🎤\nMic", 
                                     command=self.toggle_host_microphone,
                                     bg='#404040', fg='white', 
                                     font=('Segoe UI', 10, 'bold'),
                                     relief='flat', borderwidth=0,
                                     width=8, height=3,
                                     cursor='hand2', state=tk.DISABLED)
        self.host_mic_btn.pack(side=tk.LEFT, padx=5)
        
        # Speaker button (starts enabled by default)
        self.host_speaker_btn = tk.Button(media_frame, text="🔊\nSpeaker On", 
                                         command=self.toggle_host_speaker,
                                         bg='#28a745', fg='white', 
                                         font=('Segoe UI', 10, 'bold'),
                                         relief='flat', borderwidth=0,
                                         width=8, height=3,
                                         cursor='hand2', state=tk.DISABLED)
        self.host_speaker_btn.pack(side=tk.LEFT, padx=5)
        
        # Present button
        self.host_present_btn = tk.Button(media_frame, text="🖥️\nPresent", 
                                         command=self.toggle_host_presentation,
                                         bg='#404040', fg='white', 
                                         font=('Segoe UI', 10, 'bold'),
                                         relief='flat', borderwidth=0,
                                         width=8, height=3,
                                         cursor='hand2', state=tk.DISABLED)
        self.host_present_btn.pack(side=tk.LEFT, padx=10)
        
        # Stop screen sharing button
        self.host_stop_screen_btn = tk.Button(media_frame, text="⏹️\nStop", 
                                             command=self.stop_host_screen_share,
                                             bg='#dc3545', fg='white', 
                                             font=('Segoe UI', 10, 'bold'),
                                             relief='flat', borderwidth=0,
                                             width=8, height=3,
                                             cursor='hand2', state=tk.DISABLED)
        self.host_stop_screen_btn.pack(side=tk.LEFT, padx=10)
        
        # Server info
        info_frame = tk.Frame(controls_frame, bg='#2d2d2d')
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.server_info_label = tk.Label(info_frame, text="Server Information", 
                                         font=('Segoe UI', 10), 
                                         fg='#888888', bg='#2d2d2d')
        self.server_info_label.pack()
        
    def add_button_hover_effects(self):
        """Add hover effects to buttons"""
        def on_enter(event, color='#0d6efd'):
            event.widget.configure(bg=color)
        
        def on_leave(event, color):
            event.widget.configure(bg=color)
        
        # Start server button hover
        if hasattr(self, 'start_server_btn'):
            self.start_server_btn.bind("<Enter>", lambda e: on_enter(e, '#0e6e0e'))
            self.start_server_btn.bind("<Leave>", lambda e: on_leave(e, '#107c10'))
        
        # Stop server button hover
        if hasattr(self, 'stop_server_btn'):
            self.stop_server_btn.bind("<Enter>", lambda e: on_enter(e, '#b71c1c'))
            self.stop_server_btn.bind("<Leave>", lambda e: on_leave(e, '#d13438'))
        
    def get_local_ip(self):
        """Get the local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
            
    def safe_button_update(self, button_name, **kwargs):
        """Safely update button configuration with error handling"""
        try:
            if hasattr(self, button_name):
                button = getattr(self, button_name)
                if button and hasattr(button, 'winfo_exists') and button.winfo_exists():
                    button.config(**kwargs)
                    return True
        except (tk.TclError, AttributeError) as e:
            print(f"Warning: Could not update {button_name}: {e}")
        except Exception as e:
            print(f"Error updating {button_name}: {e}")
        return False
            
    def log_message(self, message, log_type='info'):
        """Enhanced logging with different log types"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # Add to activity logs list
        self.activity_logs.append({
            'timestamp': timestamp,
            'message': message,
            'type': log_type
        })
        
        # Update GUI log display if it exists
        if hasattr(self, 'log_text') and self.log_text:
            try:
                display_entry = f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n"
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, display_entry)
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
            except:
                pass
        
        # Console output with color coding
        if log_type == 'error':
            print(f"ERROR: {log_entry}")
        elif log_type == 'warning':
            print(f"WARNING: {log_entry}")
        else:
            print(log_entry)
        if hasattr(self, 'activity_log_text'):
            self.activity_log_text.config(state=tk.NORMAL)
            self.activity_log_text.insert(tk.END, log_entry + "\n")
            self.activity_log_text.see(tk.END)
            self.activity_log_text.config(state=tk.DISABLED)
        
        print(log_entry)  # Console logging
        
    def apply_meeting_settings(self):
        """Apply meeting settings"""
        try:
            # Update meeting settings
            self.meeting_settings.update({
                'allow_video': self.allow_video_var.get(),
                'allow_audio': self.allow_audio_var.get(),
                'allow_screen_share': self.allow_screen_share_var.get(),
                'allow_file_sharing': self.allow_file_sharing_var.get(),
                'allow_chat': self.allow_chat_var.get(),
                'max_participants': int(self.max_participants_var.get()),
                'meeting_password': self.meeting_password_entry.get(),
                'waiting_room': self.waiting_room_var.get(),
                'mute_on_join': self.mute_on_join_var.get(),
                'video_off_on_join': self.video_off_on_join_var.get()
            })
            
            self.log_message("Meeting settings updated successfully")
            messagebox.showinfo("Settings Applied", "Meeting settings have been updated successfully!")
            
        except Exception as e:
            self.log_message(f"Error applying settings: {str(e)}")
            messagebox.showerror("Settings Error", f"Failed to apply settings: {str(e)}")
            
    def mute_all_participants(self):
        """Mute all participants"""
        try:
            mute_msg = {'type': 'force_mute_all'}
            self.broadcast_message(mute_msg)
            self.log_message("All participants muted by host")
            messagebox.showinfo("Action Complete", "All participants have been muted")
        except Exception as e:
            self.log_message(f"Error muting all participants: {str(e)}")
            
    def disable_all_video(self):
        """Disable video for all participants"""
        try:
            disable_video_msg = {'type': 'force_disable_video_all'}
            self.broadcast_message(disable_video_msg)
            self.log_message("Video disabled for all participants by host")
            messagebox.showinfo("Action Complete", "Video has been disabled for all participants")
        except Exception as e:
            self.log_message(f"Error disabling video for all participants: {str(e)}")
            
    def remove_all_participants(self):
        """Remove all participants"""
        if messagebox.askyesno("Confirm Action", "Are you sure you want to remove all participants?"):
            try:
                for client_id in list(self.clients.keys()):
                    self.disconnect_client(client_id)
                self.log_message("All participants removed by host")
                messagebox.showinfo("Action Complete", "All participants have been removed")
            except Exception as e:
                self.log_message(f"Error removing all participants: {str(e)}")
                
    def mute_selected_participant(self):
        """Mute selected participant"""
        selection = self.detailed_participants_tree.selection()
        if selection:
            item = self.detailed_participants_tree.item(selection[0])
            client_id = item['values'][0]
            try:
                mute_msg = {'type': 'force_mute', 'target_client': client_id}
                self.send_to_client(client_id, mute_msg)
                self.log_message(f"Participant {client_id} muted by host")
            except Exception as e:
                self.log_message(f"Error muting participant: {str(e)}")
        else:
            messagebox.showwarning("No Selection", "Please select a participant first")
            
    def disable_selected_video(self):
        """Disable video for selected participant"""
        selection = self.detailed_participants_tree.selection()
        if selection:
            item = self.detailed_participants_tree.item(selection[0])
            client_id = item['values'][0]
            try:
                disable_msg = {'type': 'force_disable_video', 'target_client': client_id}
                self.send_to_client(client_id, disable_msg)
                self.log_message(f"Video disabled for participant {client_id} by host")
            except Exception as e:
                self.log_message(f"Error disabling video: {str(e)}")
        else:
            messagebox.showwarning("No Selection", "Please select a participant first")
            
    def stop_selected_presenting(self):
        """Stop presenting for selected participant"""
        selection = self.detailed_participants_tree.selection()
        if selection:
            item = self.detailed_participants_tree.item(selection[0])
            client_id = item['values'][0]
            if self.presenter_id == int(client_id):
                try:
                    self.presenter_id = None
                    stop_msg = {'type': 'force_stop_presenting'}
                    self.send_to_client(client_id, stop_msg)
                    self.log_message(f"Presentation stopped for participant {client_id} by host")
                except Exception as e:
                    self.log_message(f"Error stopping presentation: {str(e)}")
            else:
                messagebox.showinfo("Not Presenting", "Selected participant is not currently presenting")
        else:
            messagebox.showwarning("No Selection", "Please select a participant first")
            
    def remove_selected_participant(self):
        """Remove selected participant"""
        selection = self.detailed_participants_tree.selection()
        if selection:
            item = self.detailed_participants_tree.item(selection[0])
            client_id = int(item['values'][0])
            client_name = item['values'][1]
            
            if messagebox.askyesno("Confirm Removal", f"Remove participant '{client_name}'?"):
                try:
                    self.disconnect_client(client_id)
                    self.log_message(f"Participant {client_name} removed by host")
                except Exception as e:
                    self.log_message(f"Error removing participant: {str(e)}")
        else:
            messagebox.showwarning("No Selection", "Please select a participant first")
    
    def request_client_audio(self):
        """Request selected client to turn on audio"""
        selection = self.detailed_participants_tree.selection()
        if selection:
            item = self.detailed_participants_tree.item(selection[0])
            client_id = int(item['values'][0])
            client_name = item['values'][1]
            
            if client_id == self.host_id:
                messagebox.showwarning("Invalid Selection", "Cannot request from Host")
                return
                
            # Send audio request to client
            request_msg = {
                'type': 'host_request',
                'request_type': 'audio',
                'message': f"Host is requesting you to turn on your microphone"
            }
            self.send_to_client(client_id, request_msg)
            self.log_message(f"Requested audio from {client_name}")
            messagebox.showinfo("Request Sent", f"Audio request sent to {client_name}")
        else:
            messagebox.showwarning("No Selection", "Please select a participant first")
    
    def request_client_video(self):
        """Request selected client to turn on video"""
        selection = self.detailed_participants_tree.selection()
        if selection:
            item = self.detailed_participants_tree.item(selection[0])
            client_id = int(item['values'][0])
            client_name = item['values'][1]
            
            if client_id == self.host_id:
                messagebox.showwarning("Invalid Selection", "Cannot request from Host")
                return
                
            # Send video request to client
            request_msg = {
                'type': 'host_request',
                'request_type': 'video',
                'message': f"Host is requesting you to turn on your camera"
            }
            self.send_to_client(client_id, request_msg)
            self.log_message(f"Requested video from {client_name}")
            messagebox.showinfo("Request Sent", f"Video request sent to {client_name}")
        else:
            messagebox.showwarning("No Selection", "Please select a participant first")
    
    def grant_client_permissions(self):
        """Grant permissions to selected client"""
        selection = self.detailed_participants_tree.selection()
        if selection:
            item = self.detailed_participants_tree.item(selection[0])
            client_id = int(item['values'][0])
            client_name = item['values'][1]
            
            if client_id == self.host_id:
                messagebox.showwarning("Invalid Selection", "Cannot grant permissions to Host")
                return
            
            if client_id in self.pending_requests:
                # Grant all pending permissions
                permissions = self.pending_requests[client_id]
                grant_msg = {
                    'type': 'permission_granted',
                    'permissions': permissions,
                    'message': f"Host has granted your permission requests"
                }
                self.send_to_client(client_id, grant_msg)
                
                # Remove from pending requests
                del self.pending_requests[client_id]
                self.update_requests_display()
                
                self.log_message(f"Granted permissions to {client_name}")
                messagebox.showinfo("Permissions Granted", f"Permissions granted to {client_name}")
            else:
                messagebox.showinfo("No Requests", f"No pending requests from {client_name}")
        else:
            messagebox.showwarning("No Selection", "Please select a participant first")
    
    def deny_client_permissions(self):
        """Deny permissions to selected client"""
        selection = self.detailed_participants_tree.selection()
        if selection:
            item = self.detailed_participants_tree.item(selection[0])
            client_id = int(item['values'][0])
            client_name = item['values'][1]
            
            if client_id == self.host_id:
                messagebox.showwarning("Invalid Selection", "Cannot deny permissions to Host")
                return
            
            if client_id in self.pending_requests:
                # Deny all pending permissions
                deny_msg = {
                    'type': 'permission_denied',
                    'message': f"Host has denied your permission requests"
                }
                self.send_to_client(client_id, deny_msg)
                
                # Remove from pending requests
                del self.pending_requests[client_id]
                self.update_requests_display()
                
                self.log_message(f"Denied permissions to {client_name}")
                messagebox.showinfo("Permissions Denied", f"Permissions denied to {client_name}")
            else:
                messagebox.showinfo("No Requests", f"No pending requests from {client_name}")
        else:
            messagebox.showwarning("No Selection", "Please select a participant first")
    
    def force_stop_screen_sharing(self):
        """Force stop screen sharing for selected participant"""
        selection = self.detailed_participants_tree.selection()
        if selection:
            item = self.detailed_participants_tree.item(selection[0])
            client_id = int(item['values'][0])
            client_name = item['values'][1]
            
            if client_id == self.host_id:
                messagebox.showwarning("Invalid Selection", "Cannot force action on Host")
                return
                
            # Send force stop screen sharing command
            force_msg = {
                'type': 'force_stop_screen_sharing',
                'message': f"Host has stopped your screen sharing"
            }
            self.send_to_client(client_id, force_msg)
            self.log_message(f"Forced stop screen sharing for {client_name}")
            messagebox.showinfo("Action Sent", f"Screen sharing stop command sent to {client_name}")
        else:
            messagebox.showwarning("No Selection", "Please select a participant first")
    
    def update_requests_display(self):
        """Update the pending requests display"""
        if hasattr(self, 'requests_text'):
            self.requests_text.config(state=tk.NORMAL)
            self.requests_text.delete(1.0, tk.END)
            
            if self.pending_requests:
                for client_id, requests in self.pending_requests.items():
                    client_name = self.clients.get(client_id, {}).get('name', f'Client {client_id}')
                    request_types = []
                    if requests.get('audio'):
                        request_types.append('🎤 Audio')
                    if requests.get('video'):
                        request_types.append('📹 Video')
                    if requests.get('screen'):
                        request_types.append('🖥️ Screen Share')
                    
                    if request_types:
                        self.requests_text.insert(tk.END, f"{client_name}: {', '.join(request_types)}\n")
            else:
                self.requests_text.insert(tk.END, "No pending requests")
            
            self.requests_text.config(state=tk.DISABLED)
            
    def get_ephemeral_port(self):
        """Get next available ephemeral port for file transfers"""
        port = self.file_transfer['next_ephemeral_port']
        self.file_transfer['next_ephemeral_port'] += 1
        return port
        
    def handle_file_offer(self, client_id, message):
        """Handle file upload offer from client"""
        try:
            filename = message.get('filename', '')
            size = message.get('size', 0)
            fid = message.get('fid', '')
            
            if not fid or not filename or size <= 0:
                error_msg = create_error_message("Invalid file offer: missing fid, filename, or size")
                self.send_to_client(client_id, error_msg)
                return
                
            if size > self.file_transfer['max_file_size']:
                error_msg = create_error_message(f"File too large: {size} bytes (max: {self.file_transfer['max_file_size']} bytes)")
                self.send_to_client(client_id, error_msg)
                return
                
            client_name = self.clients[client_id]['name']
            self.log_message(f"File offer from {client_name}: {filename} ({size} bytes)")
            
            # Allocate ephemeral port for upload
            upload_port = self.get_ephemeral_port()
            
            # Store session info
            session_info = {
                'fid': fid,
                'filename': filename,
                'size': size,
                'uploader': client_name,
                'uploader_uid': client_id,
                'port': upload_port,
                'type': 'upload'
            }
            
            self.file_sessions[upload_port] = session_info
            
            # Start upload server thread
            upload_thread = threading.Thread(
                target=self.handle_file_upload_server,
                args=(upload_port, session_info),
                daemon=True
            )
            upload_thread.start()
            
            # Send upload port to client
            response_msg = {
                'type': MessageTypes.FILE_UPLOAD_PORT,
                'fid': fid,
                'port': upload_port
            }
            self.send_to_client(client_id, response_msg)
            
        except Exception as e:
            self.log_message(f"Error handling file offer: {str(e)}", 'error')
            error_msg = create_error_message(f"File offer failed: {str(e)}")
            self.send_to_client(client_id, error_msg)
            
    def handle_file_request(self, client_id, message):
        """Handle file download request from client"""
        try:
            fid = message.get('fid', '')
            
            if not fid:
                error_msg = create_error_message("Invalid file request: missing fid")
                self.send_to_client(client_id, error_msg)
                return
                
            # Check if file exists
            if fid not in self.shared_files:
                error_msg = create_error_message(f"File not found: fid={fid}")
                self.send_to_client(client_id, error_msg)
                return
                
            file_info = self.shared_files[fid]
            client_name = self.clients[client_id]['name']
            
            self.log_message(f"File request from {client_name}: {file_info['filename']}")
            
            # Allocate ephemeral port for download
            download_port = self.get_ephemeral_port()
            
            # Store session info
            session_info = {
                'fid': fid,
                'filename': file_info['filename'],
                'size': file_info['size'],
                'file_path': file_info['path'],
                'requester': client_name,
                'requester_uid': client_id,
                'port': download_port,
                'type': 'download'
            }
            
            self.file_sessions[download_port] = session_info
            
            # Start download server thread
            download_thread = threading.Thread(
                target=self.handle_file_download_server,
                args=(download_port, session_info),
                daemon=True
            )
            download_thread.start()
            
            # Send download port to client
            response_msg = {
                'type': MessageTypes.FILE_DOWNLOAD_PORT,
                'fid': fid,
                'filename': file_info['filename'],
                'size': file_info['size'],
                'port': download_port
            }
            self.send_to_client(client_id, response_msg)
            
        except Exception as e:
            self.log_message(f"Error handling file request: {str(e)}", 'error')
            error_msg = create_error_message(f"File request failed: {str(e)}")
            self.send_to_client(client_id, error_msg)
            
    def handle_file_upload_server(self, port, session_info):
        """Handle file upload on ephemeral port"""
        try:
            # Create TCP server for file upload
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, port))
            server_socket.listen(1)
            server_socket.settimeout(300)  # 5 minute timeout
            
            self.log_message(f"Upload server listening on port {port}")
            
            # Accept connection
            client_socket, addr = server_socket.accept()
            self.log_message(f"Upload connection from {addr}")
            
            # Receive file
            fid = session_info['fid']
            filename = session_info['filename']
            expected_size = session_info['size']
            uploader = session_info['uploader']
            
            file_path = os.path.join(self.file_transfer['upload_dir'], filename)
            bytes_received = 0
            
            with open(file_path, 'wb') as f:
                while bytes_received < expected_size:
                    chunk_size = min(self.file_transfer['chunk_size'], expected_size - bytes_received)
                    data = client_socket.recv(chunk_size)
                    
                    if not data:
                        break
                        
                    f.write(data)
                    bytes_received += len(data)
                    
                    # Log progress
                    if bytes_received % (1024 * 1024) < self.file_transfer['chunk_size']:  # Every 1MB
                        progress = (bytes_received / expected_size) * 100
                        self.log_message(f"Upload progress [{filename}]: {bytes_received}/{expected_size} bytes ({progress:.1f}%)")
            
            client_socket.close()
            server_socket.close()
            
            if bytes_received == expected_size:
                # Store file metadata
                file_metadata = {
                    'fid': fid,
                    'filename': filename,
                    'size': bytes_received,
                    'uploader': uploader,
                    'uploader_uid': session_info['uploader_uid'],
                    'path': file_path,
                    'uploaded_at': datetime.now().isoformat()
                }
                
                self.shared_files[fid] = file_metadata
                
                # Broadcast file availability
                file_available_msg = {
                    'type': MessageTypes.FILE_AVAILABLE,
                    'fid': fid,
                    'filename': filename,
                    'size': bytes_received,
                    'uploader': uploader,
                    'timestamp': datetime.now().isoformat()
                }
                self.broadcast_message(file_available_msg)
                
                self.log_message(f"File upload completed: {filename} ({bytes_received} bytes)")
                self.update_files_display()
            else:
                self.log_message(f"Upload incomplete: {bytes_received}/{expected_size} bytes", 'error')
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
        except Exception as e:
            self.log_message(f"Error in upload server: {str(e)}", 'error')
        finally:
            # Clean up session
            if port in self.file_sessions:
                del self.file_sessions[port]
                
    def handle_file_download_server(self, port, session_info):
        """Handle file download on ephemeral port"""
        try:
            # Create TCP server for file download
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, port))
            server_socket.listen(1)
            server_socket.settimeout(300)  # 5 minute timeout
            
            self.log_message(f"Download server listening on port {port}")
            
            # Accept connection
            client_socket, addr = server_socket.accept()
            self.log_message(f"Download connection from {addr}")
            
            # Send file
            filename = session_info['filename']
            file_path = session_info['file_path']
            file_size = session_info['size']
            requester = session_info['requester']
            
            if not os.path.exists(file_path):
                self.log_message(f"File not found: {file_path}", 'error')
                client_socket.close()
                server_socket.close()
                return
                
            bytes_sent = 0
            
            with open(file_path, 'rb') as f:
                while bytes_sent < file_size:
                    data = f.read(self.file_transfer['chunk_size'])
                    if not data:
                        break
                        
                    client_socket.send(data)
                    bytes_sent += len(data)
                    
                    # Log progress
                    if bytes_sent % (1024 * 1024) < self.file_transfer['chunk_size']:  # Every 1MB
                        progress = (bytes_sent / file_size) * 100
                        self.log_message(f"Download progress [{filename}]: {bytes_sent}/{file_size} bytes ({progress:.1f}%)")
            
            client_socket.close()
            server_socket.close()
            
            self.log_message(f"File download completed: {filename} to {requester}")
            
        except Exception as e:
            self.log_message(f"Error in download server: {str(e)}", 'error')
        finally:
            # Clean up session
            if port in self.file_sessions:
                del self.file_sessions[port]
                
    def add_private_message_to_gui(self, message):
        """Add private message to server GUI"""
        if hasattr(self, 'chat_display'):
            try:
                timestamp = datetime.now().strftime("%H:%M")
                sender = message.get('from_username', 'Unknown')
                text = message.get('text', '')
                
                chat_line = f"[PRIVATE] {sender} • {timestamp}\n{text}\n\n"
                
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.insert(tk.END, chat_line)
                self.chat_display.see(tk.END)
                self.chat_display.config(state=tk.DISABLED)
            except Exception as e:
                print(f"Error adding private message to GUI: {e}")
    
    def handle_permission_request(self, client_id, request_type):
        """Handle incoming permission request from client"""
        if client_id not in self.pending_requests:
            self.pending_requests[client_id] = {'audio': False, 'video': False, 'screen': False}
        
        self.pending_requests[client_id][request_type] = True
        
        client_name = self.clients.get(client_id, {}).get('name', f'Client {client_id}')
        self.log_message(f"{client_name} requested {request_type} permission")
        
        # Update the requests display
        self.update_requests_display()
        
        # Show notification to host
        messagebox.showinfo("Permission Request", 
                           f"{client_name} is requesting {request_type} permission.\n"
                           f"Go to Settings > Participants to grant or deny.")
            
    def export_logs(self):
        """Export activity logs to file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Activity Logs"
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write("LAN Meeting Server - Activity Logs\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for log_entry in self.activity_logs:
                        f.write(f"[{log_entry['timestamp']}] {log_entry['message']}\n")
                        
                self.log_message(f"Activity logs exported to {filename}")
                messagebox.showinfo("Export Complete", f"Logs exported to {filename}")
                
        except Exception as e:
            self.log_message(f"Error exporting logs: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export logs: {str(e)}")
            
    def clear_logs(self):
        """Clear activity logs"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all activity logs?"):
            try:
                self.activity_logs.clear()
                if hasattr(self, 'activity_log_text'):
                    self.activity_log_text.config(state=tk.NORMAL)
                    self.activity_log_text.delete(1.0, tk.END)
                    self.activity_log_text.config(state=tk.DISABLED)
                self.log_message("Activity logs cleared by host")
            except Exception as e:
                self.log_message(f"Error clearing logs: {str(e)}")
                
    def share_file_as_host(self):
        """Share file as host"""
        try:
            filename = filedialog.askopenfilename(
                title="Select file to share",
                filetypes=[("All files", "*.*")]
            )
            
            if filename:
                file_info = {
                    'name': os.path.basename(filename),
                    'size': os.path.getsize(filename),
                    'shared_by': 'Host',
                    'share_time': datetime.now().isoformat(),
                    'downloads': 0,
                    'path': filename
                }
                
                self.shared_files[file_info['name']] = file_info
                self.update_files_display()
                
                # Notify clients
                file_notification = {
                    'type': 'file_shared',
                    'file_info': file_info
                }
                self.broadcast_message(file_notification)
                
                self.log_message(f"Host shared file: {file_info['name']}")
                
        except Exception as e:
            self.log_message(f"Error sharing file: {str(e)}")
            messagebox.showerror("File Share Error", f"Failed to share file: {str(e)}")
            
    def clear_all_files(self):
        """Clear all shared files"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all shared files?"):
            try:
                self.shared_files.clear()
                self.update_files_display()
                
                # Notify clients
                clear_msg = {'type': 'files_cleared'}
                self.broadcast_message(clear_msg)
                
                self.log_message("All shared files cleared by host")
            except Exception as e:
                self.log_message(f"Error clearing files: {str(e)}")
                
    def update_files_display(self):
        """Update files display"""
        if hasattr(self, 'files_tree'):
            # Clear existing items
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)
                
            # Add files
            for file_info in self.shared_files.values():
                size_mb = f"{file_info['size'] / (1024*1024):.2f} MB"
                share_time = datetime.fromisoformat(file_info['share_time']).strftime("%H:%M:%S")
                
                self.files_tree.insert('', 'end', values=(
                    file_info['name'],
                    size_mb,
                    file_info['shared_by'],
                    share_time,
                    file_info['downloads']
                ))
        
    def start_server(self):
        """Start the communication server"""
        try:
            # Create TCP socket for control communications
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.bind((self.host, self.tcp_port))
            self.tcp_socket.listen(10)
            
            # Create UDP socket for video streaming
            self.udp_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_video_socket.bind((self.host, self.udp_video_port))
            
            # Create UDP socket for audio streaming
            self.udp_audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_audio_socket.bind((self.host, self.udp_audio_port))
            
            self.running = True
            
            # Start server threads
            threading.Thread(target=self.accept_tcp_clients, daemon=True).start()
            threading.Thread(target=self.handle_udp_video, daemon=True).start()
            threading.Thread(target=self.handle_udp_audio, daemon=True).start()
            threading.Thread(target=self.process_messages, daemon=True).start()
            
            # Update GUI
            self.start_server_btn.config(state=tk.DISABLED)
            self.stop_server_btn.config(state=tk.NORMAL)
            self.server_status_label.config(text="● Server Running")
            
            # Enable host controls with error handling
            try:
                if hasattr(self, 'host_video_btn') and self.host_video_btn and self.host_video_btn.winfo_exists():
                    self.host_video_btn.config(state=tk.NORMAL)
            except (tk.TclError, AttributeError):
                pass
                
            try:
                if hasattr(self, 'host_mic_btn') and self.host_mic_btn and self.host_mic_btn.winfo_exists():
                    self.host_mic_btn.config(state=tk.NORMAL)
            except (tk.TclError, AttributeError):
                pass
                
            try:
                if hasattr(self, 'host_speaker_btn') and self.host_speaker_btn and self.host_speaker_btn.winfo_exists():
                    self.host_speaker_btn.config(state=tk.NORMAL)
            except (tk.TclError, AttributeError):
                pass
                
            try:
                if hasattr(self, 'host_present_btn') and self.host_present_btn and self.host_present_btn.winfo_exists():
                    self.host_present_btn.config(state=tk.NORMAL)
            except (tk.TclError, AttributeError):
                pass
                
            try:
                if hasattr(self, 'chat_entry') and self.chat_entry and self.chat_entry.winfo_exists():
                    self.chat_entry.config(state=tk.NORMAL)
            except (tk.TclError, AttributeError):
                pass
                
            try:
                if hasattr(self, 'chat_send_btn') and self.chat_send_btn and self.chat_send_btn.winfo_exists():
                    self.chat_send_btn.config(state=tk.NORMAL)
            except (tk.TclError, AttributeError):
                pass
            
            self.log_message("Server started successfully")
            self.log_message(f"Listening on {self.get_local_ip()}:{self.tcp_port}")
            
            # Update server info
            self.server_info_label.config(text=f"🌐 Server: {self.get_local_ip()}:{self.tcp_port}")
            self.participants_count_label.config(text="👥 Participants: 1")
            
            # Update UI
            self.start_server_btn.config(state=tk.DISABLED)
            self.stop_server_btn.config(state=tk.NORMAL)
            
            # Auto-start speaker for receiving audio (after a short delay)
            self.root.after(1000, self.start_host_speaker)
            self.server_status_label.config(text="● Server Running", fg='#51cf66')
            
            # Add Host to the session
            self.add_host_to_session()
            
            # Update server info
            self.server_info_label.config(text=f"🌐 Server: {self.get_local_ip()}:{self.tcp_port} | 👥 Participants: 1")
            
        except Exception as e:
            self.log_message(f"Failed to start server: {str(e)}")
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
            
    def accept_tcp_clients(self):
        """Accept incoming TCP client connections"""
        while self.running:
            try:
                client_socket, address = self.tcp_socket.accept()
                client_id = self.next_client_id
                self.next_client_id += 1
                
                # Create client info
                join_time = datetime.now().strftime("%H:%M:%S")
                client_info = {
                    'id': client_id,
                    'socket': client_socket,
                    'address': address,
                    'name': f'Client_{client_id}',
                    'status': 'Connected',
                    'video_enabled': False,
                    'audio_enabled': False,
                    'last_seen': time.time(),
                    'join_time': join_time
                }
                
                self.clients[client_id] = client_info
                
                # Log participant join
                self.participant_logs[client_id] = {
                    'join_time': datetime.now().isoformat(),
                    'name': f'Client_{client_id}',
                    'ip': address[0]
                }
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self.handle_tcp_client, 
                    args=(client_id,), 
                    daemon=True
                )
                client_thread.start()
                self.client_threads.append(client_thread)
                
                self.log_message(f"Client {client_id} connected from {address[0]}")
                self.update_clients_display()
                self.update_server_info()
                self.update_video_grid()
                
            except Exception as e:
                if self.running:
                    self.log_message(f"Error accepting client: {str(e)}")
                break
                
    def handle_tcp_client(self, client_id):
        """Handle TCP communication with a specific client"""
        client_info = self.clients[client_id]
        client_socket = client_info['socket']
        
        try:
            while self.running and client_id in self.clients:
                # Receive message length first
                length_data = client_socket.recv(4)
                if not length_data:
                    break
                    
                message_length = struct.unpack('!I', length_data)[0]
                
                # Receive the actual message
                message_data = b''
                while len(message_data) < message_length:
                    chunk = client_socket.recv(message_length - len(message_data))
                    if not chunk:
                        break
                    message_data += chunk
                
                if len(message_data) != message_length:
                    break
                    
                # Parse message
                try:
                    message = json.loads(message_data.decode('utf-8'))
                    self.process_client_message(client_id, message)
                except json.JSONDecodeError:
                    self.log_message(f"Invalid JSON from client {client_id}")
                    
        except Exception as e:
            self.log_message(f"Error handling client {client_id}: {str(e)}")
        finally:
            self.disconnect_client(client_id)
            
    def process_client_message(self, client_id, message):
        """Process incoming message from client with enhanced protocol handling"""
        msg_type = message.get('type')
        
        # Validate message type
        if not msg_type or not isinstance(msg_type, str):
            self.send_to_client(client_id, create_error_message("Invalid message type"))
            return
        
        # Update client's last activity
        if client_id in self.clients:
            self.clients[client_id]['last_seen'] = time.time()
        
        # Handle different message types
        if msg_type == MessageTypes.LOGIN or msg_type == 'join':
            # Client joining with name
            client_name = message.get('name', f'Client_{client_id}')
            self.clients[client_id]['name'] = client_name
            self.clients[client_id]['status'] = 'Active'
            
            # Send welcome message and current session state
            all_participants = {
                str(self.host_id): {
                    'name': self.host_name, 
                    'status': 'Active',
                    'video_enabled': self.host_video_enabled,
                    'audio_enabled': self.host_audio_enabled
                }
            }
            
            # Add other clients
            for cid, info in self.clients.items():
                all_participants[str(cid)] = {
                    'name': info['name'], 
                    'status': info['status'],
                    'video_enabled': info.get('video_enabled', False),
                    'audio_enabled': info.get('audio_enabled', False)
                }
            
            welcome_msg = {
                'type': MessageTypes.LOGIN_SUCCESS,
                'client_id': client_id,
                'clients': all_participants,
                'chat_history': self.chat_history,
                'presenter_id': self.presenter_id,
                'host_id': self.host_id,
                'shared_files': self.shared_files,  # Include shared files list
                'timestamp': datetime.now().isoformat()
            }
            self.send_to_client(client_id, welcome_msg)
            
            # Notify other clients
            join_notification = create_user_joined_message(client_id, client_name)
            self.broadcast_message(join_notification, exclude=client_id)
            
            self.log_message(f"Client {client_id} ({client_name}) joined the session")
            self.update_clients_display()
            
        elif msg_type == MessageTypes.CHAT or msg_type == 'chat':
            # Regular chat message (public)
            chat_text = message.get('message', '').strip()
            if not chat_text:
                return
                
            chat_msg = create_chat_message(
                client_id, 
                self.clients[client_id]['name'], 
                chat_text
            )
            
            self.chat_history.append(chat_msg)
            self.message_history.append(chat_msg)
            self.broadcast_message(chat_msg)
            self.log_message(f"Chat from {self.clients[client_id]['name']}: {chat_text}")
            
        elif msg_type == MessageTypes.BROADCAST or msg_type == 'broadcast':
            # Broadcast message (public announcement)
            broadcast_text = message.get('text', '').strip()
            if not broadcast_text:
                return
                
            broadcast_msg = {
                'type': MessageTypes.BROADCAST,
                'uid': client_id,
                'username': self.clients[client_id]['name'],
                'text': broadcast_text,
                'timestamp': datetime.now().isoformat()
            }
            
            self.message_history.append(broadcast_msg)
            self.broadcast_message(broadcast_msg)
            self.log_message(f"Broadcast from {self.clients[client_id]['name']}: {broadcast_text}")
            
        elif msg_type == MessageTypes.UNICAST or msg_type == 'unicast':
            # Private message (unicast)
            target_uid = message.get('target_uid')
            unicast_text = message.get('text', '').strip()
            
            if not target_uid or not unicast_text:
                self.send_to_client(client_id, create_error_message("Invalid unicast: missing target_uid or text"))
                return
                
            if target_uid not in self.clients and target_uid != self.host_id:
                self.send_to_client(client_id, create_error_message(f"Target user not found: {target_uid}"))
                return
                
            unicast_msg = {
                'type': MessageTypes.UNICAST,
                'from_uid': client_id,
                'from_username': self.clients[client_id]['name'],
                'to_uid': target_uid,
                'to_username': self.clients.get(target_uid, {}).get('name', 'Host'),
                'text': unicast_text,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in private message history
            if client_id not in self.private_messages:
                self.private_messages[client_id] = []
            if target_uid not in self.private_messages:
                self.private_messages[target_uid] = []
                
            self.private_messages[client_id].append(unicast_msg)
            self.private_messages[target_uid].append(unicast_msg)
            
            # Send to target
            if target_uid == self.host_id:
                # Message to host - display in server GUI
                self.add_private_message_to_gui(unicast_msg)
            else:
                self.send_to_client(target_uid, unicast_msg)
            
            # Send confirmation to sender
            confirmation_msg = {
                'type': MessageTypes.UNICAST_SENT,
                'to_uid': target_uid,
                'to_username': self.clients.get(target_uid, {}).get('name', 'Host'),
                'message': 'Private message sent successfully'
            }
            self.send_to_client(client_id, confirmation_msg)
            
            self.log_message(f"Private message from {self.clients[client_id]['name']} to {self.clients.get(target_uid, {}).get('name', 'Host')}")
            
        elif msg_type == MessageTypes.HEARTBEAT or msg_type == 'heartbeat':
            # Heartbeat message
            heartbeat_ack = create_heartbeat_ack_message()
            self.send_to_client(client_id, heartbeat_ack)
            
        elif msg_type == 'request_presenter':
            # Request to become presenter
            if self.presenter_id is None:
                self.presenter_id = client_id
                presenter_msg = {
                    'type': 'presenter_granted',
                    'client_id': client_id
                }
                self.send_to_client(client_id, presenter_msg)
                
                # Notify others
                presenter_notification = {
                    'type': 'presenter_changed',
                    'presenter_id': client_id,
                    'presenter_name': self.clients[client_id]['name']
                }
                self.broadcast_message(presenter_notification, exclude=client_id)
                
                self.log_message(f"{self.clients[client_id]['name']} became presenter")
            else:
                # Presenter role already taken
                denied_msg = {
                    'type': 'presenter_denied',
                    'reason': 'Presenter role already taken'
                }
                self.send_to_client(client_id, denied_msg)
        
        elif msg_type == 'permission_request':
            # Client requesting permission for audio/video/screen
            request_type = message.get('request_type')  # 'audio', 'video', or 'screen'
            if request_type in ['audio', 'video', 'screen']:
                self.handle_permission_request(client_id, request_type)
                
        elif msg_type == MessageTypes.FILE_OFFER or msg_type == 'file_offer':
            # Client offering to upload a file
            self.handle_file_offer(client_id, message)
            
        elif msg_type == MessageTypes.FILE_REQUEST or msg_type == 'file_request':
            # Client requesting to download a file
            self.handle_file_request(client_id, message)
            
        elif msg_type == 'force_action_response':
            # Client responding to host's force action (like force mute/disable video)
            action = message.get('action')
            success = message.get('success', False)
            client_name = self.clients[client_id]['name']
            
            if success:
                self.log_message(f"{client_name} complied with host action: {action}")
            else:
                self.log_message(f"{client_name} failed to comply with host action: {action}")
                
        elif msg_type == 'media_status_update':
            # Client updating their media status
            if client_id in self.clients:
                self.clients[client_id]['video_enabled'] = message.get('video_enabled', False)
                self.clients[client_id]['audio_enabled'] = message.get('audio_enabled', False)
                self.clients[client_id]['screen_share_enabled'] = message.get('screen_share_enabled', False)
                self.update_clients_display()
                
        elif msg_type == 'stop_presenting':
            # Stop presenting
            if self.presenter_id == client_id:
                self.presenter_id = None
                stop_msg = {
                    'type': 'presentation_stopped',
                    'former_presenter': client_id
                }
                self.broadcast_message(stop_msg)
                self.log_message(f"{self.clients[client_id]['name']} stopped presenting")
                
        elif msg_type == 'screen_frame':
            # Client sending screen frame for sharing
            if self.presenter_id == client_id:
                # Broadcast screen frame to all other clients
                screen_msg = {
                    'type': 'screen_frame',
                    'presenter_id': client_id,
                    'frame_data': message.get('frame_data')
                }
                self.broadcast_message(screen_msg, exclude=client_id)
                
                # Display on server if needed
                try:
                    frame_data = base64.b64decode(message.get('frame_data', ''))
                    if frame_data:
                        img = Image.open(io.BytesIO(frame_data))
                        frame_rgb = np.array(img)
                        
                        # Put frame in server's screen queue for display
                        if hasattr(self, 'screen_frame_queue'):
                            try:
                                while self.screen_frame_queue.qsize() > 1:
                                    try:
                                        self.screen_frame_queue.get_nowait()
                                    except queue.Empty:
                                        break
                                self.screen_frame_queue.put_nowait(frame_rgb)
                            except queue.Full:
                                pass
                except Exception as e:
                    print(f"Error processing client screen frame on server: {e}")
                
        elif msg_type == 'video_status':
            # Video enable/disable status
            self.clients[client_id]['video_enabled'] = message.get('enabled', False)
            status_msg = {
                'type': 'client_video_status',
                'client_id': client_id,
                'enabled': message.get('enabled', False)
            }
            self.broadcast_message(status_msg, exclude=client_id)
            
            # Update video grid display
            self.update_client_video_display(client_id)
            
        elif msg_type == 'audio_status':
            # Audio enable/disable status
            self.clients[client_id]['audio_enabled'] = message.get('enabled', False)
            status_msg = {
                'type': 'client_audio_status',
                'client_id': client_id,
                'enabled': message.get('enabled', False)
            }
            self.broadcast_message(status_msg, exclude=client_id)
            
        elif msg_type == 'share_file':
            # Client sharing a file
            file_info = message.get('file_info', {})
            if file_info:
                self.shared_files[file_info['name']] = file_info
                self.update_files_display()
                
                # Notify all clients
                file_notification = {
                    'type': 'file_shared',
                    'file_info': file_info
                }
                self.broadcast_message(file_notification)
                
                self.log_message(f"File '{file_info['name']}' shared by {self.clients[client_id]['name']}")
                
        elif msg_type == 'file_downloaded':
            # Client downloaded a file
            file_name = message.get('file_name')
            if file_name in self.shared_files:
                self.shared_files[file_name]['downloads'] += 1
                self.update_files_display()
                self.log_message(f"File '{file_name}' downloaded by {self.clients[client_id]['name']}")
                
        elif msg_type == 'get_files_list':
            # Client requesting current files list
            files_list_msg = {
                'type': 'files_list_update',
                'shared_files': self.shared_files,
                'timestamp': datetime.now().isoformat()
            }
            self.send_to_client(client_id, files_list_msg)
            self.log_message(f"Sent files list to client {client_id} ({len(self.shared_files)} files)")
            
        # Update last seen time
        self.clients[client_id]['last_seen'] = time.time()
        
    def send_to_client(self, client_id, message):
        """Send message to specific client"""
        if client_id not in self.clients:
            return
            
        try:
            client_socket = self.clients[client_id]['socket']
            message_data = json.dumps(message).encode('utf-8')
            message_length = struct.pack('!I', len(message_data))
            
            client_socket.send(message_length + message_data)
        except Exception as e:
            self.log_message(f"Error sending to client {client_id}: {str(e)}")
            self.disconnect_client(client_id)
            
    def broadcast_message(self, message, exclude=None):
        """Broadcast message to all connected clients"""
        for client_id in list(self.clients.keys()):
            if exclude is None or client_id != exclude:
                self.send_to_client(client_id, message)
                
    def handle_udp_video(self):
        """Handle UDP video streaming"""
        while self.running:
            try:
                data, address = self.udp_video_socket.recvfrom(65536)
                
                # Parse video packet header
                if len(data) < 12:
                    continue
                    
                client_id, sequence, frame_size = struct.unpack('!III', data[:12])
                frame_data = data[12:]
                
                # Validate frame data
                if len(frame_data) == frame_size and client_id in self.clients:
                    # print(f"Server received video from client {client_id}, size: {frame_size}")
                    # Update server display for this client's video
                    try:
                        self.update_client_video_display(client_id, frame_data)
                        # print(f"Server updated display for client {client_id}")
                    except Exception as e:
                        print(f"Error updating client video display: {e}")
                
                # Broadcast to other clients (excluding sender)
                for cid, client_info in self.clients.items():
                    if cid != client_id and client_info.get('video_enabled', False):
                        try:
                            client_address = (client_info['address'][0], self.udp_video_port)
                            self.udp_video_socket.sendto(data, client_address)
                        except:
                            pass
                            
            except Exception as e:
                if self.running:
                    self.log_message(f"UDP video error: {str(e)}")
                    
    def handle_udp_audio(self):
        """Handle UDP audio streaming"""
        audio_buffer = {}  # Buffer for mixing audio
        
        while self.running:
            try:
                data, address = self.udp_audio_socket.recvfrom(4096)
                
                # Parse audio packet
                if len(data) < 8:
                    continue
                    
                client_id, timestamp = struct.unpack('!II', data[:8])
                audio_data = data[8:]
                
                # Debug: Show audio reception
                # print(f"Server received audio from client {client_id}, {len(audio_data)} bytes")
                
                # Play audio on server if host speaker is enabled
                if self.host_speaker_enabled and hasattr(self, 'audio_output_stream') and self.audio_output_stream:
                    try:
                        if self.audio_output_stream.is_active():
                            self.audio_output_stream.write(audio_data)
                            # print(f"Server playing audio from client {client_id}")
                    except Exception as e:
                        print(f"Error playing client audio on server: {e}")
                else:
                    # Debug: Show why audio isn't being played
                    if not self.host_speaker_enabled:
                        print(f"Server received audio from client {client_id} but host speaker is disabled")
                    elif not hasattr(self, 'audio_output_stream'):
                        print(f"Server received audio from client {client_id} but no output stream")
                    elif not self.audio_output_stream:
                        print(f"Server received audio from client {client_id} but output stream is None")
                
                # Broadcast to other clients (excluding sender)
                broadcast_count = 0
                for cid, client_info in self.clients.items():
                    if cid != client_id:  # Don't send back to sender
                        try:
                            client_address = (client_info['address'][0], self.udp_audio_port)
                            self.udp_audio_socket.sendto(data, client_address)
                            broadcast_count += 1
                            print(f"Audio broadcasted to client {cid}")
                        except Exception as e:
                            print(f"Error broadcasting audio to client {cid}: {e}")
                
                if broadcast_count > 0:
                    # print(f"Audio from client {client_id} broadcasted to {broadcast_count} clients")
                    pass
                            
            except Exception as e:
                if self.running:
                    self.log_message(f"UDP audio error: {str(e)}")
                    
    def process_messages(self):
        """Process queued messages"""
        while self.running:
            try:
                # Reduced frequency to prevent GUI interference
                time.sleep(0.5)  # Check less frequently
            except:
                break
                
    def disconnect_client(self, client_id):
        """Disconnect a client"""
        if client_id not in self.clients:
            return
            
        client_info = self.clients[client_id]
        client_name = client_info['name']
        
        try:
            client_info['socket'].close()
        except:
            pass
            
        # Remove from clients
        del self.clients[client_id]
        
        # If this was the presenter, clear presenter role
        if self.presenter_id == client_id:
            self.presenter_id = None
            stop_msg = {
                'type': 'presentation_stopped',
                'former_presenter': client_id
            }
            self.broadcast_message(stop_msg)
            
        # Notify other clients
        leave_notification = {
            'type': 'user_left',
            'client_id': client_id,
            'name': client_name
        }
        self.broadcast_message(leave_notification)
        
        self.log_message(f"Client {client_id} ({client_name}) disconnected")
        self.update_clients_display()
        self.update_server_info()
        self.update_video_grid()
        
    def add_host_to_session(self):
        """Add Host as a participant in the session"""
        # Add Host to chat history
        host_join_msg = {
            'type': 'chat',
            'client_id': self.host_id,
            'name': self.host_name,
            'message': 'Host has joined the meeting',
            'timestamp': datetime.now().isoformat()
        }
        self.chat_history.append(host_join_msg)
        self.update_chat_display()
        
        self.log_message("Host joined the session as a participant")
        
    def update_clients_display(self):
        """Update the participants display in all tabs"""
        total_participants = len(self.clients) + 1  # +1 for Host
        
        # Update main participants listbox with enhanced info
        if hasattr(self, 'participants_listbox'):
            self.participants_listbox.delete(0, tk.END)
            
            # Add Host first with enhanced status
            host_status = "🏠 Host"
            if self.host_video_enabled:
                host_status += " 📹"
            if self.host_audio_enabled:
                host_status += " 🎤"
            if self.host_screen_share_enabled:
                host_status += " 🖥️"
            if self.presenter_id == self.host_id:
                host_status += " [Presenter]"
            
            self.participants_listbox.insert(tk.END, host_status)
            
            # Add current clients with enhanced status
            for client_id, client_info in self.clients.items():
                name = client_info['name']
                status = f"👤 {name}"
                
                if client_info.get('video_enabled'):
                    status += " 📹"
                if client_info.get('audio_enabled'):
                    status += " 🎤"
                if self.presenter_id == client_id:
                    status += " [Presenter]"
                
                # Add IP address for reference
                status += f" ({client_info['address'][0]})"
                
                self.participants_listbox.insert(tk.END, status)
        
        # Update detailed participants tree
        if hasattr(self, 'detailed_participants_tree'):
            # Clear existing items
            for item in self.detailed_participants_tree.get_children():
                self.detailed_participants_tree.delete(item)
            
            # Add Host
            self.detailed_participants_tree.insert('', 'end', values=(
                self.host_id,
                "Host",
                "Server",
                datetime.now().strftime("%H:%M:%S") if self.running else "N/A",
                "Active",
                "✅" if self.host_video_enabled else "❌",
                "✅" if self.host_audio_enabled else "❌",
                "✅" if self.host_screen_share_enabled else "❌",
                "Host Controls"
            ))
            
            # Add clients
            for client_id, client_info in self.clients.items():
                self.detailed_participants_tree.insert('', 'end', values=(
                    client_id,
                    client_info['name'],
                    client_info['address'][0],
                    client_info.get('join_time', 'Unknown'),
                    client_info['status'],
                    "✅" if client_info.get('video_enabled') else "❌",
                    "✅" if client_info.get('audio_enabled') else "❌",
                    "Available"
                ))
        
        # Update participant counts and statistics
        if hasattr(self, 'participants_count_label'):
            self.participants_count_label.config(text=f"👥 Participants: {total_participants}")
        
        # Update chat messages count
        if hasattr(self, 'chat_messages_count_label'):
            self.chat_messages_count_label.config(text=f"💬 Messages: {len(self.chat_history)}")
        
        # Update files shared count
        if hasattr(self, 'files_shared_count_label'):
            self.files_shared_count_label.config(text=f"📁 Files: {len(self.shared_files)}")
        
        # Update server info
        if self.running and hasattr(self, 'server_info_label'):
            self.server_info_label.config(text=f"🌐 Server: {self.get_local_ip()}:{self.tcp_port}")
            
        # Update video grid
        self.update_video_grid()
            
    def update_video_grid(self):
        """Update the dynamic video grid layout"""
        if not hasattr(self, 'video_grid_frame'):
            return
            
        # Clear existing video labels (except host)
        for client_id, video_label in self.video_labels.items():
            video_label.destroy()
        self.video_labels.clear()
        
        # Calculate grid layout
        total_participants = len(self.clients) + 1  # +1 for host
        if total_participants <= 1:
            # Only host, show full screen
            self.host_video_label.pack(expand=True, fill=tk.BOTH)
            return
        
        # Calculate optimal grid
        if total_participants <= 4:
            self.video_grid_columns = 2
        elif total_participants <= 9:
            self.video_grid_columns = 3
        else:
            self.video_grid_columns = 4
            
        # Create grid layout
        self.create_video_grid_layout()
        
    def create_video_grid_layout(self):
        """Create the video grid layout"""
        # Clear the grid frame
        for widget in self.video_grid_frame.winfo_children():
            widget.destroy()
            
        # Create grid rows
        total_participants = len(self.clients) + 1  # +1 for host
        rows = (total_participants + self.video_grid_columns - 1) // self.video_grid_columns
        
        # Configure grid weights
        for i in range(rows):
            self.video_grid_frame.grid_rowconfigure(i, weight=1)
        for i in range(self.video_grid_columns):
            self.video_grid_frame.grid_columnconfigure(i, weight=1)
        
        # Add host video (always first)
        self.host_video_label = tk.Label(self.video_grid_frame, 
                                        text="📹 Host Video\n\nClick 'Start Video' to begin",
                                        font=('Segoe UI', 12),
                                        fg='#888888', bg='#000000',
                                        relief='solid', bd=1)
        self.host_video_label.grid(row=0, column=0, sticky='nsew', padx=2, pady=2)
        
        # Add client videos
        row, col = 0, 1
        for client_id, client_info in self.clients.items():
            if col >= self.video_grid_columns:
                row += 1
                col = 0
                
            # Create video label for client
            video_label = tk.Label(self.video_grid_frame, 
                                  text=f"📹 {client_info['name']}\n\nVideo Off",
                                  font=('Segoe UI', 10),
                                  fg='#888888', bg='#000000',
                                  relief='solid', bd=1)
            video_label.grid(row=row, column=col, sticky='nsew', padx=2, pady=2)
            
            # Store reference
            self.video_labels[client_id] = video_label
            
            col += 1
            
    def update_client_video_display(self, client_id, frame_data=None):
        """Update a specific client's video display"""
        if client_id in self.video_labels:
            video_label = self.video_labels[client_id]
            if frame_data is not None:
                # Update with actual video frame
                try:
                    # Decode frame data
                    nparr = np.frombuffer(frame_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # Convert BGR to RGB for display
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Resize frame to fit display
                        height, width = frame_rgb.shape[:2]
                        max_width, max_height = 200, 150
                        
                        if width > max_width or height > max_height:
                            scale = min(max_width/width, max_height/height)
                            new_width = int(width * scale)
                            new_height = int(height * scale)
                            frame_rgb = cv2.resize(frame_rgb, (new_width, new_height))
                        
                        # Convert to PhotoImage and display
                        image = Image.fromarray(frame_rgb)
                        photo = ImageTk.PhotoImage(image)
                        
                        video_label.config(image=photo, text="")
                        video_label.image = photo  # Keep reference
                        # print(f"Server displayed video for client {client_id}")
                    else:
                        video_label.config(text=f"📹 {self.clients[client_id]['name']}\n\nVideo Error")
                        
                except Exception as e:
                    print(f"Error processing client video frame: {e}")
                    video_label.config(text=f"📹 {self.clients[client_id]['name']}\n\nVideo Error")
            else:
                # Show video off state
                video_label.config(text=f"📹 {self.clients[client_id]['name']}\n\nVideo Off")
                
    def toggle_host_video(self):
        """Toggle Host video on/off"""
        if not self.host_video_enabled:
            self.start_host_video()
        else:
            self.stop_host_video()
            
    def start_host_video(self):
        """Start Host video"""
        try:
            self.video_cap = cv2.VideoCapture(0)
            if not self.video_cap.isOpened():
                messagebox.showerror("Camera Error", "Cannot access camera")
                return
                
            self.host_video_enabled = True
            
            # Update button with error handling
            try:
                if hasattr(self, 'host_video_btn') and self.host_video_btn and self.host_video_btn.winfo_exists():
                    self.host_video_btn.config(text="📹 Video On", bg='#51cf66')
            except (tk.TclError, AttributeError):
                pass
            
            # Start video streaming thread
            threading.Thread(target=self.host_video_loop, daemon=True).start()
            
            # Notify clients about Host video status
            self.broadcast_host_status_update()
            self.update_clients_display()
            
        except Exception as e:
            messagebox.showerror("Video Error", f"Failed to start Host video: {str(e)}")
            
    def stop_host_video(self):
        """Stop Host video"""
        self.host_video_enabled = False
        
        # Update button with error handling
        try:
            if hasattr(self, 'host_video_btn') and self.host_video_btn and self.host_video_btn.winfo_exists():
                self.host_video_btn.config(text="📹 Start Video", bg='#404040')
        except (tk.TclError, AttributeError):
            pass
        
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
            
        # Clear video display
        self.host_video_label.config(image="", 
                                    text="📹 Host Video\n\nClick 'Start Video' to begin",
                                    font=('Segoe UI', 14),
                                    fg='#888888', bg='#000000')
        
        # Notify clients
        self.broadcast_host_status_update()
        self.update_clients_display()
        
    def host_video_loop(self):
        """Host video streaming loop - CRASH SAFE VERSION"""
        print("Starting host video loop...")
        frame_count = 0
        
        while self.host_video_enabled and hasattr(self, 'video_cap') and self.video_cap:
            try:
                ret, frame = self.video_cap.read()
                if not ret:
                    print("Failed to read frame from camera")
                    break
                
                frame_count += 1
                
                # Reduce debug output frequency
                if frame_count % 30 == 0:  # Print every 30 frames
                    print(f"Frame {frame_count} captured: {frame.shape}")
                
                # Save first frame as test (only once)
                if frame_count == 1:
                    try:
                        cv2.imwrite('test_frame.jpg', frame)
                        print("Test frame saved as test_frame.jpg")
                    except:
                        pass
                    
                # Adaptive resize and convert for display with error handling
                try:
                    # Calculate adaptive size based on original frame and settings
                    original_height, original_width = frame.shape[:2]
                    target_width = self.video_settings['default_width']
                    target_height = self.video_settings['default_height']
                    
                    # Maintain aspect ratio
                    aspect_ratio = original_width / original_height
                    if aspect_ratio > (target_width / target_height):
                        # Width is the limiting factor
                        new_width = min(target_width, self.video_settings['max_width'])
                        new_height = int(new_width / aspect_ratio)
                    else:
                        # Height is the limiting factor
                        new_height = min(target_height, self.video_settings['max_height'])
                        new_width = int(new_height * aspect_ratio)
                    
                    # Ensure minimum size
                    new_width = max(new_width, self.video_settings['min_width'])
                    new_height = max(new_height, self.video_settings['min_height'])
                    
                    display_frame = cv2.resize(frame, (new_width, new_height))
                    display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                    
                    # Put frame in queue for display (non-blocking)
                    if hasattr(self, 'video_frame_queue'):
                        try:
                            # Clear old frames if queue is full
                            while self.video_frame_queue.qsize() > 1:
                                try:
                                    self.video_frame_queue.get_nowait()
                                except queue.Empty:
                                    break
                            self.video_frame_queue.put_nowait(display_frame_rgb)
                        except queue.Full:
                            # Skip frame if queue is still full
                            pass
                except Exception as e:
                    print(f"Frame processing error: {e}")
                    continue
                
                # Broadcast to clients via UDP (with error handling)
                try:
                    self.broadcast_host_video_frame(frame)
                except Exception as e:
                    print(f"Broadcast error: {e}")
                
                # Reduced frame rate to prevent overload
                time.sleep(0.05)  # 20 FPS instead of 30
                
            except Exception as e:
                print(f"Host video streaming error: {e}")
                break
                
        print("Host video loop ended")
        
        # Clean up
        if hasattr(self, 'video_cap') and self.video_cap:
            try:
                self.video_cap.release()
            except:
                pass
                
    def start_video_display_timer(self):
        """Start the video display update timer"""
        self.update_video_display_from_queue()
        
    def update_video_display_from_queue(self):
        """Update video display from queue in main thread - STABLE VERSION"""
        try:
            # Safety check - ensure GUI still exists
            if not hasattr(self, 'root') or not self.root:
                return
                
            # Track current state to prevent unnecessary UI updates
            screen_frame_displayed = False
            video_frame_displayed = False
            
            # Check for screen sharing frames first (priority over video for display)
            if self.host_screen_share_enabled and hasattr(self, 'screen_frame_queue'):
                try:
                    # Get screen frame from queue with timeout
                    frame_rgb = self.screen_frame_queue.get_nowait()
                    
                    # Validate frame data
                    if frame_rgb is not None and frame_rgb.size > 0:
                        # Create photo safely
                        pil_image = Image.fromarray(frame_rgb)
                        photo = ImageTk.PhotoImage(pil_image)
                        
                        # Update display with safety checks
                        if hasattr(self, 'host_video_label') and self.host_video_label.winfo_exists():
                            self.host_video_label.configure(image=photo, text="")
                            self.host_video_label.image = photo  # Keep reference
                            screen_frame_displayed = True
                            
                except queue.Empty:
                    # No screen frame available, try video instead
                    pass
                except Exception as e:
                    print(f"Screen frame error: {e}")
            
            # Check for video frames (if no screen frame was displayed)
            if not screen_frame_displayed and self.host_video_enabled and hasattr(self, 'video_frame_queue'):
                try:
                    # Get frame from queue with timeout
                    frame_rgb = self.video_frame_queue.get_nowait()
                    
                    # Validate frame data
                    if frame_rgb is not None and frame_rgb.size > 0:
                        # Create photo safely
                        pil_image = Image.fromarray(frame_rgb)
                        photo = ImageTk.PhotoImage(pil_image)
                        
                        # Update display with safety checks
                        if hasattr(self, 'host_video_label') and self.host_video_label.winfo_exists():
                            self.host_video_label.configure(image=photo, text="")
                            self.host_video_label.image = photo  # Keep reference
                            video_frame_displayed = True
                            
                except queue.Empty:
                    # No video frame available, skip this update
                    pass
                except Exception as e:
                    print(f"Video frame error: {e}")
            
            # Update display mode tracking (prevent unnecessary UI updates)
            new_display_mode = 'screen_sharing' if screen_frame_displayed else ('video' if video_frame_displayed else 'none')
            
            # Only update UI state when mode actually changes
            if self.current_display_mode != new_display_mode:
                self.current_display_mode = new_display_mode
                # Any additional UI state updates can go here if needed
                    
        except Exception as e:
            print(f"Critical display error: {e}")
        
        # Schedule next update with safety checks and adaptive frequency
        try:
            if hasattr(self, 'root') and self.root:
                if self.host_screen_share_enabled:
                    # Screen sharing is stable, can use lower refresh rate
                    self.root.after(100, self.update_video_display_from_queue)  # 10 FPS for screen sharing
                elif self.host_video_enabled:
                    # Video mode needs higher refresh rate
                    self.root.after(50, self.update_video_display_from_queue)  # 20 FPS for video
                else:
                    self.root.after(200, self.update_video_display_from_queue)  # Check less frequently when idle
        except:
            # GUI might be destroyed, stop scheduling
            pass
        
    def broadcast_host_video_frame(self, frame):
        """Broadcast Host video frame to all clients with adaptive sizing"""
        try:
            # Adaptive resize based on settings
            original_height, original_width = frame.shape[:2]
            target_width = self.video_settings['default_width']
            target_height = self.video_settings['default_height']
            
            # Maintain aspect ratio for broadcast
            aspect_ratio = original_width / original_height
            if aspect_ratio > (target_width / target_height):
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:
                new_height = target_height
                new_width = int(target_height * aspect_ratio)
            
            frame_resized = cv2.resize(frame, (new_width, new_height))
            
            # Compress with adaptive quality
            quality = self.video_settings['quality']
            _, encoded = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, quality])
            
            # Create packet
            sequence = int(time.time() * 1000) % (2**32)  # Use timestamp as sequence
            packet = struct.pack('!III', self.host_id, sequence, len(encoded)) + encoded.tobytes()
            
            # Send to all clients
            for client_id, client_info in self.clients.items():
                try:
                    client_address = (client_info['address'][0], self.udp_video_port)
                    self.udp_video_socket.sendto(packet, client_address)
                except:
                    pass
                    
        except Exception as e:
            print(f"Error broadcasting Host video: {e}")
            
    def toggle_host_microphone(self):
        """Toggle Host microphone on/off"""
        if not self.host_microphone_enabled:
            self.start_host_microphone()
        else:
            self.stop_host_microphone()
            
    def toggle_host_speaker(self):
        """Toggle Host speaker on/off"""
        if not self.host_speaker_enabled:
            self.start_host_speaker()
        else:
            self.stop_host_speaker()
            
    def toggle_host_audio(self):
        """Legacy method for compatibility - toggles microphone"""
        self.toggle_host_microphone()
            
    def start_host_microphone(self):
        """Start Host microphone"""
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
            
            self.host_microphone_enabled = True
            self.host_audio_enabled = True  # For compatibility
            
            # Update button safely
            self.safe_button_update('host_mic_btn', text="🎤\nMic On", bg='#28a745')
            
            # Start audio streaming thread
            threading.Thread(target=self.host_audio_loop, daemon=True).start()
            
            # Notify clients
            self.broadcast_host_status_update()
            self.update_clients_display()
            
        except Exception as e:
            messagebox.showerror("Microphone Error", f"Failed to start Host microphone: {str(e)}")
            
    def start_host_speaker(self):
        """Start Host speaker"""
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
            
            self.host_speaker_enabled = True
            
            # Update button with error handling
            try:
                if hasattr(self, 'host_speaker_btn') and self.host_speaker_btn and self.host_speaker_btn.winfo_exists():
                    self.host_speaker_btn.config(text="🔊\nSpeaker On", bg='#28a745')
            except (tk.TclError, AttributeError):
                pass
            
        except Exception as e:
            messagebox.showerror("Speaker Error", f"Failed to start Host speaker: {str(e)}")
            
    def start_host_audio(self):
        """Legacy method for compatibility - starts both mic and speaker"""
        self.start_host_microphone()
        if not self.host_speaker_enabled:
            self.start_host_speaker()
            
    def stop_host_microphone(self):
        """Stop Host microphone with proper error handling"""
        self.host_microphone_enabled = False
        
        # Update button safely
        self.safe_button_update('host_mic_btn', text="🎤\nMic", bg='#404040')
        
        if hasattr(self, 'audio_stream') and self.audio_stream:
            try:
                if self.audio_stream.is_active():
                    self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception as e:
                print(f"Error stopping host microphone stream: {e}")
            finally:
                self.audio_stream = None
        
        # Update compatibility flag
        self.host_audio_enabled = self.host_microphone_enabled
        
        # Notify clients
        self.broadcast_host_status_update()
        self.update_clients_display()
        
    def stop_host_speaker(self):
        """Stop Host speaker with proper error handling"""
        self.host_speaker_enabled = False
        
        # Update button with error handling
        try:
            if hasattr(self, 'host_speaker_btn') and self.host_speaker_btn and self.host_speaker_btn.winfo_exists():
                self.host_speaker_btn.config(text="🔊\nSpeaker", bg='#404040')
        except (tk.TclError, AttributeError):
            pass
        
        if hasattr(self, 'audio_output_stream') and self.audio_output_stream:
            try:
                if self.audio_output_stream.is_active():
                    self.audio_output_stream.stop_stream()
                self.audio_output_stream.close()
            except Exception as e:
                print(f"Error stopping host speaker stream: {e}")
            finally:
                self.audio_output_stream = None
                
    def stop_host_audio(self):
        """Legacy method for compatibility - stops both mic and speaker"""
        self.stop_host_microphone()
        self.stop_host_speaker()
        
        # Clean up PyAudio if both are stopped
        if not self.host_microphone_enabled and not self.host_speaker_enabled:
            if hasattr(self, 'audio') and self.audio:
                try:
                    self.audio.terminate()
                except Exception as e:
                    print(f"Error terminating PyAudio: {e}")
                finally:
                    self.audio = None
            
        if self.audio:
            self.audio.terminate()
            self.audio = None
            
        # Notify clients
        self.broadcast_host_status_update()
        self.update_clients_display()
        
    def host_audio_loop(self):
        """Host audio streaming loop"""
        consecutive_errors = 0
        max_errors = 5
        
        while self.host_microphone_enabled and self.audio_stream and self.running:
            try:
                # Check if stream is still active
                if not self.audio_stream.is_active():
                    print("Host audio stream is not active, stopping loop")
                    break
                
                # Read audio data with exception handling for overflow
                try:
                    data = self.audio_stream.read(1024, exception_on_overflow=False)
                except Exception as read_error:
                    if "Input overflowed" in str(read_error):
                        print("Host audio input overflow, clearing buffer...")
                        try:
                            self.audio_stream.read(1024, exception_on_overflow=False)
                        except:
                            pass
                        time.sleep(0.1)
                        continue
                    else:
                        raise read_error
                
                # Broadcast to clients via UDP
                self.broadcast_host_audio_data(data)
                print(f"Host audio broadcasted: {len(data)} bytes")
                
                # Reset error counter on success
                consecutive_errors = 0
                time.sleep(0.02)  # Small delay to prevent overwhelming
                
            except Exception as e:
                consecutive_errors += 1
                print(f"Host audio streaming error ({consecutive_errors}/{max_errors}): {e}")
                
                # If too many consecutive errors, stop the loop
                if consecutive_errors >= max_errors:
                    print("Too many host audio errors, stopping audio stream")
                    self.root.after(0, self.stop_host_audio)
                    break
                    
                time.sleep(0.1)  # Brief pause before retrying
                
    def broadcast_host_audio_data(self, audio_data):
        """Broadcast Host audio data to all clients"""
        try:
            # Create packet
            timestamp = int(time.time() * 1000) % (2**32)
            packet = struct.pack('!II', self.host_id, timestamp) + audio_data
            
            # Send to all clients
            broadcast_count = 0
            for client_id, client_info in self.clients.items():
                try:
                    client_address = (client_info['address'][0], self.udp_audio_port)
                    self.udp_audio_socket.sendto(packet, client_address)
                    broadcast_count += 1
                    print(f"Host audio sent to client {client_id}")
                except Exception as e:
                    print(f"Error sending host audio to client {client_id}: {e}")
            
            if broadcast_count > 0:
                print(f"Host audio broadcasted to {broadcast_count} clients")
                    
        except Exception as e:
            print(f"Error broadcasting Host audio: {e}")
            
    def toggle_host_presentation(self):
        """Toggle Host presentation mode"""
        print("Toggle host presentation called")
        if self.presenter_id != self.host_id:
            # Become presenter
            if self.presenter_id is None:
                print("Starting presentation...")
                self.presenter_id = self.host_id
                self.host_present_btn.config(text="🖥️ Presenting", bg='#fd7e14')
                
                # Start screen sharing
                print("Calling start_host_screen_share...")
                self.start_host_screen_share()
                
                # Notify clients
                presenter_notification = {
                    'type': 'presenter_changed',
                    'presenter_id': self.host_id,
                    'presenter_name': self.host_name
                }
                self.broadcast_message(presenter_notification)
                
                self.log_message("Host became presenter")
                self.update_clients_display()
            else:
                messagebox.showwarning("Presenter Active", "Another participant is currently presenting")
        else:
            # Stop presenting
            print("Stopping presentation...")
            self.presenter_id = None
            self.host_present_btn.config(text="🖥️ Present", bg='#fd7e14')
            
            # Stop screen sharing
            self.stop_host_screen_share()
            
            stop_msg = {
                'type': 'presentation_stopped',
                'former_presenter': self.host_id
            }
            self.broadcast_message(stop_msg)
            
            self.log_message("Host stopped presenting")
            self.update_clients_display()
            
    def send_host_chat_message(self, event=None):
        """Send chat message from Host"""
        message = self.chat_entry.get().strip()
        if message:
            chat_msg = {
                'type': 'chat',
                'client_id': self.host_id,
                'name': self.host_name,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            self.chat_history.append(chat_msg)
            self.broadcast_message(chat_msg)
            self.update_chat_display()
            
            self.chat_entry.delete(0, tk.END)
            self.log_message(f"Host chat: {message}")
            
    def update_chat_display(self):
        """Update modern chat display with history"""
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
        
    def add_host_to_session(self):
        """Add Host as a participant in the session"""
        # Add Host to chat history
        host_join_msg = {
            'type': 'chat',
            'client_id': self.host_id,
            'name': self.host_name,
            'message': 'Host has joined the meeting',
            'timestamp': datetime.now().isoformat()
        }
        self.chat_history.append(host_join_msg)
        self.update_chat_display()
        
        self.log_message("Host joined the session as a participant")
        
    def broadcast_host_status_update(self):
        """Broadcast Host status update to all clients"""
        status_msg = {
            'type': 'host_status_update',
            'host_id': self.host_id,
            'video_enabled': self.host_video_enabled,
            'audio_enabled': self.host_audio_enabled,
            'screen_share_enabled': self.host_screen_share_enabled,
            'is_presenter': self.presenter_id == self.host_id
        }
        self.broadcast_message(status_msg)


    def send_host_chat_message(self, event=None):
        """Send chat message from Host"""
        message = self.chat_entry.get().strip()
        if message:
            chat_msg = {
                'type': 'chat',
                'client_id': self.host_id,
                'name': self.host_name,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            self.chat_history.append(chat_msg)
            self.broadcast_message(chat_msg)
            self.update_chat_display()
            
            self.chat_entry.delete(0, tk.END)
            self.log_message(f"Host chat: {message}")
            
    def update_chat_display(self):
        """Update modern chat display with history"""
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
        
    def broadcast_host_status_update(self):
        """Broadcast Host status update to all clients"""
        status_msg = {
            'type': 'host_status_update',
            'host_id': self.host_id,
            'video_enabled': self.host_video_enabled,
            'audio_enabled': self.host_audio_enabled,
            'screen_share_enabled': self.host_screen_share_enabled,
            'is_presenter': self.presenter_id == self.host_id
        }
        self.broadcast_message(status_msg)
        
    def stop_server(self):
        """Stop the communication server"""
        self.running = False
        
        # Stop Host media
        if self.host_video_enabled:
            self.stop_host_video()
        if self.host_audio_enabled:
            self.stop_host_audio()
        
        # Disconnect all clients
        for client_id in list(self.clients.keys()):
            self.disconnect_client(client_id)
            
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
            
        # Update GUI
        self.start_server_btn.config(state=tk.NORMAL)
        self.stop_server_btn.config(state=tk.DISABLED)
        self.server_status_label.config(text="● Server Stopped")
        
        # Disable host controls with error handling
        try:
            if hasattr(self, 'host_video_btn') and self.host_video_btn and self.host_video_btn.winfo_exists():
                self.host_video_btn.config(state=tk.DISABLED, text="📹 Start Video")
        except (tk.TclError, AttributeError):
            pass
            
        try:
            if hasattr(self, 'host_mic_btn') and self.host_mic_btn and self.host_mic_btn.winfo_exists():
                self.host_mic_btn.config(state=tk.DISABLED, text="🎤 Mic")
        except (tk.TclError, AttributeError):
            pass
            
        try:
            if hasattr(self, 'host_speaker_btn') and self.host_speaker_btn and self.host_speaker_btn.winfo_exists():
                self.host_speaker_btn.config(state=tk.DISABLED, text="🔊 Speaker")
        except (tk.TclError, AttributeError):
            pass
            
        try:
            if hasattr(self, 'host_present_btn') and self.host_present_btn and self.host_present_btn.winfo_exists():
                self.host_present_btn.config(state=tk.DISABLED, text="🖥️ Present")
        except (tk.TclError, AttributeError):
            pass
            
        try:
            if hasattr(self, 'host_stop_screen_btn') and self.host_stop_screen_btn and self.host_stop_screen_btn.winfo_exists():
                self.host_stop_screen_btn.config(state=tk.DISABLED)
        except (tk.TclError, AttributeError):
            pass
            
        try:
            if hasattr(self, 'chat_entry') and self.chat_entry and self.chat_entry.winfo_exists():
                self.chat_entry.config(state=tk.DISABLED)
        except (tk.TclError, AttributeError):
            pass
            
        try:
            if hasattr(self, 'chat_send_btn') and self.chat_send_btn and self.chat_send_btn.winfo_exists():
                self.chat_send_btn.config(state=tk.DISABLED)
        except (tk.TclError, AttributeError):
            pass
        
        # Clear displays
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Reset video display
        self.host_video_label.config(image="", 
                                    text="📹 Host Video\n\nClick 'Start Server' to begin",
                                    font=('Segoe UI', 14),
                                    fg='#888888', bg='#000000')
        
        # Clear participants
        if hasattr(self, 'participants_tree'):
            for item in self.participants_tree.get_children():
                self.participants_tree.delete(item)
        if hasattr(self, 'detailed_participants_tree'):
            for item in self.detailed_participants_tree.get_children():
                self.detailed_participants_tree.delete(item)
                
        self.participants_count_label.config(text="👥 Participants: 0")
        self.server_info_label.config(text="🌐 Server: Not Running")
        
        self.log_message("Server stopped")
        
    def on_closing(self):
        """Handle window closing"""
        if self.running:
            self.stop_server()
        self.root.destroy()
        
    def start_host_screen_share(self):
        """Start CN_project style advanced screen sharing"""
        try:
            if not MSS_AVAILABLE:
                messagebox.showerror("Screen Sharing Error", "Screen sharing not available. Please install mss: pip install mss")
                return
                
            if self.presentation_active:
                messagebox.showwarning("Screen Sharing", "Presentation already active")
                return
                
            print("Starting CN_project style screen sharing...")
            
            # Allocate dedicated ports for screen sharing
            self.presenter_port = self.get_ephemeral_port()
            self.viewer_port = self.get_ephemeral_port()
            
            print(f"Allocated ports - Presenter: {self.presenter_port}, Viewer: {self.viewer_port}")
            
            # Set presentation state
            self.presentation_active = True
            self.presenter_id = self.host_id
            self.presenter_username = "Host"
            self.host_screen_share_enabled = True
            
            # Update UI
            self.host_video_label.config(text="🖥️ Screen Sharing\n\nCapturing your screen...", 
                                       font=('Segoe UI', 14),
                                       fg='#888888', bg='#000000')
            
            if hasattr(self, 'host_present_btn'):
                self.host_present_btn.config(text="🖥️ Stop Presenting", bg='#28a745')
            
            # Start presenter server (receives frames from host)
            threading.Thread(target=self.start_presenter_server_sync, daemon=True).start()
            
            # Start viewer server (sends frames to clients)
            threading.Thread(target=self.start_viewer_server_sync, daemon=True).start()
            
            # Start local screen capture
            threading.Thread(target=self.cn_style_screen_capture, daemon=True).start()
            
            # Notify all clients about presentation start
            present_msg = {
                'type': 'cn_present_start',
                'presenter_id': self.host_id,
                'presenter_name': 'Host',
                'viewer_port': self.viewer_port,
                'topic': 'Screen Share'
            }
            self.broadcast_message(present_msg)
            
            self.log_message("CN_project style screen sharing started")
            print("Advanced screen sharing started successfully")
            
        except Exception as e:
            print(f"Screen sharing error: {e}")
            messagebox.showerror("Screen Share Error", f"Failed to start screen sharing: {str(e)}")
            self.presentation_active = False
            self.host_screen_share_enabled = False
            
    def stop_host_screen_share(self):
        """Stop CN_project style screen sharing"""
        print("Stopping CN_project style screen sharing...")
        
        if not self.presentation_active:
            print("No active presentation to stop")
            return
            
        # Close presenter connection
        if self.presenter_writer:
            try:
                self.presenter_writer.close()
            except:
                pass
                
        # Close all viewer connections
        for viewer_conn in list(self.frame_viewers.values()):
            try:
                viewer_conn.close()
            except:
                pass
        self.frame_viewers.clear()
        
        # Close servers
        if self.presenter_server:
            try:
                self.presenter_server.close()
            except:
                pass
        if self.viewer_server:
            try:
                self.viewer_server.close()
            except:
                pass
            
        # Reset state
        self.presentation_active = False
        self.presenter_id = None
        self.presenter_username = None
        self.presenter_port = None
        self.viewer_port = None
        self.host_screen_share_enabled = False
        
        # Update UI
        if hasattr(self, 'host_present_btn'):
            self.host_present_btn.config(text="🖥️ Present", bg='#fd7e14')
            
        if not self.host_video_enabled:
            self.host_video_label.config(image="", 
                                        text="📹 Host Video\n\nClick 'Start Video' to begin",
                                        font=('Segoe UI', 14),
                                        fg='#888888', bg='#000000')
        
        # Notify clients that presentation stopped
        stop_msg = {
            'type': 'cn_present_stop',
            'presenter_id': self.host_id,
            'presenter_name': 'Host'
        }
        self.broadcast_message(stop_msg)
        
        self.log_message("CN_project style screen sharing stopped")
        print("Advanced screen sharing stopped successfully")
    
    def get_ephemeral_port(self):
        """Allocate an ephemeral port for screen sharing"""
        port = self.next_screen_port
        self.next_screen_port += 1
        return port
    
    def start_presenter_server_sync(self):
        """Start server to receive frames from presenter (host) - Threading version"""
        try:
            import socket
            import threading
            
            # Create server socket
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('localhost', self.presenter_port))
            server_sock.listen(1)
            self.presenter_server = server_sock
            
            print(f"[SCREEN] Presenter server started on port {self.presenter_port}")
            
            # Accept presenter connection
            conn, addr = server_sock.accept()
            self.presenter_writer = conn
            print(f"[SCREEN] Presenter connected from {addr}")
            
            # Start frame relay
            threading.Thread(target=self.relay_frames_sync, args=(conn,), daemon=True).start()
            
        except Exception as e:
            print(f"Failed to start presenter server: {e}")
    
    def start_viewer_server_sync(self):
        """Start server to send frames to viewers (clients) - Threading version"""
        try:
            import socket
            import threading
            
            # Create server socket
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('localhost', self.viewer_port))
            server_sock.listen(10)  # Allow multiple viewers
            self.viewer_server = server_sock
            
            print(f"[SCREEN] Viewer server started on port {self.viewer_port}")
            
            # Accept viewer connections
            while self.presentation_active:
                try:
                    conn, addr = server_sock.accept()
                    print(f"[SCREEN] Viewer connected from {addr}")
                    
                    # Store viewer connection
                    viewer_id = id(conn)
                    self.frame_viewers[viewer_id] = conn
                    
                    # Handle viewer in separate thread
                    threading.Thread(target=self.handle_viewer_connection, args=(conn, viewer_id, addr), daemon=True).start()
                    
                except Exception as e:
                    if self.presentation_active:
                        print(f"Error accepting viewer: {e}")
                    break
            
        except Exception as e:
            print(f"Failed to start viewer server: {e}")
    
    def handle_viewer_connection(self, conn, viewer_id, addr):
        """Handle individual viewer connection"""
        try:
            # Keep connection alive until presentation ends or client disconnects
            while self.presentation_active and viewer_id in self.frame_viewers:
                try:
                    # Send a small keepalive or wait for client to disconnect
                    conn.settimeout(1.0)
                    data = conn.recv(1)
                    if not data:
                        break
                except socket.timeout:
                    continue
                except:
                    break
        except:
            pass
        finally:
            # Clean up viewer connection
            if viewer_id in self.frame_viewers:
                del self.frame_viewers[viewer_id]
            try:
                conn.close()
            except:
                pass
            print(f"[SCREEN] Viewer {addr} disconnected")
    
    def relay_frames_sync(self, presenter_conn):
        """Relay frames from presenter to all viewers (Threading version)"""
        print("[SCREEN] Starting frame relay")
        frame_count = 0
        
        try:
            while self.presentation_active:
                try:
                    # Read 4-byte frame length header
                    length_data = b''
                    while len(length_data) < 4:
                        chunk = presenter_conn.recv(4 - len(length_data))
                        if not chunk:
                            raise ConnectionError("Presenter disconnected")
                        length_data += chunk
                    
                    frame_length = struct.unpack('!I', length_data)[0]
                    
                    # Read frame data
                    frame_data = b''
                    while len(frame_data) < frame_length:
                        chunk = presenter_conn.recv(min(8192, frame_length - len(frame_data)))
                        if not chunk:
                            raise ConnectionError("Presenter disconnected")
                        frame_data += chunk
                    
                    frame_count += 1
                    
                    # Relay to all viewers
                    disconnected_viewers = []
                    for viewer_id, viewer_conn in list(self.frame_viewers.items()):
                        try:
                            viewer_conn.sendall(length_data + frame_data)
                        except Exception as e:
                            print(f"Failed to relay to viewer {viewer_id}: {e}")
                            disconnected_viewers.append(viewer_id)
                    
                    # Clean up disconnected viewers
                    for viewer_id in disconnected_viewers:
                        if viewer_id in self.frame_viewers:
                            del self.frame_viewers[viewer_id]
                    
                    # Log every 50 frames
                    if frame_count % 50 == 0:
                        print(f"[SCREEN] Relayed {frame_count} frames to {len(self.frame_viewers)} viewers")
                
                except ConnectionError as e:
                    print(f"[SCREEN] {e}")
                    break
                except Exception as e:
                    print(f"[SCREEN] Frame relay error: {e}")
                    break
        
        finally:
            print(f"[SCREEN] Frame relay stopped. Total frames: {frame_count}")
            try:
                presenter_conn.close()
            except:
                pass
    
    def cn_style_screen_capture(self):
        """CN_project style screen capture and streaming"""
        print("Starting CN_project style screen capture...")
        frame_interval = 1.0 / self.screen_settings['fps']
        frame_count = 0
        start_time = time.time()
        
        try:
            # Connect to our own presenter server
            import socket
            import struct
            from PIL import Image as PILImage
            from io import BytesIO
            
            # Wait for presenter server to be ready
            time.sleep(1)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', self.presenter_port))
            print(f"[SCREEN] Connected to presenter port {self.presenter_port}")
            
            with mss.mss() as sct:
                while self.presentation_active and self.host_screen_share_enabled:
                    loop_start = time.time()
                    
                    try:
                        # Capture primary monitor
                        monitor = sct.monitors[1]
                        screenshot = sct.grab(monitor)
                        
                        # Convert to PIL Image
                        img = PILImage.frombytes('RGB', screenshot.size, screenshot.rgb)
                        
                        # Scale down for performance (CN_project style)
                        if self.screen_settings['scale_factor'] != 1.0:
                            new_width = int(img.width * self.screen_settings['scale_factor'])
                            new_height = int(img.height * self.screen_settings['scale_factor'])
                            img = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
                        
                        # Compress to JPEG
                        buffer = BytesIO()
                        img.save(buffer, format='JPEG', quality=self.screen_settings['quality'], optimize=True)
                        frame_data = buffer.getvalue()
                        
                        # Send frame with CN_project protocol: [4 bytes length][frame data]
                        frame_length = len(frame_data)
                        header = struct.pack('!I', frame_length)
                        
                        sock.sendall(header + frame_data)
                        
                        frame_count += 1
                        
                        # Update GUI display occasionally
                        if frame_count % 10 == 0:  # Every 10 frames
                            try:
                                # Create smaller version for GUI display
                                display_img = img.resize((400, 300), PILImage.Resampling.LANCZOS)
                                display_photo = ImageTk.PhotoImage(display_img)
                                # Update in main thread
                                self.root.after_idle(lambda photo=display_photo: self.update_screen_display_gui(photo))
                            except:
                                pass
                        
                        # Log performance every 50 frames
                        if frame_count % 50 == 0:
                            elapsed = time.time() - start_time
                            actual_fps = frame_count / elapsed if elapsed > 0 else 0
                            frame_size_kb = len(frame_data) / 1024
                            print(f"[SCREEN] Frames: {frame_count}, FPS: {actual_fps:.1f}, "
                                  f"Size: {frame_size_kb:.1f} KB, Viewers: {len(self.frame_viewers)}")
                    
                    except Exception as e:
                        print(f"[SCREEN] Frame capture error: {e}")
                    
                    # Sleep to maintain target FPS
                    elapsed = time.time() - loop_start
                    sleep_time = max(0, frame_interval - elapsed)
                    time.sleep(sleep_time)
        
        except Exception as e:
            print(f"[SCREEN] Screen capture error: {e}")
        finally:
            try:
                sock.close()
            except:
                pass
            print(f"[SCREEN] Screen capture stopped. Total frames: {frame_count}")
    
    def update_screen_display_gui(self, photo):
        """Update GUI screen display"""
        try:
            if hasattr(self, 'host_video_label') and self.host_video_label:
                self.host_video_label.config(image=photo)
                self.host_video_label.image = photo  # Keep a reference
        except Exception as e:
            print(f"Error updating screen display: {e}")
        
    def ensure_buttons_visible(self):
        """Ensure all buttons remain visible and responsive"""
        try:
            # Force update all button states to ensure visibility
            if hasattr(self, 'start_server_btn') and self.start_server_btn:
                self.start_server_btn.update_idletasks()
            if hasattr(self, 'stop_server_btn') and self.stop_server_btn:
                self.stop_server_btn.update_idletasks()
            if hasattr(self, 'settings_btn') and self.settings_btn:
                self.settings_btn.update_idletasks()
            if hasattr(self, 'host_video_btn') and self.host_video_btn:
                self.host_video_btn.update_idletasks()
            if hasattr(self, 'host_mic_btn') and self.host_mic_btn:
                self.host_mic_btn.update_idletasks()
            if hasattr(self, 'host_speaker_btn') and self.host_speaker_btn:
                self.host_speaker_btn.update_idletasks()
            if hasattr(self, 'host_present_btn') and self.host_present_btn:
                self.host_present_btn.update_idletasks()
            if hasattr(self, 'host_stop_screen_btn') and self.host_stop_screen_btn:
                self.host_stop_screen_btn.update_idletasks()
        except Exception as e:
            print(f"Error ensuring button visibility: {e}")
            
    def start_gui_monitor(self):
        """Start GUI responsiveness monitor during screen sharing"""
        def monitor_gui():
            while self.host_screen_share_enabled:
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
        
    def host_screen_loop(self):
        """Host screen sharing loop"""
        print("Starting host screen loop...")
        frame_count = 0
        
        # Use a simpler approach with PIL ImageGrab instead of mss to avoid thread issues
        try:
            from PIL import ImageGrab
            print("Using PIL ImageGrab for screen capture")
        except ImportError:
            if MSS_AVAILABLE:
                print("PIL ImageGrab not available, trying mss...")
                try:
                    screen_capture = mss.mss()
                    print(f"Available monitors: {len(screen_capture.monitors)}")
                except Exception as e:
                    print(f"Error creating screen capture: {e}")
                    return
            else:
                print("Neither PIL ImageGrab nor mss available. Screen sharing disabled.")
                return
        
        while self.host_screen_share_enabled:
            try:
                # Try PIL ImageGrab first (simpler and more reliable)
                try:
                    from PIL import ImageGrab
                    screenshot = ImageGrab.grab()
                    frame_rgb = np.array(screenshot)
                    print(f"PIL ImageGrab captured: {frame_rgb.shape}")
                except:
                    # Fallback to mss if PIL fails and mss is available
                    if MSS_AVAILABLE and 'screen_capture' in locals():
                        if len(screen_capture.monitors) > 1:
                            screenshot = screen_capture.grab(screen_capture.monitors[1])
                        else:
                            screenshot = screen_capture.grab(screen_capture.monitors[0])
                        frame = np.array(screenshot)
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                    else:
                        print("No screen capture method available")
                        break
                
                frame_count += 1
                if frame_count % 10 == 1:  # Print every 10th frame to reduce spam
                    print(f"Captured screen: {frame_rgb.shape}")
                
                # Resize for better performance (maintain aspect ratio)
                height, width = frame_rgb.shape[:2]
                if width > 1280:
                    scale = 1280 / width
                    new_width = 1280
                    new_height = int(height * scale)
                    frame_rgb = cv2.resize(frame_rgb, (new_width, new_height))
                    if frame_count % 10 == 1:
                        print(f"Resized to: {frame_rgb.shape}")
                
                # Add to queue for display (only if queue is not full)
                if not self.screen_frame_queue.full():
                    self.screen_frame_queue.put(frame_rgb)
                    if frame_count % 10 == 1:
                        print(f"Screen frame added to queue: {frame_rgb.shape}")
                else:
                    # Skip this frame if queue is full to prevent lag
                    if frame_count % 10 == 1:
                        print("Screen frame queue full, skipping frame")
                
                # Broadcast to clients via TCP
                self.broadcast_host_screen_data(frame_rgb)
                
                # Ensure GUI remains responsive during screen sharing
                try:
                    if hasattr(self, 'root') and self.root:
                        self.root.update_idletasks()
                except:
                    pass
                
                time.sleep(1/5)  # Reduced to 5 FPS for better GUI responsiveness
                
            except Exception as e:
                print(f"Error in screen sharing loop: {e}")
                import traceback
                traceback.print_exc()
                break
        
        # Clean up screen capture if using mss
        try:
            if MSS_AVAILABLE and 'screen_capture' in locals():
                screen_capture.close()
        except:
            pass
        
        print("Host screen loop ended")
                
    def broadcast_host_screen_data(self, frame):
        """Broadcast Host screen data to all clients via TCP"""
        try:
            # Compress frame
            img = Image.fromarray(frame)
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=60)
            frame_data = buffer.getvalue()
            
            # Create screen frame message
            screen_msg = {
                'type': 'screen_frame',
                'client_id': self.host_id,
                'presenter_id': self.host_id,
                'frame_data': base64.b64encode(frame_data).decode('utf-8')
            }
            
            # Send to all clients via TCP
            self.broadcast_message(screen_msg)
                        
        except Exception as e:
            print(f"Error broadcasting Host screen: {e}")
        
    def run(self):
        """Run the server application"""
        self.root.mainloop()

if __name__ == "__main__":
    server = LANCommunicationServer()
    server.run()