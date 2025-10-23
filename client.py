#!/usr/bin/env python3
"""
LAN Communication Client
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
from tkinter import ttk, messagebox, filedialog, scrolledtext
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
        
        # Threading
        self.running = False
        
        # GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Initialize the client GUI"""
        self.root = tk.Tk()
        self.root.title("LAN Communication Client")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create main notebook for different sections
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection tab
        self.setup_connection_tab()
        
        # Main communication tab
        self.setup_communication_tab()
        
        # File sharing tab
        self.setup_file_sharing_tab()
        
    def setup_connection_tab(self):
        """Setup the connection tab"""
        conn_frame = ttk.Frame(self.notebook)
        self.notebook.add(conn_frame, text="Connection")
        
        # Connection form
        form_frame = ttk.LabelFrame(conn_frame, text="Connect to Server")
        form_frame.pack(fill=tk.X, padx=20, pady=20)
        
        form_inner = ttk.Frame(form_frame)
        form_inner.pack(padx=20, pady=20)
        
        # Server IP
        ttk.Label(form_inner, text="Server IP:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.server_ip_entry = ttk.Entry(form_inner, width=20)
        self.server_ip_entry.grid(row=0, column=1, padx=5, pady=5)
        self.server_ip_entry.insert(0, "127.0.0.1")
        
        # Client name
        ttk.Label(form_inner, text="Your Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_entry = ttk.Entry(form_inner, width=20)
        self.name_entry.grid(row=1, column=1, padx=5, pady=5)
        self.name_entry.insert(0, "User")
        
        # Connect button
        self.connect_btn = ttk.Button(form_inner, text="Connect", command=self.connect_to_server)
        self.connect_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Status
        self.conn_status_label = ttk.Label(form_inner, text="Not connected")
        self.conn_status_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Instructions
        instructions = """
Instructions:
1. Make sure the server is running
2. Enter the server's IP address
3. Enter your name
4. Click 'Connect'

Features Available After Connection:
• Video Conferencing with multiple participants
• Audio Conferencing with real-time mixing
• Screen/Slide Sharing (presenter mode)
• Group Text Chat
• File Sharing between participants

Note: This application works only on LAN (Local Area Network)
        """
        
        ttk.Label(conn_frame, text=instructions, justify=tk.LEFT).pack(pady=20)
        
    def setup_communication_tab(self):
        """Setup the main communication tab"""
        self.comm_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.comm_frame, text="Communication", state=tk.DISABLED)
        
        # Main container with paned window
        main_paned = ttk.PanedWindow(self.comm_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for video and controls
        left_panel = ttk.Frame(main_paned)
        main_paned.add(left_panel, weight=3)
        
        # Video section
        video_frame = ttk.LabelFrame(left_panel, text="Video Conference")
        video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Main video area (presenter or main speaker)
        self.main_video_frame = ttk.LabelFrame(video_frame, text="Main View")
        self.main_video_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.main_video_label = ttk.Label(self.main_video_frame, text="No video feed")
        self.main_video_label.pack(expand=True)
        
        # Participants video grid
        participants_frame = ttk.LabelFrame(video_frame, text="Participants")
        participants_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Scrollable frame for participant videos
        canvas = tk.Canvas(participants_frame, height=120)
        scrollbar = ttk.Scrollbar(participants_frame, orient="horizontal", command=canvas.xview)
        self.participants_scroll_frame = ttk.Frame(canvas)
        
        self.participants_scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.participants_scroll_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)
        
        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")
        
        # Your video preview
        your_video_frame = ttk.LabelFrame(video_frame, text="Your Video")
        your_video_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.your_video_label = ttk.Label(your_video_frame, text="Camera off")
        self.your_video_label.pack(pady=5)
        
        # Controls
        controls_frame = ttk.LabelFrame(left_panel, text="Controls")
        controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        controls_inner = ttk.Frame(controls_frame)
        controls_inner.pack(fill=tk.X, padx=10, pady=10)
        
        # Media controls
        media_frame = ttk.Frame(controls_inner)
        media_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.video_btn = ttk.Button(media_frame, text="Start Video", command=self.toggle_video)
        self.video_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.audio_btn = ttk.Button(media_frame, text="Start Audio", command=self.toggle_audio)
        self.audio_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Presentation controls
        present_frame = ttk.Frame(controls_inner)
        present_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.present_btn = ttk.Button(present_frame, text="Start Presenting", command=self.toggle_presentation)
        self.present_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.screen_share_btn = ttk.Button(present_frame, text="Share Screen", command=self.toggle_screen_share, state=tk.DISABLED)
        self.screen_share_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Disconnect
        self.disconnect_btn = ttk.Button(controls_inner, text="Disconnect", command=self.disconnect)
        self.disconnect_btn.pack(side=tk.RIGHT)
        
        # Right panel for chat and participants
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, weight=1)
        
        # Participants list
        participants_list_frame = ttk.LabelFrame(right_panel, text="Participants")
        participants_list_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.participants_listbox = tk.Listbox(participants_list_frame, height=6)
        self.participants_listbox.pack(fill=tk.X, padx=5, pady=5)
        
        # Chat section
        chat_frame = ttk.LabelFrame(right_panel, text="Group Chat")
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, height=15, state=tk.DISABLED, wrap=tk.WORD)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Chat input
        chat_input_frame = ttk.Frame(chat_frame)
        chat_input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.chat_entry = ttk.Entry(chat_input_frame)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.chat_entry.bind("<Return>", self.send_chat_message)
        
        ttk.Button(chat_input_frame, text="Send", command=self.send_chat_message).pack(side=tk.RIGHT)
        
    def setup_file_sharing_tab(self):
        """Setup the file sharing tab"""
        self.file_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.file_frame, text="File Sharing", state=tk.DISABLED)
        
        # Upload section
        upload_frame = ttk.LabelFrame(self.file_frame, text="Share File")
        upload_frame.pack(fill=tk.X, padx=10, pady=10)
        
        upload_inner = ttk.Frame(upload_frame)
        upload_inner.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(upload_inner, text="Select File to Share", command=self.select_file_to_share).pack(side=tk.LEFT)
        
        self.selected_file_label = ttk.Label(upload_inner, text="No file selected")
        self.selected_file_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Available files section
        files_frame = ttk.LabelFrame(self.file_frame, text="Available Files")
        files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Files list
        self.files_tree = ttk.Treeview(files_frame, columns=('Name', 'Size', 'Sender'), show='headings')
        self.files_tree.heading('Name', text='File Name')
        self.files_tree.heading('Size', text='Size')
        self.files_tree.heading('Sender', text='Shared By')
        
        files_scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_scrollbar.set)
        
        self.files_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        files_scrollbar.pack(side="right", fill="y", pady=5)
        
        # Download button
        download_frame = ttk.Frame(self.file_frame)
        download_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(download_frame, text="Download Selected File", command=self.download_selected_file).pack()
        
    def connect_to_server(self):
        """Connect to the communication server"""
        try:
            self.server_host = self.server_ip_entry.get().strip()
            self.client_name = self.name_entry.get().strip()
            
            if not self.server_host or not self.client_name:
                messagebox.showerror("Error", "Please enter server IP and your name")
                return
                
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
            
            # Update GUI
            self.conn_status_label.config(text="Connected!")
            self.connect_btn.config(state=tk.DISABLED)
            self.server_ip_entry.config(state=tk.DISABLED)
            self.name_entry.config(state=tk.DISABLED)
            
            # Enable communication tabs
            self.notebook.tab(1, state=tk.NORMAL)
            self.notebook.tab(2, state=tk.NORMAL)
            self.notebook.select(1)
            
            messagebox.showinfo("Connected", "Successfully connected to the server!")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.conn_status_label.config(text="Connection failed")
            
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
            self.root.after(0, lambda: self.present_btn.config(text="Stop Presenting"))
            self.root.after(0, lambda: self.screen_share_btn.config(state=tk.NORMAL))
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
                self.root.after(0, lambda: self.present_btn.config(text="Start Presenting"))
                self.root.after(0, lambda: self.screen_share_btn.config(state=tk.DISABLED))
            self.presenter_id = None
            self.root.after(0, lambda: self.add_chat_message("System", "Presentation stopped"))
            
        elif msg_type == 'host_status_update':
            # Update Host status in clients list
            host_id = str(message.get('host_id', 0))
            if host_id in self.clients_list:
                self.clients_list[host_id]['video_enabled'] = message.get('video_enabled', False)
                self.clients_list[host_id]['audio_enabled'] = message.get('audio_enabled', False)
                self.root.after(0, self.update_participants_list)
            
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
                messagebox.showerror("Error", "Cannot access camera")
                return
                
            self.video_enabled = True
            self.video_btn.config(text="Stop Video")
            
            # Start video streaming thread
            threading.Thread(target=self.video_stream_loop, daemon=True).start()
            
            # Notify server
            status_msg = {'type': 'video_status', 'enabled': True}
            self.send_tcp_message(status_msg)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start video: {str(e)}")
            
    def stop_video(self):
        """Stop video capture and streaming"""
        self.video_enabled = False
        self.video_btn.config(text="Start Video")
        
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
            
        # Clear video display
        self.your_video_label.config(image="", text="Camera off")
        
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
                display_frame = cv2.resize(frame, (200, 150))
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
            self.audio_btn.config(text="Stop Audio")
            
            # Start audio streaming thread
            threading.Thread(target=self.audio_stream_loop, daemon=True).start()
            
            # Notify server
            status_msg = {'type': 'audio_status', 'enabled': True}
            self.send_tcp_message(status_msg)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start audio: {str(e)}")
            
    def stop_audio(self):
        """Stop audio capture and streaming"""
        self.audio_enabled = False
        self.audio_btn.config(text="Start Audio")
        
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
            
    def toggle_screen_share(self):
        """Toggle screen sharing"""
        if not self.screen_sharing:
            self.start_screen_share()
        else:
            self.stop_screen_share()
            
    def start_screen_share(self):
        """Start screen sharing"""
        self.screen_sharing = True
        self.screen_share_btn.config(text="Stop Sharing")
        # Implementation for screen capture and sharing
        
    def stop_screen_share(self):
        """Stop screen sharing"""
        self.screen_sharing = False
        self.screen_share_btn.config(text="Share Screen")
        
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
        timestamp = datetime.now().strftime("%H:%M:%S")
        chat_line = f"[{timestamp}] {sender}: {message}\n"
        
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
                time_obj = datetime.fromisoformat(timestamp)
                time_str = time_obj.strftime("%H:%M:%S")
            else:
                time_str = "??:??:??"
                
            chat_line = f"[{time_str}] {sender}: {message}\n"
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
            status = client_info.get('status', 'Unknown')
            
            # Add status indicators
            status_indicators = []
            if client_info.get('video_enabled'):
                status_indicators.append("Video")
            if client_info.get('audio_enabled'):
                status_indicators.append("Audio")
            if status_indicators:
                status += f" ({', '.join(status_indicators)})"
            
            if client_id == str(self.client_id):
                name += " (You)"
            elif client_id == str(getattr(self, 'host_id', 0)):
                name = f"🏠 {name}"  # Host indicator
            if client_id == str(self.presenter_id):
                name += " [Presenter]"
                
            self.participants_listbox.insert(tk.END, f"{name} - {status}")
            
    def select_file_to_share(self):
        """Select file to share"""
        filename = filedialog.askopenfilename(
            title="Select file to share",
            filetypes=[("All files", "*.*")]
        )
        
        if filename:
            self.selected_file_label.config(text=os.path.basename(filename))
            # Implementation for file sharing
            
    def download_selected_file(self):
        """Download selected file"""
        selection = self.files_tree.selection()
        if selection:
            # Implementation for file download
            pass
            
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
            
        # Reset GUI
        self.notebook.tab(1, state=tk.DISABLED)
        self.notebook.tab(2, state=tk.DISABLED)
        self.notebook.select(0)
        
        self.connect_btn.config(state=tk.NORMAL)
        self.server_ip_entry.config(state=tk.NORMAL)
        self.name_entry.config(state=tk.NORMAL)
        self.conn_status_label.config(text="Disconnected")
        
        # Clear displays
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self.participants_listbox.delete(0, tk.END)
        
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