"""
Server GUI for the LAN Video Calling Application
Provides a management interface for the server
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from typing import Dict, Any
from server.main_server import LANVideoServer
from shared.utils import logger, get_local_ip


class ServerGUI:
    """Server management GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAN Video Calling Server")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Server instance
        self.server: LANVideoServer = None
        self.is_running = False
        
        # GUI variables
        self.host_var = tk.StringVar(value="0.0.0.0")
        self.port_var = tk.StringVar(value="8888")
        self.status_var = tk.StringVar(value="Stopped")
        
        # Create GUI
        self.create_widgets()
        
        # Update thread
        self.update_thread = threading.Thread(target=self.update_stats, daemon=True)
        self.update_thread.start()
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Server configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Server Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Host
        ttk.Label(config_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        host_entry = ttk.Entry(config_frame, textvariable=self.host_var, width=20)
        host_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Port
        ttk.Label(config_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        port_entry = ttk.Entry(config_frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        # Status
        ttk.Label(config_frame, text="Status:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        status_label = ttk.Label(config_frame, textvariable=self.status_var, foreground="red")
        status_label.grid(row=0, column=5, sticky=tk.W)
        
        # Control buttons
        self.start_button = ttk.Button(config_frame, text="Start Server", command=self.start_server)
        self.start_button.grid(row=0, column=6, padx=(20, 5))
        
        self.stop_button = ttk.Button(config_frame, text="Stop Server", command=self.stop_server, state="disabled")
        self.stop_button.grid(row=0, column=7, padx=5)
        
        # Server info frame
        info_frame = ttk.LabelFrame(main_frame, text="Server Information", padding="10")
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        # Local IP
        ttk.Label(info_frame, text="Local IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.local_ip_label = ttk.Label(info_frame, text=get_local_ip())
        self.local_ip_label.grid(row=0, column=1, sticky=tk.W)
        
        # Server URL
        ttk.Label(info_frame, text="Server URL:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.server_url_label = ttk.Label(info_frame, text="Not running")
        self.server_url_label.grid(row=1, column=1, sticky=tk.W)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(main_frame, text="Server Statistics", padding="10")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        stats_frame.columnconfigure(1, weight=1)
        
        # Create statistics labels
        self.stats_labels = {}
        stats_items = [
            ("Uptime", "uptime"),
            ("Total Connections", "total_connections"),
            ("Active Connections", "active_connections"),
            ("Online Users", "online_users"),
            ("Active Rooms", "active_rooms"),
            ("Total Files", "total_files"),
            ("Active Video Streams", "active_video_streams"),
            ("Active Audio Streams", "active_audio_streams")
        ]
        
        for i, (label_text, key) in enumerate(stats_items):
            ttk.Label(stats_frame, text=f"{label_text}:").grid(row=i//2, column=(i%2)*2, sticky=tk.W, padx=(0, 5))
            self.stats_labels[key] = ttk.Label(stats_frame, text="0")
            self.stats_labels[key].grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=(0, 20))
        
        # Users frame
        users_frame = ttk.LabelFrame(main_frame, text="Connected Users", padding="10")
        users_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        users_frame.columnconfigure(0, weight=1)
        users_frame.rowconfigure(1, weight=1)
        
        # Users treeview
        self.users_tree = ttk.Treeview(users_frame, columns=("username", "room", "status"), show="headings")
        self.users_tree.heading("username", text="Username")
        self.users_tree.heading("room", text="Room")
        self.users_tree.heading("status", text="Status")
        self.users_tree.column("username", width=150)
        self.users_tree.column("room", width=150)
        self.users_tree.column("status", width=100)
        self.users_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Users scrollbar
        users_scrollbar = ttk.Scrollbar(users_frame, orient="vertical", command=self.users_tree.yview)
        users_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.users_tree.configure(yscrollcommand=users_scrollbar.set)
        
        # Rooms frame
        rooms_frame = ttk.LabelFrame(main_frame, text="Active Rooms", padding="10")
        rooms_frame.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        rooms_frame.columnconfigure(0, weight=1)
        rooms_frame.rowconfigure(1, weight=1)
        
        # Rooms treeview
        self.rooms_tree = ttk.Treeview(rooms_frame, columns=("name", "participants", "created"), show="headings")
        self.rooms_tree.heading("name", text="Room Name")
        self.rooms_tree.heading("participants", text="Participants")
        self.rooms_tree.heading("created", text="Created")
        self.rooms_tree.column("name", width=150)
        self.rooms_tree.column("participants", width=100)
        self.rooms_tree.column("created", width=120)
        self.rooms_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Rooms scrollbar
        rooms_scrollbar = ttk.Scrollbar(rooms_frame, orient="vertical", command=self.rooms_tree.yview)
        rooms_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.rooms_tree.configure(yscrollcommand=rooms_scrollbar.set)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Server Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state="disabled")
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main frame grid weights
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(4, weight=1)
    
    def start_server(self):
        """Start the server"""
        try:
            host = self.host_var.get().strip()
            port = int(self.port_var.get().strip())
            
            if not host or not port:
                messagebox.showerror("Error", "Please enter valid host and port")
                return
            
            # Create and start server
            self.server = LANVideoServer(host, port)
            
            if self.server.start():
                self.is_running = True
                self.status_var.set("Running")
                self.start_button.config(state="disabled")
                self.stop_button.config(state="normal")
                
                # Update server URL
                self.server_url_label.config(text=f"http://{host}:{port}")
                
                self.log_message("Server started successfully")
            else:
                messagebox.showerror("Error", "Failed to start server")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid port number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
    
    def stop_server(self):
        """Stop the server"""
        try:
            if self.server:
                self.server.stop()
                self.server = None
            
            self.is_running = False
            self.status_var.set("Stopped")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            
            # Clear server URL
            self.server_url_label.config(text="Not running")
            
            # Clear statistics
            for label in self.stats_labels.values():
                label.config(text="0")
            
            # Clear trees
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            for item in self.rooms_tree.get_children():
                self.rooms_tree.delete(item)
            
            self.log_message("Server stopped")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")
    
    def update_stats(self):
        """Update server statistics"""
        while True:
            try:
                if self.is_running and self.server:
                    # Get server info
                    server_info = self.server.get_server_info()
                    
                    # Update statistics labels
                    self.root.after(0, self.update_stats_labels, server_info)
                    
                    # Update users tree
                    self.root.after(0, self.update_users_tree, server_info)
                    
                    # Update rooms tree
                    self.root.after(0, self.update_rooms_tree, server_info)
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                logger.error(f"Error updating stats: {e}")
                time.sleep(5)
    
    def update_stats_labels(self, server_info: Dict[str, Any]):
        """Update statistics labels"""
        try:
            # Format uptime
            uptime = server_info.get('uptime', 0)
            uptime_str = f"{int(uptime//3600):02d}:{int((uptime%3600)//60):02d}:{int(uptime%60):02d}"
            
            # Update labels
            self.stats_labels['uptime'].config(text=uptime_str)
            self.stats_labels['total_connections'].config(text=str(server_info.get('total_connections', 0)))
            self.stats_labels['active_connections'].config(text=str(server_info.get('active_connections', 0)))
            
            # User stats
            user_stats = server_info.get('user_stats', {})
            self.stats_labels['online_users'].config(text=str(user_stats.get('online_users', 0)))
            
            # Room stats
            room_stats = server_info.get('room_stats', {})
            self.stats_labels['active_rooms'].config(text=str(room_stats.get('active_rooms', 0)))
            
            # File stats
            file_stats = server_info.get('file_stats', {})
            self.stats_labels['total_files'].config(text=str(file_stats.get('total_files', 0)))
            
            # Media stats
            media_stats = server_info.get('media_stats', {})
            self.stats_labels['active_video_streams'].config(text=str(media_stats.get('active_video_streams', 0)))
            self.stats_labels['active_audio_streams'].config(text=str(media_stats.get('active_audio_streams', 0)))
            
        except Exception as e:
            logger.error(f"Error updating stats labels: {e}")
    
    def update_users_tree(self, server_info: Dict[str, Any]):
        """Update users tree"""
        try:
            # Clear existing items
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            # Get users from server
            if self.server and self.server.user_manager:
                users = self.server.user_manager.get_online_users()
                
                for user in users:
                    status = "Online"
                    if user.is_muted:
                        status += " (Muted)"
                    if user.is_video_enabled:
                        status += " (Video)"
                    if user.is_audio_enabled:
                        status += " (Audio)"
                    if user.is_screen_sharing:
                        status += " (Screen)"
                    
                    self.users_tree.insert("", "end", values=(
                        user.username,
                        user.room_id or "None",
                        status
                    ))
        
        except Exception as e:
            logger.error(f"Error updating users tree: {e}")
    
    def update_rooms_tree(self, server_info: Dict[str, Any]):
        """Update rooms tree"""
        try:
            # Clear existing items
            for item in self.rooms_tree.get_children():
                self.rooms_tree.delete(item)
            
            # Get rooms from server
            if self.server and self.server.room_manager:
                rooms = self.server.room_manager.get_room_list(include_private=True)
                
                for room in rooms:
                    created_time = time.strftime("%H:%M:%S", time.localtime(room['created_at']))
                    self.rooms_tree.insert("", "end", values=(
                        room['room_name'],
                        room['participant_count'],
                        created_time
                    ))
        
        except Exception as e:
            logger.error(f"Error updating rooms tree: {e}")
    
    def log_message(self, message: str):
        """Add message to log"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
            
        except Exception as e:
            logger.error(f"Error logging message: {e}")
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Server is running. Do you want to stop it and quit?"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()


def main():
    """Main function"""
    try:
        app = ServerGUI()
        app.run()
    except Exception as e:
        logger.error(f"Error running server GUI: {e}")
        messagebox.showerror("Error", f"Failed to start server GUI: {e}")


if __name__ == "__main__":
    main()
