#!/usr/bin/env python3
"""
LAN Communication Server
A comprehensive multi-user communication system for LAN environments

Features:
- Multi-user video conferencing (UDP)
- Multi-user audio conferencing (UDP) 
- Screen/slide sharing (TCP)
- Group text chat (TCP)
- File sharing (TCP)
- Session management
"""

import socket
import threading
import json
import time
import struct
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import queue
import cv2
import pyaudio
from PIL import Image, ImageTk

class LANCommunicationServer:
    def __init__(self):
        # Network configuration
        self.host = '0.0.0.0'
        self.tcp_port = 8888  # Main TCP port for control, chat, files
        self.udp_video_port = 8889  # UDP port for video streams
        self.udp_audio_port = 8890  # UDP port for audio streams
        
        # Server state
        self.running = False
        self.clients = {}  # {client_id: client_info}
        self.next_client_id = 1
        
        # Host participant info
        self.host_id = 0  # Server acts as participant with ID 0
        self.host_name = "Host"
        self.host_video_enabled = False
        self.host_audio_enabled = False
        
        # Sockets
        self.tcp_socket = None
        self.udp_video_socket = None
        self.udp_audio_socket = None
        
        # Session management
        self.presenter_id = None
        self.chat_history = []
        self.shared_files = {}  # {filename: file_info}
        
        # Threading
        self.client_threads = []
        self.message_queue = queue.Queue()
        
        # Media devices for Host
        self.video_cap = None
        self.audio_stream = None
        self.audio = None
        
        # GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Initialize the server GUI"""
        self.root = tk.Tk()
        self.root.title("LAN Communication Server")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Server controls
        control_frame = ttk.LabelFrame(main_frame, text="Server Controls")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        controls_inner = ttk.Frame(control_frame)
        controls_inner.pack(fill=tk.X, padx=10, pady=10)
        
        # Server management
        server_mgmt = ttk.Frame(controls_inner)
        server_mgmt.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(server_mgmt, text="Start Server", command=self.start_server)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(server_mgmt, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_label = ttk.Label(server_mgmt, text="Server Stopped")
        self.status_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Host participant controls
        host_controls = ttk.Frame(controls_inner)
        host_controls.pack(fill=tk.X)
        
        ttk.Label(host_controls, text="Host Controls:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.host_video_btn = ttk.Button(host_controls, text="Start Video", command=self.toggle_host_video, state=tk.DISABLED)
        self.host_video_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.host_audio_btn = ttk.Button(host_controls, text="Start Audio", command=self.toggle_host_audio, state=tk.DISABLED)
        self.host_audio_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.host_present_btn = ttk.Button(host_controls, text="Start Presenting", command=self.toggle_host_presentation, state=tk.DISABLED)
        self.host_present_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Host video and server info
        middle_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        middle_paned.pack(fill=tk.X, pady=(0, 10))
        
        # Host video section
        host_video_frame = ttk.LabelFrame(middle_paned, text="Host Video")
        middle_paned.add(host_video_frame, weight=1)
        
        self.host_video_label = ttk.Label(host_video_frame, text="Host video off")
        self.host_video_label.pack(expand=True, padx=10, pady=10)
        
        # Server info
        info_frame = ttk.LabelFrame(middle_paned, text="Server Information")
        middle_paned.add(info_frame, weight=1)
        
        info_inner = ttk.Frame(info_frame)
        info_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.server_info_text = tk.Text(info_inner, height=4, state=tk.DISABLED)
        self.server_info_text.pack(fill=tk.BOTH, expand=True)
        
        # Connected clients
        clients_frame = ttk.LabelFrame(main_frame, text="Connected Clients")
        clients_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Clients list with scrollbar
        clients_inner = ttk.Frame(clients_frame)
        clients_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.clients_tree = ttk.Treeview(clients_inner, columns=('ID', 'Name', 'IP', 'Status'), show='headings')
        self.clients_tree.heading('ID', text='ID')
        self.clients_tree.heading('Name', text='Name')
        self.clients_tree.heading('IP', text='IP Address')
        self.clients_tree.heading('Status', text='Status')
        
        self.clients_tree.column('ID', width=50)
        self.clients_tree.column('Name', width=150)
        self.clients_tree.column('IP', width=120)
        self.clients_tree.column('Status', width=100)
        
        clients_scrollbar = ttk.Scrollbar(clients_inner, orient="vertical", command=self.clients_tree.yview)
        self.clients_tree.configure(yscrollcommand=clients_scrollbar.set)
        
        self.clients_tree.pack(side="left", fill="both", expand=True)
        clients_scrollbar.pack(side="right", fill="y")
        
        # Bottom section with chat and activity log
        bottom_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        bottom_paned.pack(fill=tk.BOTH, expand=True)
        
        # Host chat section
        chat_frame = ttk.LabelFrame(bottom_paned, text="Group Chat")
        bottom_paned.add(chat_frame, weight=1)
        
        chat_inner = ttk.Frame(chat_frame)
        chat_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_display = tk.Text(chat_inner, height=8, state=tk.DISABLED, wrap=tk.WORD)
        chat_scrollbar = ttk.Scrollbar(chat_inner, orient="vertical", command=self.chat_display.yview)
        self.chat_display.configure(yscrollcommand=chat_scrollbar.set)
        
        self.chat_display.pack(side="left", fill="both", expand=True)
        chat_scrollbar.pack(side="right", fill="y")
        
        # Chat input
        chat_input_frame = ttk.Frame(chat_frame)
        chat_input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.chat_entry = ttk.Entry(chat_input_frame, state=tk.DISABLED)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.chat_entry.bind("<Return>", self.send_host_chat_message)
        
        self.chat_send_btn = ttk.Button(chat_input_frame, text="Send", command=self.send_host_chat_message, state=tk.DISABLED)
        self.chat_send_btn.pack(side=tk.RIGHT)
        
        # Activity log
        log_frame = ttk.LabelFrame(bottom_paned, text="Activity Log")
        bottom_paned.add(log_frame, weight=1)
        
        log_inner = ttk.Frame(log_frame)
        log_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(log_inner, height=8, state=tk.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_inner, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
    def log_message(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        print(log_entry.strip())  # Also print to console
        
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
            
    def update_server_info(self):
        """Update server information display"""
        if self.running:
            local_ip = self.get_local_ip()
            total_participants = len(self.clients) + 1  # +1 for Host
            info = f"""Server Status: RUNNING
Local IP: {local_ip}
TCP Port: {self.tcp_port} (Control, Chat, Files)
UDP Video Port: {self.udp_video_port}
UDP Audio Port: {self.udp_audio_port}
Total Participants: {total_participants} (Host + {len(self.clients)} clients)"""
        else:
            info = "Server Status: STOPPED"
            
        self.server_info_text.config(state=tk.NORMAL)
        self.server_info_text.delete(1.0, tk.END)
        self.server_info_text.insert(1.0, info)
        self.server_info_text.config(state=tk.DISABLED)
        
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
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Server Running")
            self.update_server_info()
            
            self.log_message("Server started successfully")
            self.log_message(f"Listening on {self.get_local_ip()}:{self.tcp_port}")
            
            # Enable host controls
            self.host_video_btn.config(state=tk.NORMAL)
            self.host_audio_btn.config(state=tk.NORMAL)
            self.host_present_btn.config(state=tk.NORMAL)
            self.chat_entry.config(state=tk.NORMAL)
            self.chat_send_btn.config(state=tk.NORMAL)
            
            # Add Host to the session
            self.add_host_to_session()
            
            messagebox.showinfo("Server Started", 
                              f"Server is running on {self.get_local_ip()}:{self.tcp_port}")
            
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
                client_info = {
                    'id': client_id,
                    'socket': client_socket,
                    'address': address,
                    'name': f'Client_{client_id}',
                    'status': 'Connected',
                    'video_enabled': False,
                    'audio_enabled': False,
                    'last_seen': time.time()
                }
                
                self.clients[client_id] = client_info
                
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
        """Process incoming message from client"""
        msg_type = message.get('type')
        
        if msg_type == 'join':
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
                'type': 'welcome',
                'client_id': client_id,
                'clients': all_participants,
                'chat_history': self.chat_history,
                'presenter_id': self.presenter_id,
                'host_id': self.host_id
            }
            self.send_to_client(client_id, welcome_msg)
            
            # Notify other clients
            join_notification = {
                'type': 'user_joined',
                'client_id': client_id,
                'name': client_name
            }
            self.broadcast_message(join_notification, exclude=client_id)
            
            self.log_message(f"Client {client_id} ({client_name}) joined the session")
            self.update_clients_display()
            
        elif msg_type == 'chat':
            # Chat message
            chat_msg = {
                'type': 'chat',
                'client_id': client_id,
                'name': self.clients[client_id]['name'],
                'message': message.get('message', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            self.chat_history.append(chat_msg)
            self.broadcast_message(chat_msg)
            self.log_message(f"Chat from {self.clients[client_id]['name']}: {message.get('message', '')}")
            
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
                
        elif msg_type == 'video_status':
            # Video enable/disable status
            self.clients[client_id]['video_enabled'] = message.get('enabled', False)
            status_msg = {
                'type': 'client_video_status',
                'client_id': client_id,
                'enabled': message.get('enabled', False)
            }
            self.broadcast_message(status_msg, exclude=client_id)
            
        elif msg_type == 'audio_status':
            # Audio enable/disable status
            self.clients[client_id]['audio_enabled'] = message.get('enabled', False)
            status_msg = {
                'type': 'client_audio_status',
                'client_id': client_id,
                'enabled': message.get('enabled', False)
            }
            self.broadcast_message(status_msg, exclude=client_id)
            
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
                if len(data) < 8:
                    continue
                    
                client_id, sequence, frame_size = struct.unpack('!III', data[:12])
                frame_data = data[12:]
                
                # Broadcast to other clients
                for cid, client_info in self.clients.items():
                    if cid != client_id and client_info.get('video_enabled', False):
                        try:
                            client_address = (client_info['address'][0], self.udp_video_port + cid)
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
                
                # Simple audio mixing (just broadcast to others for now)
                for cid, client_info in self.clients.items():
                    if cid != client_id and client_info.get('audio_enabled', False):
                        try:
                            client_address = (client_info['address'][0], self.udp_audio_port + cid)
                            self.udp_audio_socket.sendto(data, client_address)
                        except:
                            pass
                            
            except Exception as e:
                if self.running:
                    self.log_message(f"UDP audio error: {str(e)}")
                    
    def process_messages(self):
        """Process queued messages"""
        while self.running:
            try:
                # Process any queued GUI updates
                self.root.update_idletasks()
                time.sleep(0.1)
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
        """Update the clients display in GUI"""
        # Clear existing items
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)
            
        # Add Host first
        host_status = "Active"
        if self.host_video_enabled:
            host_status += " (Video)"
        if self.host_audio_enabled:
            host_status += " (Audio)"
        if self.presenter_id == self.host_id:
            host_status += " [Presenter]"
            
        self.clients_tree.insert('', 'end', values=(
            self.host_id,
            self.host_name,
            "Server",
            host_status
        ))
            
        # Add current clients
        for client_id, client_info in self.clients.items():
            status = client_info['status']
            if client_info.get('video_enabled'):
                status += " (Video)"
            if client_info.get('audio_enabled'):
                status += " (Audio)"
            if self.presenter_id == client_id:
                status += " [Presenter]"
                
            self.clients_tree.insert('', 'end', values=(
                client_id,
                client_info['name'],
                client_info['address'][0],
                status
            ))
            
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
                messagebox.showerror("Error", "Cannot access camera")
                return
                
            self.host_video_enabled = True
            self.host_video_btn.config(text="Stop Video")
            
            # Start video streaming thread
            threading.Thread(target=self.host_video_loop, daemon=True).start()
            
            # Notify clients about Host video status
            self.broadcast_host_status_update()
            self.update_clients_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Host video: {str(e)}")
            
    def stop_host_video(self):
        """Stop Host video"""
        self.host_video_enabled = False
        self.host_video_btn.config(text="Start Video")
        
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
            
        # Clear video display
        self.host_video_label.config(image="", text="Host video off")
        
        # Notify clients
        self.broadcast_host_status_update()
        self.update_clients_display()
        
    def host_video_loop(self):
        """Host video streaming loop"""
        while self.host_video_enabled and self.video_cap:
            try:
                ret, frame = self.video_cap.read()
                if not ret:
                    break
                    
                # Resize and display locally
                display_frame = cv2.resize(frame, (200, 150))
                display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                
                pil_image = Image.fromarray(display_frame_rgb)
                photo = ImageTk.PhotoImage(pil_image)
                
                self.root.after(0, lambda p=photo: self.update_host_video_display(p))
                
                # Broadcast to clients via UDP
                self.broadcast_host_video_frame(frame)
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Host video streaming error: {e}")
                break
                
    def update_host_video_display(self, photo):
        """Update Host video display"""
        self.host_video_label.config(image=photo, text="")
        self.host_video_label.image = photo
        
    def broadcast_host_video_frame(self, frame):
        """Broadcast Host video frame to all clients"""
        try:
            # Compress frame
            frame_resized = cv2.resize(frame, (640, 480))
            _, encoded = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
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
            
    def toggle_host_audio(self):
        """Toggle Host audio on/off"""
        if not self.host_audio_enabled:
            self.start_host_audio()
        else:
            self.stop_host_audio()
            
    def start_host_audio(self):
        """Start Host audio"""
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
            
            self.host_audio_enabled = True
            self.host_audio_btn.config(text="Stop Audio")
            
            # Start audio streaming thread
            threading.Thread(target=self.host_audio_loop, daemon=True).start()
            
            # Notify clients
            self.broadcast_host_status_update()
            self.update_clients_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Host audio: {str(e)}")
            
    def stop_host_audio(self):
        """Stop Host audio"""
        self.host_audio_enabled = False
        self.host_audio_btn.config(text="Start Audio")
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
            
        if self.audio:
            self.audio.terminate()
            self.audio = None
            
        # Notify clients
        self.broadcast_host_status_update()
        self.update_clients_display()
        
    def host_audio_loop(self):
        """Host audio streaming loop"""
        while self.host_audio_enabled and self.audio_stream:
            try:
                # Read audio data
                data = self.audio_stream.read(1024)
                
                # Broadcast to clients via UDP
                self.broadcast_host_audio_data(data)
                
            except Exception as e:
                print(f"Host audio streaming error: {e}")
                break
                
    def broadcast_host_audio_data(self, audio_data):
        """Broadcast Host audio data to all clients"""
        try:
            # Create packet
            timestamp = int(time.time() * 1000) % (2**32)
            packet = struct.pack('!II', self.host_id, timestamp) + audio_data
            
            # Send to all clients
            for client_id, client_info in self.clients.items():
                try:
                    client_address = (client_info['address'][0], self.udp_audio_port)
                    self.udp_audio_socket.sendto(packet, client_address)
                except:
                    pass
                    
        except Exception as e:
            print(f"Error broadcasting Host audio: {e}")
            
    def toggle_host_presentation(self):
        """Toggle Host presentation mode"""
        if self.presenter_id != self.host_id:
            # Become presenter
            if self.presenter_id is None:
                self.presenter_id = self.host_id
                self.host_present_btn.config(text="Stop Presenting")
                
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
            self.presenter_id = None
            self.host_present_btn.config(text="Start Presenting")
            
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
                    time_str = time_obj.strftime("%H:%M:%S")
                except:
                    time_str = "??:??:??"
            else:
                time_str = "??:??:??"
                
            chat_line = f"[{time_str}] {sender}: {message}\n"
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
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Server Stopped")
        
        # Disable host controls
        self.host_video_btn.config(state=tk.DISABLED)
        self.host_audio_btn.config(state=tk.DISABLED)
        self.host_present_btn.config(state=tk.DISABLED)
        self.chat_entry.config(state=tk.DISABLED)
        self.chat_send_btn.config(state=tk.DISABLED)
        
        # Clear displays
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self.update_server_info()
        self.update_clients_display()
        
        self.log_message("Server stopped")
        
    def on_closing(self):
        """Handle window closing"""
        if self.running:
            self.stop_server()
        self.root.destroy()
        
    def run(self):
        """Run the server application"""
        self.root.mainloop()

if __name__ == "__main__":
    server = LANCommunicationServer()
    server.run()