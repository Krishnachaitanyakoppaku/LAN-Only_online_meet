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
        """Update video display from queue in main thread - CRASH SAFE VERSION"""
        try:
            # Safety check - ensure GUI still exists and we're connected
            if not hasattr(self, 'root') or not self.root or not self.connected:
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
                        if hasattr(self, 'main_video_label') and self.main_video_label and self.main_video_label.winfo_exists():
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
                    frame_data = self.video_frame_queue.get_nowait()
                    
                    # Handle both old format (just frame) and new format (client_id, frame)
                    if isinstance(frame_data, tuple) and len(frame_data) == 2:
                        client_id, frame_rgb = frame_data
                    else:
                        # Old format - just the frame (local video)
                        frame_rgb = frame_data
                        client_id = None
                    
                    # Validate frame data
                    if frame_rgb is not None and frame_rgb.size > 0:
                        # Create photo safely
                        pil_image = Image.fromarray(frame_rgb)
                        photo = ImageTk.PhotoImage(pil_image)
                        
                        # Update appropriate display based on source
                        if client_id is None:
                            # Local video - NO LONGER USED (handled by update_local_video_preview)
                            # This is legacy code that won't execute since video_loop no longer queues local frames
                            pass
                        else:
                            # Remote video - update main display
                            if (hasattr(self, 'main_video_label') and self.main_video_label and 
                                hasattr(self.main_video_label, 'winfo_exists') and self.main_video_label.winfo_exists()):
                                # Show who's video this is
                                if client_id == 0:  # Host video
                                    display_text = "📹 Host"
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
                    
        except Exception as e:
            print(f"Critical display error: {e}")
        
        # Schedule next update with safety checks and reduced frequency
        try:
            if hasattr(self, 'root') and self.root and self.connected:
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
        """Send TCP message to server"""
        try:
            message_data = json.dumps(message).encode('utf-8')
            message_length = struct.pack('!I', len(message_data))
            self.tcp_socket.send(message_length + message_data)
        except Exception as e:
            print(f"Error sending TCP message: {e}")
            
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
                
                # Resize and convert for local display
                display_frame = cv2.resize(frame, (200, 150))
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
                # Compress frame with very small size and low quality for UDP transmission
                frame_resized = cv2.resize(frame, (128, 96))  # Very small resolution for UDP
                _, encoded = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 20])  # Very low quality
                
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
        """Send media status update to server"""
        if self.connected:
            status_msg = {
                'type': 'media_status_update',
                'video_enabled': self.video_enabled,
                'audio_enabled': self.audio_enabled,
                'screen_sharing': getattr(self, 'screen_sharing', False)
            }
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
            
            # Start screen sharing thread
            threading.Thread(target=self.screen_sharing_loop, daemon=True).start()
            
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
                        
                time.sleep(0.1)  # 10 FPS for screen sharing
                
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
        """Disconnect from server with proper cleanup"""
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
