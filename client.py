#!/usr/bin/env python3
"""
LAN Communication Client - Modern Interface
A comprehensive multi-user communication client for LAN environments

Features:
- Multi-user video conferencing (UDP)
- Multi-user audio conferencing (UDP) 
- Screen/slide sharing (TCP)
- Group text chat (TCP)
- File sharing (TCP)
- Modern UI/UX Design
- Permission Management
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

# Optional imports
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    print("Warning: mss module not available. Screen sharing will be disabled.")

class LANCommunicationClient:
    def __init__(self):
        # Network configuration
        self.server_host = ""
        self.tcp_port = 8888
        self.udp_video_port = 8889
        self.udp_audio_port = 8890
        
        # Client state
        self.connected = False
        self.client_id = None
        self.client_name = ""
        self.is_presenter = False
        
        # Sockets
        self.tcp_socket = None
        self.udp_video_socket = None
        self.udp_audio_socket = None
        
        # Media devices
        self.video_cap = None
        self.audio_stream = None
        self.audio = None
        
        # Media state
        self.video_enabled = False
        self.audio_enabled = False
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
        
        # Start video display timer
        self.start_video_display_timer()
        
    def start_video_display_timer(self):
        """Start the video display update timer"""
        self.update_video_display_from_queue()
        
    def update_video_display_from_queue(self):
        """Update video display from queue in main thread - CRASH SAFE VERSION"""
        try:
            # Safety check - ensure GUI still exists
            if not hasattr(self, 'root') or not self.root:
                return
                
            # Check for screen sharing frames first (priority over video for display)
            screen_frame_displayed = False
            if hasattr(self, 'screen_frame_queue'):
                try:
                    # Get screen frame from queue with timeout
                    frame_rgb = self.screen_frame_queue.get_nowait()
                    
                    # Validate frame data
                    if frame_rgb is not None and frame_rgb.size > 0:
                        # Create photo safely
                        pil_image = Image.fromarray(frame_rgb)
                        photo = ImageTk.PhotoImage(pil_image)
                        
                        # Update main display with safety checks
                        if hasattr(self, 'main_video_label') and self.main_video_label.winfo_exists():
                            self.main_video_label.configure(image=photo, text="")
                            self.main_video_label.image = photo  # Keep reference
                            screen_frame_displayed = True
                            
                except queue.Empty:
                    # No screen frame available, try video instead
                    pass
                except Exception as e:
                    print(f"Screen frame error: {e}")
            
            # Check for video frames (if no screen frame was displayed)
            if not screen_frame_displayed and hasattr(self, 'video_frame_queue'):
                try:
                    # Get frame from queue with timeout
                    frame_rgb = self.video_frame_queue.get_nowait()
                    
                    # Validate frame data
                    if frame_rgb is not None and frame_rgb.size > 0:
                        # Create photo safely
                        pil_image = Image.fromarray(frame_rgb)
                        photo = ImageTk.PhotoImage(pil_image)
                        
                        # Update my video display with safety checks
                        if hasattr(self, 'your_video_label') and self.your_video_label.winfo_exists():
                            self.your_video_label.configure(image=photo, text="")
                            self.your_video_label.image = photo  # Keep reference
                            
                except queue.Empty:
                    # No video frame available, skip this update
                    pass
                except Exception as e:
                    print(f"Video frame error: {e}")
                    
        except Exception as e:
            print(f"Critical display error: {e}")
        
        # Schedule next update with safety checks and reduced frequency
        try:
            if hasattr(self, 'root') and self.root:
                self.root.after(50, self.update_video_display_from_queue)  # 20 FPS
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
            self.connection_status.config(text="❌ Please enter server IP", fg='#dc3545')
            return
            
        self.connection_status.config(text="🔍 Testing connection...", fg='#fd7e14')
        self.root.update()
        
        try:
            # Test TCP connection
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(3)
            test_socket.connect((server_ip, self.tcp_port))
            test_socket.close()
            
            self.connection_status.config(text="✅ Connection successful!", fg='#28a745')
        except Exception as e:
            self.connection_status.config(text=f"❌ Connection failed: {str(e)}", fg='#dc3545')
        
    def test_connection(self):
        """Test connection to server"""
        server_ip = self.server_ip_entry.get().strip()
        if not server_ip:
            self.connection_status.config(text="❌ Please enter server IP", fg='#dc3545')
            return
            
        self.connection_status.config(text="🔍 Testing connection...", fg='#fd7e14')
        self.root.update()
        
        try:
            # Test TCP connection
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(3)
            test_socket.connect((server_ip, self.tcp_port))
            test_socket.close()
            
            self.connection_status.config(text="✅ Connection successful!", fg='#28a745')
        except Exception as e:
            self.connection_status.config(text=f"❌ Connection failed: {str(e)}", fg='#dc3545')
    
    def show_connection_screen(self):
        """Show the modern connection screen"""
        # Clear main container
        for widget in self.main_container.winfo_children():
            widget.destroy()
            
        # Connection screen with gradient-like background
        conn_frame = tk.Frame(self.main_container, bg='#1e1e1e')
        conn_frame.pack(fill=tk.BOTH, expand=True)
        
        # Center container with modern styling
        center_frame = tk.Frame(conn_frame, bg='#2d2d2d', padx=60, pady=60)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Add subtle border effect
        border_frame = tk.Frame(center_frame, bg='#404040', height=2)
        border_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Title with icon
        title_frame = tk.Frame(center_frame, bg='#2d2d2d')
        title_frame.pack(pady=(0, 40))
        
        title_label = tk.Label(title_frame, text="🚀 Join LAN Meeting", 
                              font=('Segoe UI', 28, 'bold'), 
                              fg='#0078d4', bg='#2d2d2d')
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame, text="Connect to your team's meeting", 
                                 font=('Segoe UI', 12), 
                                 fg='#888888', bg='#2d2d2d')
        subtitle_label.pack(pady=(5, 0))
        
        # Connection form with modern styling
        form_frame = tk.Frame(center_frame, bg='#2d2d2d')
        form_frame.pack(pady=20)
        
        # Server IP section
        ip_section = tk.Frame(form_frame, bg='#2d2d2d')
        ip_section.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(ip_section, text="🌐 Server IP Address", 
                font=('Segoe UI', 14, 'bold'), 
                fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=(0, 8))
        
        self.server_ip_entry = tk.Entry(ip_section, 
                                       font=('Segoe UI', 14),
                                       bg='#3d3d3d', fg='white',
                                       relief='flat', borderwidth=2,
                                       insertbackground='white',
                                       width=35)
        self.server_ip_entry.pack(pady=(0, 5), ipady=12)
        self.server_ip_entry.insert(0, "127.0.0.1")
        
        # Name section
        name_section = tk.Frame(form_frame, bg='#2d2d2d')
        name_section.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(name_section, text="👤 Your Name", 
                font=('Segoe UI', 14, 'bold'), 
                fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=(0, 8))
        
        self.client_name_entry = tk.Entry(name_section, 
                                         font=('Segoe UI', 14),
                                         bg='#3d3d3d', fg='white',
                                         relief='flat', borderwidth=2,
                                         insertbackground='white',
                                         width=35)
        self.client_name_entry.pack(pady=(0, 5), ipady=12)
        self.client_name_entry.insert(0, f"User_{int(time.time()) % 1000}")
        
        # Connection buttons
        button_frame = tk.Frame(form_frame, bg='#2d2d2d')
        button_frame.pack(pady=(30, 0))
        
        # Connect button with modern styling
        self.connect_btn = tk.Button(button_frame, text="🔗 Connect to Meeting", 
                                    command=self.connect_to_server,
                                    bg='#0078d4', fg='white', 
                                    font=('Segoe UI', 14, 'bold'),
                                    relief='flat', borderwidth=0,
                                    padx=30, pady=15,
                                    cursor='hand2')
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Test connection button
        test_btn = tk.Button(button_frame, text="🔍 Test Connection", 
                            command=self.test_connection,
                            bg='#6c757d', fg='white', 
                            font=('Segoe UI', 12),
                            relief='flat', borderwidth=0,
                            padx=20, pady=15,
                            cursor='hand2')
        test_btn.pack(side=tk.LEFT)
        
        # Status label
        self.connection_status = tk.Label(center_frame, text="", 
                                         font=('Segoe UI', 11), 
                                         fg='#888888', bg='#2d2d2d')
        self.connection_status.pack(pady=(20, 0))
        
        # Bind Enter key to connect
        self.server_ip_entry.bind('<Return>', lambda e: self.connect_to_server())
        self.client_name_entry.bind('<Return>', lambda e: self.connect_to_server())
        
        # Client name
        tk.Label(form_frame, text="Your Name", 
                font=('Segoe UI', 12), 
                fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=(0, 5))
        
        self.name_entry = tk.Entry(form_frame, 
                                  font=('Segoe UI', 12),
                                  bg='#3d3d3d', fg='white',
                                  relief='flat', borderwidth=0,
                                  insertbackground='white',
                                  width=30)
        self.name_entry.pack(pady=(0, 30), ipady=10)
        self.name_entry.insert(0, "Participant")
        
        # Connect button
        self.connect_btn = tk.Button(form_frame, text="🚀 Join Meeting", 
                                    command=self.connect_to_server,
                                    bg='#0078d4', fg='white', 
                                    font=('Segoe UI', 14, 'bold'),
                                    relief='flat', borderwidth=0,
                                    padx=40, pady=15,
                                    cursor='hand2')
        self.connect_btn.pack(pady=10)
        
        # Status
        self.conn_status_label = tk.Label(form_frame, text="Ready to connect", 
                                         font=('Segoe UI', 10), 
                                         fg='#888888', bg='#2d2d2d')
        self.conn_status_label.pack(pady=(10, 0))
        
        # Instructions
        instructions = """
