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
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import io
import base64

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
        
        # Threading
        self.running = False
        
        # GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Initialize the modern client GUI"""
        self.root = tk.Tk()
        self.root.title("LAN Meeting")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        self.root.configure(bg='#1e1e1e')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure modern style
        self.setup_modern_style()
        
        # Main container
        self.main_container = tk.Frame(self.root, bg='#1e1e1e')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Show connection screen initially
        self.show_connection_screen()
        
    def setup_modern_style(self):
        """Setup modern dark theme styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors for modern dark theme
        style.configure('Modern.TFrame', background='#2d2d2d', relief='flat')
        style.configure('Header.TFrame', background='#1e1e1e', relief='flat')
        
        # Modern buttons
        style.configure('Modern.TButton',
                       background='#0078d4',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        # Modern labels
        style.configure('Modern.TLabel',
                       background='#2d2d2d',
                       foreground='white',
                       font=('Segoe UI', 10))
        
    def show_connection_screen(self):
        """Show the connection screen"""
        # Clear main container
        for widget in self.main_container.winfo_children():
            widget.destroy()
            
        # Connection screen
        conn_frame = tk.Frame(self.main_container, bg='#1e1e1e')
        conn_frame.pack(fill=tk.BOTH, expand=True)
        
        # Center container
        center_frame = tk.Frame(conn_frame, bg='#2d2d2d', padx=50, pady=50)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        title_label = tk.Label(center_frame, text="Join LAN Meeting", 
                              font=('Segoe UI', 24, 'bold'), 
                              fg='white', bg='#2d2d2d')
        title_label.pack(pady=(0, 30))
        
        # Connection form
        form_frame = tk.Frame(center_frame, bg='#2d2d2d')
        form_frame.pack(pady=20)
        
        # Server IP
        tk.Label(form_frame, text="Server IP Address", 
                font=('Segoe UI', 12), 
                fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=(0, 5))
        
        self.server_ip_entry = tk.Entry(form_frame, 
                                       font=('Segoe UI', 12),
                                       bg='#3d3d3d', fg='white',
                                       relief='flat', borderwidth=0,
                                       insertbackground='white',
                                       width=30)
        self.server_ip_entry.pack(pady=(0, 20), ipady=10)
        self.server_ip_entry.insert(0, "127.0.0.1")
        
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
        
    def toggle_video(self):
        """Toggle video on/off"""
        if not self.video_enabled:
            self.start_video()
        else:
            self.stop_video()
            
    def start_video(self):
        """Start video capture and streaming"""
        try:
            self.video_cap = cv2.VideoCapture(0)
            if not self.video_cap.isOpened():
                messagebox.showerror("Camera Error", "Cannot access camera")
                return
                
            self.video_enabled = True
            self.video_btn.config(text="📹\nVideo On", bg='#51cf66')
            
            # Start video streaming thread
            threading.Thread(target=self.video_stream_loop, daemon=True).start()
            
            # Notify server
            status_msg = {'type': 'video_status', 'enabled': True}
            self.send_tcp_message(status_msg)
            
        except Exception as e:
            messagebox.showerror("Video Error", f"Failed to start video: {str(e)}")
            
    def stop_video(self):
        """Stop video capture and streaming"""
        self.video_enabled = False
        self.video_btn.config(text="📹\nVideo", bg='#404040')
        
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
            
        # Clear video display
        self.your_video_label.config(image="", text="📹 Camera Off",
                                    font=('Segoe UI', 10),
                                    fg='#888888', bg='#000000')
        
        # Notify server
        status_msg = {'type': 'video_status', 'enabled': False}
        self.send_tcp_message(status_msg)
        
    def video_stream_loop(self):
        """Video streaming loop"""
        while self.video_enabled and self.video_cap:
            try:
                ret, frame = self.video_cap.read()
                if not ret:
                    break
                    
                # Resize and display locally
                display_frame = cv2.resize(frame, (200, 100))
                display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(display_frame_rgb)
                photo = ImageTk.PhotoImage(pil_image)
                
                self.root.after(0, lambda p=photo: self.update_your_video(p))
                
                # Compress and send via UDP (simplified)
                # In a real implementation, you'd compress the frame and send it
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Video streaming error: {e}")
                break
                
    def update_your_video(self, photo):
        """Update your video display"""
        self.your_video_label.config(image=photo, text="")
        self.your_video_label.image = photo
        
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

if __name__ == "__main__":
    client = LANCommunicationClient()
    client.run()