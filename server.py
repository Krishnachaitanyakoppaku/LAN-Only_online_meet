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
        
        self.start_btn = ttk.Button(controls_inner, text="Start Server", command=self.start_server)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(controls_inner, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_label = ttk.Label(controls_inner, text="Server Stopped")
        self.status_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Server info
        info_frame = ttk.LabelFrame(main_frame, text="Server Information")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_inner = ttk.Frame(info_frame)
        info_inner.pack(fill=tk.X, padx=10, pady=10)
        
        self.server_info_text = tk.Text(info_inner, height=4, state=tk.DISABLED)
        self.server_info_text.pack(fill=tk.X)
        
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
        
        # Activity log
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
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
            info = f"""Server Status: RUNNING
Local IP: {local_ip}
TCP Port: {self.tcp_port} (Control, Chat, Files)
UDP Video Port: {self.udp_video_port}
UDP Audio Port: {self.udp_audio_port}
Connected Clients: {len(self.clients)}"""
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
            welcome_msg = {
                'type': 'welcome',
                'client_id': client_id,
                'clients': {cid: {'name': info['name'], 'status': info['status']} 
                           for cid, info in self.clients.items()},
                'chat_history': self.chat_history,
                'presenter_id': self.presenter_id
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
        
    def update_clients_display(self):
        """Update the clients display in GUI"""
        # Clear existing items
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)
            
        # Add current clients
        for client_id, client_info in self.clients.items():
            self.clients_tree.insert('', 'end', values=(
                client_id,
                client_info['name'],
                client_info['address'][0],
                client_info['status']
            ))
            
    def stop_server(self):
        """Stop the communication server"""
        self.running = False
        
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