🌐 Connect to a LAN Meeting Server

• Make sure the server is running
• Enter the server's IP address  
• Enter your display name
• Click 'Join Meeting' to connect

This application works on Local Area Network (LAN) only
        """
        
        tk.Label(center_frame, text=instructions, 
                font=('Segoe UI', 10), 
                fg='#888888', bg='#2d2d2d',
                justify=tk.LEFT).pack(pady=(30, 0))
        
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
        
        # Right sidebar
        sidebar = tk.Frame(video_container, bg='#2d2d2d', width=350)
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
        
        # Header
        tk.Label(your_video_frame, text="📹 Your Video", 
                font=('Segoe UI', 12, 'bold'), 
                fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=(0, 10))
        
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
                                              height=6)
        self.participants_listbox.pack(fill=tk.X)
        
    def create_meeting_chat_section(self, parent):
        """Create chat section"""
        chat_frame = tk.Frame(parent, bg='#2d2d2d')
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Chat header
        tk.Label(chat_frame, text="💬 Group Chat", 
                font=('Segoe UI', 12, 'bold'), 
                fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=(0, 10))
        
        # Chat display
        self.chat_display = tk.Text(chat_frame, 
                                   bg='#3d3d3d', fg='white',
                                   font=('Segoe UI', 9),
                                   relief='flat', borderwidth=0,
                                   wrap=tk.WORD, state=tk.DISABLED,
                                   height=10)
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
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
                                             height=6)
        self.shared_files_listbox.pack(fill=tk.BOTH, expand=True)
        
        # File sharing controls
        file_controls_frame = tk.Frame(file_frame, bg='#2d2d2d')
        file_controls_frame.pack(fill=tk.X)
        
        self.share_file_btn = tk.Button(file_controls_frame, text="📤 Share File", 
                                       command=self.share_file,
                                       bg='#0078d4', fg='white', 
                                       font=('Segoe UI', 9, 'bold'),
                                       relief='flat', borderwidth=0,
                                       padx=10, pady=6,
                                       cursor='hand2', state=tk.DISABLED)
        self.share_file_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.download_file_btn = tk.Button(file_controls_frame, text="📥 Download", 
                                          command=self.download_selected_file,
                                          bg='#107c10', fg='white', 
                                          font=('Segoe UI', 9, 'bold'),
                                          relief='flat', borderwidth=0,
                                          padx=10, pady=6,
                                          cursor='hand2', state=tk.DISABLED)
        self.download_file_btn.pack(side=tk.LEFT)
        
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
        
        # Audio button
        self.audio_btn = tk.Button(media_frame, text="🎤\nAudio", 
                                  command=self.toggle_audio,
                                  bg='#404040', fg='white', 
                                  font=('Segoe UI', 10, 'bold'),
                                  relief='flat', borderwidth=0,
                                  width=8, height=3,
                                  cursor='hand2')
        self.audio_btn.pack(side=tk.LEFT, padx=10)
        
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
        """Connect to the communication server"""
        try:
            self.server_host = self.server_ip_entry.get().strip()
            self.client_name = self.name_entry.get().strip()
            
            if not self.server_host or not self.client_name:
                messagebox.showerror("Connection Error", "Please enter server IP and your name")
                return
                
            self.conn_status_label.config(text="Connecting...", fg='#ffd43b')
            self.connect_btn.config(state=tk.DISABLED)
            
            # Create TCP socket
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.server_host, self.tcp_port))
            
            # Create UDP sockets
            self.udp_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            self.connected = True
            self.running = True
            
            # Start communication threads
            threading.Thread(target=self.tcp_receiver, daemon=True).start()
            threading.Thread(target=self.udp_video_receiver, daemon=True).start()
            threading.Thread(target=self.udp_audio_receiver, daemon=True).start()
            
            # Send join message
            join_msg = {
                'type': 'join',
                'name': self.client_name
            }
            self.send_tcp_message(join_msg)
            
            # Switch to meeting screen
            self.show_meeting_screen()
            
            # Enable file sharing controls
            self.share_file_btn.config(state=tk.NORMAL)
            self.download_file_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            self.conn_status_label.config(text="Connection failed", fg='#ff6b6b')
            self.connect_btn.config(state=tk.NORMAL)
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            
    def send_tcp_message(self, message):
        """Send TCP message to server"""
        try:
            message_data = json.dumps(message).encode('utf-8')
            message_length = struct.pack('!I', len(message_data))
            self.tcp_socket.send(message_length + message_data)
        except Exception as e:
            print(f"Error sending TCP message: {e}")
            
    def tcp_receiver(self):
        """Receive TCP messages from server"""
        while self.running and self.connected:
            try:
                # Receive message length
                length_data = self.tcp_socket.recv(4)
                if not length_data:
                    break
                    
                message_length = struct.unpack('!I', length_data)[0]
                
                # Receive message data
                message_data = b''
                while len(message_data) < message_length:
                    chunk = self.tcp_socket.recv(message_length - len(message_data))
                    if not chunk:
                        break
                    message_data += chunk
                    
                if len(message_data) != message_length:
                    break
                    
                # Parse message
                message = json.loads(message_data.decode('utf-8'))
                self.process_server_message(message)
                
            except Exception as e:
                if self.running:
                    print(f"TCP receiver error: {e}")
                break
                
    def process_server_message(self, message):
        """Process message from server"""
        msg_type = message.get('type')
        
        if msg_type == 'welcome':
            self.client_id = message.get('client_id')
            self.clients_list = message.get('clients', {})
            self.chat_history = message.get('chat_history', [])
            self.presenter_id = message.get('presenter_id')
            self.host_id = message.get('host_id', 0)
            
            # Update GUI
            self.root.after(0, self.update_participants_list)
            self.root.after(0, self.update_chat_display)
            
        elif msg_type == 'user_joined':
            client_id = message.get('client_id')
            name = message.get('name')
            self.clients_list[str(client_id)] = {'name': name, 'status': 'Active'}
            self.root.after(0, self.update_participants_list)
            self.root.after(0, lambda: self.add_chat_message("System", f"{name} joined the session"))
            
        elif msg_type == 'user_left':
            client_id = str(message.get('client_id'))
            name = message.get('name')
            if client_id in self.clients_list:
                del self.clients_list[client_id]
            self.root.after(0, self.update_participants_list)
            self.root.after(0, lambda: self.add_chat_message("System", f"{name} left the session"))
            
        elif msg_type == 'chat':
            sender_name = message.get('name')
            chat_message = message.get('message')
            self.root.after(0, lambda: self.add_chat_message(sender_name, chat_message))
            
        elif msg_type == 'presenter_granted':
            self.is_presenter = True
            self.root.after(0, lambda: self.present_btn.config(text="🖥️\nPresenting", bg='#fd7e14'))
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
                
    def udp_video_receiver(self):
        """Receive UDP video streams"""
        # This would handle incoming video streams from other clients
        pass
        
    def udp_audio_receiver(self):
        """Receive UDP audio streams"""
        # This would handle incoming audio streams from other clients
        pass
        

        
    def toggle_audio(self):
        """Toggle audio on/off"""
        if not self.audio_enabled:
            self.start_audio()
        else:
            self.stop_audio()
            
    def start_audio(self):
        """Start audio capture and streaming"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Audio configuration
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = 44100
            
            self.audio_stream = self.audio.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk
            )
            
            self.audio_enabled = True
            self.audio_btn.config(text="🎤\nMic On", bg='#51cf66')
            
            # Start audio streaming thread
            threading.Thread(target=self.audio_stream_loop, daemon=True).start()
            
            # Notify server
            status_msg = {'type': 'audio_status', 'enabled': True}
            self.send_tcp_message(status_msg)
            
        except Exception as e:
            messagebox.showerror("Audio Error", f"Failed to start audio: {str(e)}")
            
    def stop_audio(self):
        """Stop audio capture and streaming"""
        self.audio_enabled = False
        self.audio_btn.config(text="🎤\nAudio", bg='#404040')
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
            
        if self.audio:
            self.audio.terminate()
            self.audio = None
            
        # Notify server
        status_msg = {'type': 'audio_status', 'enabled': False}
        self.send_tcp_message(status_msg)
        
    def audio_stream_loop(self):
        """Audio streaming loop"""
        while self.audio_enabled and self.audio_stream:
            try:
                # Read audio data
                data = self.audio_stream.read(1024)
                
                # Send via UDP (simplified)
                # In a real implementation, you'd encode and send the audio data
                
            except Exception as e:
                print(f"Audio streaming error: {e}")
                break
                
    def toggle_presentation(self):
        """Toggle presentation mode"""
        if not self.is_presenter:
            # Request presenter role
            request_msg = {'type': 'request_presenter'}
            self.send_tcp_message(request_msg)
        else:
            # Stop presenting
            stop_msg = {'type': 'stop_presenting'}
            self.send_tcp_message(stop_msg)
            
    def send_chat_message(self, event=None):
        """Send chat message"""
        message = self.chat_entry.get().strip()
        if message and self.connected:
            chat_msg = {
                'type': 'chat',
                'message': message
            }
            self.send_tcp_message(chat_msg)
            self.chat_entry.delete(0, tk.END)
            
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
        """Update participants list"""
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
                    initialname=file_name,
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
            
    def disconnect(self):
        """Disconnect from server"""
        self.running = False
        self.connected = False
        
        # Stop media
        if self.video_enabled:
            self.stop_video()
        if self.audio_enabled:
            self.stop_audio()
            
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
            
        # Show connection screen
        self.show_connection_screen()
        
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
            
        # Main meeting container
        meeting_frame = tk.Frame(self.main_container, bg='#1e1e1e')
        meeting_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with meeting info and controls
        self.create_meeting_header(meeting_frame)
        
        # Main content area
        content_frame = tk.Frame(meeting_frame, bg='#1e1e1e')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Left side - Video area
        video_container = tk.Frame(content_frame, bg='#1e1e1e')
        video_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Main video display area
        self.create_video_area(video_container)
        
        # My video controls
        self.create_media_controls(video_container)
        
        # Right sidebar - Chat and participants
        sidebar = tk.Frame(content_frame, bg='#252525', width=350)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Participants section
        self.create_participants_section(sidebar)
        
        # Chat section
        self.create_chat_section(sidebar)
        
        # File sharing section
        self.create_file_section(sidebar)
        
    def create_meeting_header(self, parent):
        """Create the meeting header with controls"""
        header = tk.Frame(parent, bg='#2d2d2d', height=80)
        header.pack(fill=tk.X, padx=10, pady=10)
        header.pack_propagate(False)
        
        # Left side - Meeting info
        left_header = tk.Frame(header, bg='#2d2d2d')
        left_header.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=15)
        
        meeting_title = tk.Label(left_header, text="📹 LAN Meeting", 
                                font=('Segoe UI', 18, 'bold'), 
                                fg='white', bg='#2d2d2d')
        meeting_title.pack(anchor=tk.W)
        
        self.connection_info = tk.Label(left_header, text=f"Connected as: {self.client_name}", 
                                       font=('Segoe UI', 11), 
                                       fg='#888888', bg='#2d2d2d')
        self.connection_info.pack(anchor=tk.W, pady=(2, 0))
        
        # Right side - Meeting controls
        right_header = tk.Frame(header, bg='#2d2d2d')
        right_header.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=15)
        
        # Screen share button
        self.screen_share_btn = tk.Button(right_header, text="🖥️ Share Screen", 
                                         command=self.toggle_screen_share,
                                         bg='#fd7e14', fg='white', 
                                         font=('Segoe UI', 11, 'bold'),
                                         relief='flat', borderwidth=0,
                                         padx=20, pady=8,
                                         cursor='hand2')
        self.screen_share_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Request presenter button
        self.presenter_btn = tk.Button(right_header, text="🎯 Request Presenter", 
                                      command=self.request_presenter,
                                      bg='#28a745', fg='white', 
                                      font=('Segoe UI', 11, 'bold'),
                                      relief='flat', borderwidth=0,
                                      padx=20, pady=8,
                                      cursor='hand2')
        self.presenter_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Leave meeting button
        leave_btn = tk.Button(right_header, text="🚪 Leave Meeting", 
                             command=self.disconnect_from_server,
                             bg='#dc3545', fg='white', 
                             font=('Segoe UI', 11, 'bold'),
                             relief='flat', borderwidth=0,
                             padx=20, pady=8,
                             cursor='hand2')
        leave_btn.pack(side=tk.LEFT)
        
    def create_video_area(self, parent):
        """Create the main video display area"""
        video_frame = tk.LabelFrame(parent, text="📹 Meeting Video", 
                                   bg='#2d2d2d', fg='white',
                                   font=('Segoe UI', 14, 'bold'))
        video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Main video container
        main_video_container = tk.Frame(video_frame, bg='#000000')
        main_video_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Host/Presenter video (large display)
        self.main_video_label = tk.Label(main_video_container, 
                                        text="📹 Waiting for video...\n\nHost or presenter video will appear here",
                                        font=('Segoe UI', 16),
                                        fg='#888888', bg='#000000')
        self.main_video_label.pack(fill=tk.BOTH, expand=True)
        
        # Participant videos (smaller grid)
        participants_video_frame = tk.Frame(video_frame, bg='#2d2d2d')
        participants_video_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Scrollable frame for participant videos
        canvas = tk.Canvas(participants_video_frame, bg='#2d2d2d', height=120, highlightthickness=0)
        scrollbar = tk.Scrollbar(participants_video_frame, orient="horizontal", command=canvas.xview)
        self.participants_video_container = tk.Frame(canvas, bg='#2d2d2d')
        
        self.participants_video_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.participants_video_container, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)
        
        canvas.pack(side="top", fill="x", expand=True)
        scrollbar.pack(side="bottom", fill="x")
        
        # My video preview (small)
        self.my_video_label = tk.Label(self.participants_video_container, 
                                      text="📹 My Video\n(Off)",
                                      font=('Segoe UI', 10),
                                      fg='#888888', bg='#1a1a1a',
                                      width=15, height=8)
        self.my_video_label.pack(side=tk.LEFT, padx=5)
        
    def create_media_controls(self, parent):
        """Create media control buttons"""
        controls_frame = tk.LabelFrame(parent, text="🎛️ Media Controls", 
                                      bg='#2d2d2d', fg='white',
                                      font=('Segoe UI', 12, 'bold'))
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        controls_inner = tk.Frame(controls_frame, bg='#2d2d2d')
        controls_inner.pack(fill=tk.X, padx=15, pady=15)
        
        # Video button
        self.video_btn = tk.Button(controls_inner, text="📹 Start Video", 
                                  command=self.toggle_video,
                                  bg='#404040', fg='white', 
                                  font=('Segoe UI', 12, 'bold'),
                                  relief='flat', borderwidth=0,
                                  padx=25, pady=10,
                                  cursor='hand2')
        self.video_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Audio button
        self.audio_btn = tk.Button(controls_inner, text="🎤 Start Audio", 
                                  command=self.toggle_audio,
                                  bg='#404040', fg='white', 
                                  font=('Segoe UI', 12, 'bold'),
                                  relief='flat', borderwidth=0,
                                  padx=25, pady=10,
                                  cursor='hand2')
        self.audio_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Request permissions button
        self.request_permissions_btn = tk.Button(controls_inner, text="✋ Request to Speak", 
                                               command=self.request_permissions,
                                               bg='#17a2b8', fg='white', 
                                               font=('Segoe UI', 12, 'bold'),
                                               relief='flat', borderwidth=0,
                                               padx=25, pady=10,
                                               cursor='hand2')
        self.request_permissions_btn.pack(side=tk.LEFT)
        
    def create_participants_section(self, parent):
        """Create participants list section"""
        participants_frame = tk.LabelFrame(parent, text="👥 Participants", 
                                          bg='#252525', fg='white',
                                          font=('Segoe UI', 12, 'bold'))
        participants_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Participants list
        list_frame = tk.Frame(participants_frame, bg='#252525')
        list_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.participants_listbox = tk.Listbox(list_frame, 
                                              bg='#1e1e1e', fg='white',
                                              font=('Segoe UI', 10),
                                              selectbackground='#0078d4',
                                              borderwidth=0,
                                              height=6)
        self.participants_listbox.pack(fill=tk.X)
        
    def create_chat_section(self, parent):
        """Create chat section"""
        chat_frame = tk.LabelFrame(parent, text="💬 Chat", 
                                  bg='#252525', fg='white',
                                  font=('Segoe UI', 12, 'bold'))
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, 
                                                     bg='#1e1e1e', fg='white',
                                                     font=('Segoe UI', 10),
                                                     wrap=tk.WORD,
                                                     height=12,
                                                     borderwidth=0,
                                                     state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
        
        # Chat input
        chat_input_frame = tk.Frame(chat_frame, bg='#252525')
        chat_input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.chat_entry = tk.Entry(chat_input_frame, 
                                  bg='#3d3d3d', fg='white',
                                  font=('Segoe UI', 10),
                                  relief='flat', borderwidth=0,
                                  insertbackground='white')
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        self.chat_entry.bind('<Return>', self.send_chat_message)
        
        send_btn = tk.Button(chat_input_frame, text="📤", 
                            command=self.send_chat_message,
                            bg='#0078d4', fg='white', 
                            font=('Segoe UI', 12),
                            relief='flat', borderwidth=0,
                            padx=15, pady=8,
                            cursor='hand2')
        send_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
    def create_file_section(self, parent):
        """Create file sharing section"""
        file_frame = tk.LabelFrame(parent, text="📁 File Sharing", 
                                  bg='#252525', fg='white',
                                  font=('Segoe UI', 12, 'bold'))
        file_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # File buttons
        file_buttons = tk.Frame(file_frame, bg='#252525')
        file_buttons.pack(fill=tk.X, padx=10, pady=10)
        
        upload_btn = tk.Button(file_buttons, text="📤 Upload File", 
                              command=self.upload_file,
                              bg='#28a745', fg='white', 
                              font=('Segoe UI', 10, 'bold'),
                              relief='flat', borderwidth=0,
                              padx=15, pady=8,
                              cursor='hand2')
        upload_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        refresh_btn = tk.Button(file_buttons, text="🔄 Refresh", 
                               command=self.refresh_files,
                               bg='#6c757d', fg='white', 
                               font=('Segoe UI', 10),
                               relief='flat', borderwidth=0,
                               padx=15, pady=8,
                               cursor='hand2')
        refresh_btn.pack(side=tk.LEFT)
        
        # Files list
        self.files_listbox = tk.Listbox(file_frame, 
                                       bg='#1e1e1e', fg='white',
                                       font=('Segoe UI', 9),
                                       selectbackground='#0078d4',
                                       borderwidth=0,
                                       height=4)
        self.files_listbox.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.files_listbox.bind('<Double-Button-1>', self.download_selected_file)    

    def connect_to_server(self):
        """Connect to the server"""
        server_ip = self.server_ip_entry.get().strip()
        client_name = self.client_name_entry.get().strip()
        
        if not server_ip:
            messagebox.showerror("Error", "Please enter server IP address")
            return
            
        if not client_name:
            messagebox.showerror("Error", "Please enter your name")
            return
            
        self.server_host = server_ip
        self.client_name = client_name
        
        self.connection_status.config(text="🔗 Connecting...", fg='#fd7e14')
        self.connect_btn.config(state=tk.DISABLED)
        self.root.update()
        
        try:
            # Create TCP socket for control messages
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.server_host, self.tcp_port))
            
            # Create UDP sockets for media
            self.udp_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Start networking threads
            self.running = True
            threading.Thread(target=self.tcp_listener, daemon=True).start()
            threading.Thread(target=self.udp_video_listener, daemon=True).start()
            threading.Thread(target=self.udp_audio_listener, daemon=True).start()
            
            # Send join message
            join_msg = {
                'type': 'join',
                'name': self.client_name
            }
            self.send_tcp_message(join_msg)
            
            self.connected = True
            self.connection_status.config(text="✅ Connected successfully!", fg='#28a745')
            
            # Switch to meeting interface after a short delay
            self.root.after(1000, self.show_meeting_interface)
            
        except Exception as e:
            self.connection_status.config(text=f"❌ Connection failed: {str(e)}", fg='#dc3545')
            self.connect_btn.config(state=tk.NORMAL)
            messagebox.showerror("Connection Error", f"Failed to connect to server:\n{str(e)}")
    
    def disconnect_from_server(self):
        """Disconnect from server"""
        if messagebox.askyesno("Leave Meeting", "Are you sure you want to leave the meeting?"):
            self.running = False
            self.connected = False
            
            # Stop media
            self.stop_video()
            self.stop_audio()
            self.stop_screen_sharing()
            
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
            
            # Return to connection screen
            self.show_connection_screen()
    
    def send_tcp_message(self, message):
        """Send TCP message to server"""
        try:
            if self.tcp_socket and self.connected:
                message_data = json.dumps(message).encode('utf-8')
                message_length = len(message_data)
                self.tcp_socket.send(struct.pack('!I', message_length))
                self.tcp_socket.send(message_data)
        except Exception as e:
            print(f"Error sending TCP message: {e}")
    
    def tcp_listener(self):
        """Listen for TCP messages from server"""
        while self.running and self.connected:
            try:
                # Receive message length
                length_data = self.tcp_socket.recv(4)
                if not length_data:
                    break
                    
                message_length = struct.unpack('!I', length_data)[0]
                
                # Receive message data
                message_data = b''
                while len(message_data) < message_length:
                    chunk = self.tcp_socket.recv(message_length - len(message_data))
                    if not chunk:
                        break
                    message_data += chunk
                
                if len(message_data) == message_length:
                    message = json.loads(message_data.decode('utf-8'))
                    self.process_server_message(message)
                    
            except Exception as e:
                if self.running:
                    print(f"TCP listener error: {e}")
                break
        
        self.connected = False
    
    def udp_video_listener(self):
        """Listen for UDP video frames"""
        while self.running:
            try:
                data, addr = self.udp_video_socket.recvfrom(65536)
                
                if len(data) > 12:  # Header size
                    # Unpack header
                    sender_id, sequence, frame_size = struct.unpack('!III', data[:12])
                    frame_data = data[12:]
                    
                    if len(frame_data) == frame_size:
                        # Decode frame
                        frame_array = np.frombuffer(frame_data, dtype=np.uint8)
                        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            # Convert to RGB for display
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            
                            # Put in appropriate queue based on sender
                            if sender_id == self.host_id:  # Host video
                                try:
                                    # Clear old frames
                                    while self.screen_frame_queue.qsize() > 1:
                                        try:
                                            self.screen_frame_queue.get_nowait()
                                        except queue.Empty:
                                            break
                                    self.screen_frame_queue.put_nowait(frame_rgb)
                                except queue.Full:
                                    pass
                            else:  # Other participant video
                                self.update_participant_video(sender_id, frame_rgb)
                                
            except Exception as e:
                if self.running:
                    print(f"UDP video listener error: {e}")
    
    def udp_audio_listener(self):
        """Listen for UDP audio data"""
        while self.running:
            try:
                data, addr = self.udp_audio_socket.recvfrom(4096)
                
                if len(data) > 12:  # Header size
                    # Unpack header
                    sender_id, sequence, audio_size = struct.unpack('!III', data[:12])
                    audio_data = data[12:]
                    
                    if len(audio_data) == audio_size and hasattr(self, 'audio_stream'):
                        # Play audio (if audio output is enabled)
                        try:
                            if hasattr(self, 'audio_output_stream'):
                                self.audio_output_stream.write(audio_data)
                        except:
                            pass
                            
            except Exception as e:
                if self.running:
                    print(f"UDP audio listener error: {e}")
    
    def update_participant_video(self, client_id, frame_rgb):
        """Update video display for a participant"""
        try:
            # Create or update video display for this participant
            if client_id not in self.video_displays:
                # Create new video label for this participant
                video_label = tk.Label(self.participants_video_container, 
                                      text=f"👤 User {client_id}",
                                      font=('Segoe UI', 9),
                                      fg='#888888', bg='#1a1a1a',
                                      width=15, height=8)
                video_label.pack(side=tk.LEFT, padx=5)
                self.video_displays[client_id] = video_label
            
            # Update the video display
            video_label = self.video_displays[client_id]
            if video_label.winfo_exists():
                # Resize frame for participant video
                frame_resized = cv2.resize(frame_rgb, (120, 90))
                pil_image = Image.fromarray(frame_resized)
                photo = ImageTk.PhotoImage(pil_image)
                
                video_label.configure(image=photo, text="")
                video_label.image = photo  # Keep reference
                
        except Exception as e:
            print(f"Error updating participant video: {e}")    

    def process_server_message(self, message):
        """Process incoming message from server"""
        msg_type = message.get('type')
        
        if msg_type == 'welcome':
            self.client_id = message.get('client_id')
            self.clients_list = message.get('clients', {})
            self.chat_history = message.get('chat_history', [])
            self.presenter_id = message.get('presenter_id')
            self.host_id = message.get('host_id', 0)
            
            # Update UI
            self.update_participants_display()
            self.update_chat_display()
            
        elif msg_type == 'user_joined':
            client_id = message.get('client_id')
            name = message.get('name')
            self.clients_list[str(client_id)] = {'name': name, 'status': 'Active'}
            self.update_participants_display()
            self.add_chat_message("System", f"{name} joined the meeting", system=True)
            
        elif msg_type == 'user_left':
            client_id = str(message.get('client_id'))
            name = message.get('name', f'User {client_id}')
            if client_id in self.clients_list:
                del self.clients_list[client_id]
            self.update_participants_display()
            self.add_chat_message("System", f"{name} left the meeting", system=True)
            
            # Remove video display if exists
            if int(client_id) in self.video_displays:
                self.video_displays[int(client_id)].destroy()
                del self.video_displays[int(client_id)]
            
        elif msg_type == 'chat':
            sender_name = message.get('name', 'Unknown')
            chat_message = message.get('message', '')
            self.add_chat_message(sender_name, chat_message)
            
        elif msg_type == 'presenter_changed':
            self.presenter_id = message.get('presenter_id')
            presenter_name = message.get('presenter_name', 'Unknown')
            self.add_chat_message("System", f"{presenter_name} is now presenting", system=True)
            self.update_presenter_status()
            
        elif msg_type == 'presentation_stopped':
            former_presenter = message.get('former_presenter')
            self.presenter_id = None
            self.add_chat_message("System", "Presentation stopped", system=True)
            self.update_presenter_status()
            
        elif msg_type == 'host_request':
            request_type = message.get('request_type')
            request_message = message.get('message', '')
            self.handle_host_request(request_type, request_message)
            
        elif msg_type == 'permission_granted':
            permissions = message.get('permissions', {})
            request_message = message.get('message', 'Host granted your permissions')
            self.handle_permission_granted(permissions, request_message)
            
        elif msg_type == 'permission_denied':
            request_message = message.get('message', 'Host denied your permissions')
            self.handle_permission_denied(request_message)
            
        elif msg_type == 'force_mute':
            self.force_stop_audio()
            
        elif msg_type == 'force_disable_video':
            self.force_stop_video()
            
        elif msg_type == 'force_stop_screen_sharing':
            self.force_stop_screen_sharing()
            
        elif msg_type == 'file_list':
            self.shared_files = message.get('files', {})
            self.update_files_display()
            
        elif msg_type == 'file_uploaded':
            filename = message.get('filename')
            self.add_chat_message("System", f"File uploaded: {filename}", system=True)
            self.refresh_files()
    
    def handle_host_request(self, request_type, message):
        """Handle request from host"""
        response = messagebox.askyesno("Host Request", 
                                     f"{message}\n\nDo you want to comply?")
        
        if response:
            if request_type == 'audio':
                self.start_audio()
            elif request_type == 'video':
                self.start_video()
        
        # Send response to host
        response_msg = {
            'type': 'host_request_response',
            'request_type': request_type,
            'accepted': response
        }
        self.send_tcp_message(response_msg)
    
    def handle_permission_granted(self, permissions, message):
        """Handle permission granted by host"""
        messagebox.showinfo("Permission Granted", message)
        
        # Enable granted permissions
        if permissions.get('audio'):
            self.audio_btn.config(state=tk.NORMAL)
        if permissions.get('video'):
            self.video_btn.config(state=tk.NORMAL)
        if permissions.get('screen'):
            self.screen_share_btn.config(state=tk.NORMAL)
    
    def handle_permission_denied(self, message):
        """Handle permission denied by host"""
        messagebox.showwarning("Permission Denied", message)
    
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
            self.video_btn.config(text="📹 Video On", bg='#28a745')
            self.your_video_label.config(text="📹 My Video\n(On)")
            
            # Start video streaming thread
            threading.Thread(target=self.video_loop, daemon=True).start()
            
            # Notify server
            self.send_media_status_update()
            
        except Exception as e:
            messagebox.showerror("Video Error", f"Failed to start video: {str(e)}")
    
    def stop_video(self):
        """Stop video capture"""
        self.video_enabled = False
        self.video_btn.config(text="📹 Start Video", bg='#404040')
        self.your_video_label.config(text="📹 My Video\n(Off)", image="")
        
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
        
        # Notify server
        self.send_media_status_update()
    
    def force_stop_video(self):
        """Force stop video (by host command)"""
        self.stop_video()
        messagebox.showwarning("Video Disabled", "Host has disabled your video")
    
    def video_loop(self):
        """Video capture and streaming loop"""
        while self.video_enabled and self.video_cap:
            try:
                ret, frame = self.video_cap.read()
                if not ret:
                    break
                
                # Resize and convert for display
                display_frame = cv2.resize(frame, (320, 240))
                display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                
                # Put frame in queue for local display
                try:
                    # Clear old frames
                    while self.video_frame_queue.qsize() > 1:
                        try:
                            self.video_frame_queue.get_nowait()
                        except queue.Empty:
                            break
                    self.video_frame_queue.put_nowait(display_frame_rgb)
                except queue.Full:
                    pass
                
                # Send to server
                self.send_video_frame(frame)
                
                time.sleep(0.05)  # 20 FPS
                
            except Exception as e:
                print(f"Video loop error: {e}")
                break
    
    def send_video_frame(self, frame):
        """Send video frame to server"""
        try:
            if self.udp_video_socket and self.connected:
                # Compress frame
                frame_resized = cv2.resize(frame, (320, 240))
                _, encoded = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 70])
                
                # Create packet
                sequence = int(time.time() * 1000) % (2**32)
                packet = struct.pack('!III', self.client_id or 0, sequence, len(encoded)) + encoded.tobytes()
                
                # Send to server
                self.udp_video_socket.sendto(packet, (self.server_host, self.udp_video_port))
                
        except Exception as e:
            print(f"Error sending video frame: {e}")
    
    def toggle_audio(self):
        """Toggle audio on/off"""
        if not self.audio_enabled:
            self.start_audio()
        else:
            self.stop_audio()
    
    def start_audio(self):
        """Start audio capture"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Audio configuration
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = 44100
            
            self.audio_stream = self.audio.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk
            )
            
            # Audio output for receiving
            self.audio_output_stream = self.audio.open(
                format=format,
                channels=channels,
                rate=rate,
                output=True,
                frames_per_buffer=chunk
            )
            
            self.audio_enabled = True
            self.audio_btn.config(text="🎤 Mic On", bg='#28a745')
            
            # Start audio streaming thread
            threading.Thread(target=self.audio_loop, daemon=True).start()
            
            # Notify server
            self.send_media_status_update()
            
        except Exception as e:
            messagebox.showerror("Audio Error", f"Failed to start audio: {str(e)}")
    
    def stop_audio(self):
        """Stop audio capture"""
        self.audio_enabled = False
        self.audio_btn.config(text="🎤 Start Audio", bg='#404040')
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
            
        if self.audio_output_stream:
            self.audio_output_stream.stop_stream()
            self.audio_output_stream.close()
            self.audio_output_stream = None
            
        if self.audio:
            self.audio.terminate()
            self.audio = None
        
        # Notify server
        self.send_media_status_update()
    
    def force_stop_audio(self):
        """Force stop audio (by host command)"""
        self.stop_audio()
        messagebox.showwarning("Audio Disabled", "Host has muted your microphone")
    
    def audio_loop(self):
        """Audio capture and streaming loop"""
        while self.audio_enabled and self.audio_stream:
            try:
                # Read audio data
                audio_data = self.audio_stream.read(1024, exception_on_overflow=False)
                
                # Send to server
                self.send_audio_data(audio_data)
                
            except Exception as e:
                print(f"Audio loop error: {e}")
                break
    
    def send_audio_data(self, audio_data):
        """Send audio data to server"""
        try:
            if self.udp_audio_socket and self.connected:
                # Create packet
                sequence = int(time.time() * 1000) % (2**32)
                packet = struct.pack('!III', self.client_id or 0, sequence, len(audio_data)) + audio_data
                
                # Send to server
                self.udp_audio_socket.sendto(packet, (self.server_host, self.udp_audio_port))
                
        except Exception as e:
            print(f"Error sending audio data: {e}")
    
    def send_media_status_update(self):
        """Send media status update to server"""
        status_msg = {
            'type': 'media_status_update',
            'video_enabled': self.video_enabled,
            'audio_enabled': self.audio_enabled,
            'screen_share_enabled': self.screen_sharing
        }
        self.send_tcp_message(status_msg)
    
    def toggle_screen_share(self):
        """Toggle screen sharing"""
        if not self.screen_sharing:
            self.start_screen_sharing()
        else:
            self.stop_screen_sharing()
    
    def start_screen_sharing(self):
        """Start screen sharing"""
        try:
            self.screen_sharing = True
            self.screen_share_btn.config(text="🖥️ Stop Sharing", bg='#dc3545')
            
            # Start screen sharing thread
            threading.Thread(target=self.screen_share_loop, daemon=True).start()
            
            # Notify server
            self.send_media_status_update()
            
        except Exception as e:
            messagebox.showerror("Screen Share Error", f"Failed to start screen sharing: {str(e)}")
    
    def stop_screen_sharing(self):
        """Stop screen sharing"""
        self.screen_sharing = False
        self.screen_share_btn.config(text="🖥️ Share Screen", bg='#fd7e14')
        
        # Notify server
        self.send_media_status_update()
    
    def force_stop_screen_sharing(self):
        """Force stop screen sharing (by host command)"""
        self.stop_screen_sharing()
        messagebox.showwarning("Screen Sharing Stopped", "Host has stopped your screen sharing")
    
    def screen_share_loop(self):
        """Screen sharing capture loop"""
        while self.screen_sharing:
            try:
                # Capture screen using PIL ImageGrab (more reliable)
                try:
                    from PIL import ImageGrab
                    screenshot = ImageGrab.grab()
                    frame_rgb = np.array(screenshot)
                except ImportError:
                    if MSS_AVAILABLE:
                        # Fallback to mss
                        with mss.mss() as sct:
                            screenshot = sct.grab(sct.monitors[1])
                            frame = np.array(screenshot)
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                    else:
                        print("No screen capture method available")
                        break
                
                # Resize for better performance
                height, width = frame_rgb.shape[:2]
                if width > 1280:
                    scale = 1280 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame_rgb = cv2.resize(frame_rgb, (new_width, new_height))
                
                # Convert to BGR for encoding
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                
                # Send to server
                self.send_screen_frame(frame_bgr)
                
                time.sleep(0.1)  # 10 FPS for screen sharing
                
            except Exception as e:
                print(f"Screen share loop error: {e}")
                break
    
    def send_screen_frame(self, frame):
        """Send screen frame to server"""
        try:
            if self.tcp_socket and self.connected:
                # Compress frame
                _, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                
                # Send as TCP message (for screen sharing)
                screen_msg = {
                    'type': 'screen_frame',
                    'frame_data': base64.b64encode(encoded).decode('utf-8')
                }
                self.send_tcp_message(screen_msg)
                
        except Exception as e:
            print(f"Error sending screen frame: {e}")
    
    def request_presenter(self):
        """Request to become presenter"""
        if self.presenter_id is None:
            request_msg = {
                'type': 'request_presenter'
            }
            self.send_tcp_message(request_msg)
            self.add_chat_message("System", "Requested presenter role...", system=True)
        else:
            messagebox.showinfo("Presenter Active", "Someone is already presenting")
    
    def request_permissions(self):
        """Request permissions from host"""
        # Show permission request dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Request Permissions")
        dialog.geometry("400x300")
        dialog.configure(bg='#2d2d2d')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Title
        title_label = tk.Label(dialog, text="Request Permissions from Host", 
                              font=('Segoe UI', 16, 'bold'), 
                              fg='white', bg='#2d2d2d')
        title_label.pack(pady=20)
        
        # Permission checkboxes
        permissions_frame = tk.Frame(dialog, bg='#2d2d2d')
        permissions_frame.pack(pady=20)
        
        audio_var = tk.BooleanVar()
        video_var = tk.BooleanVar()
        screen_var = tk.BooleanVar()
        
        tk.Checkbutton(permissions_frame, text="🎤 Microphone Access", 
                      variable=audio_var, bg='#2d2d2d', fg='white',
                      selectcolor='#3d3d3d', font=('Segoe UI', 12)).pack(anchor=tk.W, pady=5)
        
        tk.Checkbutton(permissions_frame, text="📹 Camera Access", 
                      variable=video_var, bg='#2d2d2d', fg='white',
                      selectcolor='#3d3d3d', font=('Segoe UI', 12)).pack(anchor=tk.W, pady=5)
        
        tk.Checkbutton(permissions_frame, text="🖥️ Screen Share Access", 
                      variable=screen_var, bg='#2d2d2d', fg='white',
                      selectcolor='#3d3d3d', font=('Segoe UI', 12)).pack(anchor=tk.W, pady=5)
        
        # Buttons
        button_frame = tk.Frame(dialog, bg='#2d2d2d')
        button_frame.pack(pady=20)
        
        def send_request():
            permissions = {
                'audio': audio_var.get(),
                'video': video_var.get(),
                'screen': screen_var.get()
            }
            
            if any(permissions.values()):
                for perm_type, requested in permissions.items():
                    if requested:
                        request_msg = {
                            'type': 'permission_request',
                            'request_type': perm_type
                        }
                        self.send_tcp_message(request_msg)
                
                self.add_chat_message("System", "Permission request sent to host", system=True)
                dialog.destroy()
            else:
                messagebox.showwarning("No Permissions", "Please select at least one permission to request")
        
        tk.Button(button_frame, text="Send Request", command=send_request,
                 bg='#0078d4', fg='white', font=('Segoe UI', 12, 'bold'),
                 relief='flat', padx=20, pady=10).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg='#6c757d', fg='white', font=('Segoe UI', 12),
                 relief='flat', padx=20, pady=10).pack(side=tk.LEFT)
    
    def send_chat_message(self, event=None):
        """Send chat message"""
        message = self.chat_entry.get().strip()
        if message:
            chat_msg = {
                'type': 'chat',
                'message': message
            }
            self.send_tcp_message(chat_msg)
            self.chat_entry.delete(0, tk.END)
    
    def add_chat_message(self, sender, message, system=False):
        """Add message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M")
        
        if system:
            self.chat_display.insert(tk.END, f"[{timestamp}] {message}\n", "system")
        else:
            self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Configure system message style
        self.chat_display.tag_configure("system", foreground="#888888", font=('Segoe UI', 9, 'italic'))
    
    def update_chat_display(self):
        """Update chat display with history"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        
        for msg in self.chat_history:
            sender = msg.get('name', 'Unknown')
            message = msg.get('message', '')
            timestamp = msg.get('timestamp', '')
            
            if timestamp:
                time_str = datetime.fromisoformat(timestamp).strftime("%H:%M")
            else:
                time_str = "??:??"
            
            self.chat_display.insert(tk.END, f"[{time_str}] {sender}: {message}\n")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def upload_file(self):
        """Upload file to server"""
        file_path = filedialog.askopenfilename(
            title="Select file to upload",
            filetypes=[("All files", "*.*")]
        )
        
        if file_path:
            try:
                filename = os.path.basename(file_path)
                
                # Read file data
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                # Calculate file hash
                file_hash = hashlib.md5(file_data).hexdigest()
                
                # Send file to server
                file_msg = {
                    'type': 'file_upload',
                    'filename': filename,
                    'file_size': len(file_data),
                    'file_hash': file_hash,
                    'file_data': base64.b64encode(file_data).decode('utf-8')
                }
                self.send_tcp_message(file_msg)
                
                self.add_chat_message("System", f"Uploading file: {filename}", system=True)
                
            except Exception as e:
                messagebox.showerror("Upload Error", f"Failed to upload file: {str(e)}")
    
    def download_selected_file(self, event=None):
        """Download selected file"""
        selection = self.files_listbox.curselection()
        if selection:
            filename = self.files_listbox.get(selection[0])
            
            # Request file from server
            download_msg = {
                'type': 'file_download',
                'filename': filename
            }
            self.send_tcp_message(download_msg)
    
    def refresh_files(self):
        """Refresh files list"""
        refresh_msg = {
            'type': 'get_file_list'
        }
        self.send_tcp_message(refresh_msg)
    
    def update_files_display(self):
        """Update files display"""
        if hasattr(self, 'files_listbox'):
            self.files_listbox.delete(0, tk.END)
            for filename in self.shared_files.keys():
                self.files_listbox.insert(tk.END, filename)
    
    def update_participants_display(self):
        """Update participants display"""
        if hasattr(self, 'participants_listbox'):
            self.participants_listbox.delete(0, tk.END)
            
            # Add host
            host_status = "👑 Host"
            if self.presenter_id == self.host_id:
                host_status += " [Presenting]"
            self.participants_listbox.insert(tk.END, host_status)
            
            # Add other participants
            for client_id, client_info in self.clients_list.items():
                name = client_info.get('name', f'User {client_id}')
                status = f"👤 {name}"
                
                if self.presenter_id == int(client_id):
                    status += " [Presenting]"
                
                self.participants_listbox.insert(tk.END, status)
    
    def update_presenter_status(self):
        """Update presenter status in UI"""
        if self.presenter_id == self.client_id:
            self.presenter_btn.config(text="🎯 Stop Presenting", bg='#dc3545')
        else:
            self.presenter_btn.config(text="🎯 Request Presenter", bg='#28a745')
    
    def on_closing(self):
        """Handle window closing"""
        if self.connected:
            if messagebox.askyesno("Exit", "Are you sure you want to leave the meeting?"):
                self.disconnect_from_server()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Start the client application"""
        self.root.mainloop()

# Main execution
if __name__ == "__main__":
    client = LANCommunicationClient()
    client.run()