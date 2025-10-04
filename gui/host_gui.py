"""
Host GUI for the LAN Video Calling Application
Provides meeting control and monitoring capabilities for the host
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from typing import Dict, Any, Optional, List
from server.host_server import HostServer
from shared.utils import logger, get_local_ip


class HostGUI:
    """Host GUI for meeting control and monitoring"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAN Video Call - Host Control Panel")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Server instance
        self.server: Optional[HostServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.is_server_running = False
        
        # GUI variables
        self.host_username_var = tk.StringVar(value="Host")
        self.server_host_var = tk.StringVar(value="0.0.0.0")
        self.server_port_var = tk.StringVar(value="8888")
        
        # Meeting control variables
        self.mute_all_var = tk.BooleanVar()
        self.disable_video_all_var = tk.BooleanVar()
        self.recording_var = tk.BooleanVar()
        self.chat_enabled_var = tk.BooleanVar(value=True)
        self.file_sharing_enabled_var = tk.BooleanVar(value=True)
        
        # Statistics
        self.participants = {}
        self.rooms = {}
        self.chat_messages = []
        
        self.setup_gui()
        self.start_update_thread()
    
    def setup_gui(self):
        """Setup the GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="LAN Video Call - Host Control Panel", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Server control section
        self.setup_server_controls(main_frame)
        
        # Main content area
        self.setup_main_content(main_frame)
        
        # Status bar
        self.setup_status_bar(main_frame)
    
    def setup_server_controls(self, parent):
        """Setup server control section"""
        server_frame = ttk.LabelFrame(parent, text="Server Control", padding="10")
        server_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Server settings
        ttk.Label(server_frame, text="Host Username:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(server_frame, textvariable=self.host_username_var, width=15).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(server_frame, text="Server Host:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Entry(server_frame, textvariable=self.server_host_var, width=15).grid(row=0, column=3, padx=(0, 20))
        
        ttk.Label(server_frame, text="Port:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        ttk.Entry(server_frame, textvariable=self.server_port_var, width=8).grid(row=0, column=5, padx=(0, 20))
        
        # Server buttons
        self.start_button = ttk.Button(server_frame, text="Start Server", command=self.start_server)
        self.start_button.grid(row=0, column=6, padx=(0, 10))
        
        self.stop_button = ttk.Button(server_frame, text="Stop Server", command=self.stop_server, state='disabled')
        self.stop_button.grid(row=0, column=7)
        
        # Server status
        self.server_status_label = ttk.Label(server_frame, text="Server: Stopped", foreground='red')
        self.server_status_label.grid(row=1, column=0, columnspan=8, pady=(10, 0))
    
    def setup_main_content(self, parent):
        """Setup main content area"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Meeting controls tab
        self.setup_meeting_controls_tab()
        
        # Participants tab
        self.setup_participants_tab()
        
        # Chat monitoring tab
        self.setup_chat_monitoring_tab()
        
        # Statistics tab
        self.setup_statistics_tab()
    
    def setup_meeting_controls_tab(self):
        """Setup meeting controls tab"""
        controls_frame = ttk.Frame(self.notebook)
        self.notebook.add(controls_frame, text="Meeting Controls")
        
        # Audio controls
        audio_frame = ttk.LabelFrame(controls_frame, text="Audio Controls", padding="10")
        audio_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(audio_frame, text="Mute All Participants", 
                       variable=self.mute_all_var, command=self.toggle_mute_all).pack(anchor=tk.W)
        
        # Video controls
        video_frame = ttk.LabelFrame(controls_frame, text="Video Controls", padding="10")
        video_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(video_frame, text="Disable Video for All Participants", 
                       variable=self.disable_video_all_var, command=self.toggle_disable_video_all).pack(anchor=tk.W)
        
        # Recording controls
        recording_frame = ttk.LabelFrame(controls_frame, text="Recording Controls", padding="10")
        recording_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(recording_frame, text="Recording", 
                       variable=self.recording_var, command=self.toggle_recording).pack(anchor=tk.W)
        
        # Feature controls
        features_frame = ttk.LabelFrame(controls_frame, text="Feature Controls", padding="10")
        features_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(features_frame, text="Enable Chat", 
                       variable=self.chat_enabled_var, command=self.toggle_chat).pack(anchor=tk.W)
        
        ttk.Checkbutton(features_frame, text="Enable File Sharing", 
                       variable=self.file_sharing_enabled_var, command=self.toggle_file_sharing).pack(anchor=tk.W)
        
        # Participant management
        participant_frame = ttk.LabelFrame(controls_frame, text="Participant Management", padding="10")
        participant_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Participant list for management
        self.participant_tree = ttk.Treeview(participant_frame, columns=('username', 'status', 'room'), show='headings')
        self.participant_tree.heading('username', text='Username')
        self.participant_tree.heading('status', text='Status')
        self.participant_tree.heading('room', text='Room')
        self.participant_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Participant action buttons
        action_frame = ttk.Frame(participant_frame)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="Mute Selected", command=self.mute_selected_participant).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Kick Selected", command=self.kick_selected_participant).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Refresh", command=self.refresh_participants).pack(side=tk.LEFT)
    
    def setup_participants_tab(self):
        """Setup participants monitoring tab"""
        participants_frame = ttk.Frame(self.notebook)
        self.notebook.add(participants_frame, text="Participants")
        
        # Participants list
        self.participants_tree = ttk.Treeview(participants_frame, 
                                            columns=('username', 'user_id', 'room', 'connected_time', 'status'), 
                                            show='headings')
        self.participants_tree.heading('username', text='Username')
        self.participants_tree.heading('user_id', text='User ID')
        self.participants_tree.heading('room', text='Room')
        self.participants_tree.heading('connected_time', text='Connected')
        self.participants_tree.heading('status', text='Status')
        
        # Configure column widths
        self.participants_tree.column('username', width=150)
        self.participants_tree.column('user_id', width=100)
        self.participants_tree.column('room', width=150)
        self.participants_tree.column('connected_time', width=120)
        self.participants_tree.column('status', width=100)
        
        self.participants_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Participants info
        info_frame = ttk.Frame(participants_frame)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.participants_count_label = ttk.Label(info_frame, text="Participants: 0")
        self.participants_count_label.pack(side=tk.LEFT)
        
        ttk.Button(info_frame, text="Refresh", command=self.refresh_participants).pack(side=tk.RIGHT)
    
    def setup_chat_monitoring_tab(self):
        """Setup chat monitoring tab"""
        chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(chat_frame, text="Chat Monitoring")
        
        # Chat messages display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, height=20, state='disabled')
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat controls
        chat_controls = ttk.Frame(chat_frame)
        chat_controls.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(chat_controls, text="Chat Status:").pack(side=tk.LEFT)
        self.chat_status_label = ttk.Label(chat_controls, text="Enabled", foreground='green')
        self.chat_status_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Button(chat_controls, text="Clear Chat", command=self.clear_chat).pack(side=tk.RIGHT)
        ttk.Button(chat_controls, text="Export Chat", command=self.export_chat).pack(side=tk.RIGHT, padx=(0, 5))
    
    def setup_statistics_tab(self):
        """Setup statistics tab"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Statistics")
        
        # Statistics display
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20, state='disabled')
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Refresh button
        ttk.Button(stats_frame, text="Refresh Statistics", command=self.refresh_statistics).pack(pady=(0, 10))
    
    def setup_status_bar(self, parent):
        """Setup status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.time_label = ttk.Label(status_frame, text="")
        self.time_label.pack(side=tk.RIGHT)
    
    def start_server(self):
        """Start the host server"""
        try:
            host = self.server_host_var.get()
            port = int(self.server_port_var.get())
            username = self.host_username_var.get()
            
            if not username:
                messagebox.showerror("Error", "Please enter a host username")
                return
            
            # Create and start server
            self.server = HostServer(host, port, username)
            
            # Start server in separate thread
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            # Update UI
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.server_status_label.config(text=f"Server: Running on {host}:{port}", foreground='green')
            self.status_label.config(text=f"Host server started as '{username}'")
            
            self.is_server_running = True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
            logger.error(f"Failed to start server: {e}")
    
    def stop_server(self):
        """Stop the host server"""
        try:
            if self.server:
                self.server.stop()
                self.server = None
            
            self.is_server_running = False
            
            # Update UI
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.server_status_label.config(text="Server: Stopped", foreground='red')
            self.status_label.config(text="Server stopped")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")
            logger.error(f"Failed to stop server: {e}")
    
    def _run_server(self):
        """Run the server (in separate thread)"""
        try:
            self.server.start_host_mode()
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.root.after(0, lambda: self.stop_server())
    
    def toggle_mute_all(self):
        """Toggle mute all participants"""
        if self.server and self.is_server_running:
            self.server.mute_all_participants(self.mute_all_var.get())
            self.status_label.config(text=f"Mute all: {'ON' if self.mute_all_var.get() else 'OFF'}")
    
    def toggle_disable_video_all(self):
        """Toggle disable video for all participants"""
        if self.server and self.is_server_running:
            self.server.disable_video_all_participants(self.disable_video_all_var.get())
            self.status_label.config(text=f"Disable video all: {'ON' if self.disable_video_all_var.get() else 'OFF'}")
    
    def toggle_recording(self):
        """Toggle recording"""
        if self.server and self.is_server_running:
            if self.recording_var.get():
                self.server.start_recording()
            else:
                self.server.stop_recording()
            self.status_label.config(text=f"Recording: {'ON' if self.recording_var.get() else 'OFF'}")
    
    def toggle_chat(self):
        """Toggle chat"""
        if self.server and self.is_server_running:
            self.server.toggle_chat(self.chat_enabled_var.get())
            self.chat_status_label.config(
                text="Enabled" if self.chat_enabled_var.get() else "Disabled",
                foreground='green' if self.chat_enabled_var.get() else 'red'
            )
    
    def toggle_file_sharing(self):
        """Toggle file sharing"""
        if self.server and self.is_server_running:
            self.server.toggle_file_sharing(self.file_sharing_enabled_var.get())
            self.status_label.config(text=f"File sharing: {'ON' if self.file_sharing_enabled_var.get() else 'OFF'}")
    
    def refresh_participants(self):
        """Refresh participants list"""
        if not self.server or not self.is_server_running:
            return
        
        try:
            # Clear existing items
            for item in self.participants_tree.get_children():
                self.participants_tree.delete(item)
            
            # Get participants from server
            stats = self.server.get_meeting_stats()
            user_stats = stats.get('user_stats', {})
            
            # Add participants
            for user_id, user_info in user_stats.get('users', {}).items():
                if user_id != self.server.host_id:  # Don't show host in participants list
                    self.participants_tree.insert('', 'end', values=(
                        user_info.get('username', 'Unknown'),
                        user_id,
                        user_info.get('room_id', 'None'),
                        time.strftime('%H:%M:%S', time.localtime(user_info.get('connected_time', 0))),
                        'Connected' if user_info.get('is_online', False) else 'Disconnected'
                    ))
            
            # Update count
            participant_count = len([u for u in user_stats.get('users', {}).values() if u.get('user_id') != self.server.host_id])
            self.participants_count_label.config(text=f"Participants: {participant_count}")
            
        except Exception as e:
            logger.error(f"Error refreshing participants: {e}")
    
    def mute_selected_participant(self):
        """Mute selected participant"""
        selection = self.participant_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a participant")
            return
        
        # Implementation for muting individual participants
        messagebox.showinfo("Info", "Individual participant muting not yet implemented")
    
    def kick_selected_participant(self):
        """Kick selected participant"""
        selection = self.participant_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a participant")
            return
        
        item = self.participant_tree.item(selection[0])
        username = item['values'][0]
        user_id = item['values'][1]
        
        if messagebox.askyesno("Confirm", f"Are you sure you want to kick {username}?"):
            if self.server and self.is_server_running:
                success = self.server.kick_participant(user_id, "Kicked by host")
                if success:
                    self.status_label.config(text=f"Kicked participant: {username}")
                    self.refresh_participants()
                else:
                    messagebox.showerror("Error", "Failed to kick participant")
    
    def clear_chat(self):
        """Clear chat display"""
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state='disabled')
    
    def export_chat(self):
        """Export chat to file"""
        # Implementation for chat export
        messagebox.showinfo("Info", "Chat export not yet implemented")
    
    def refresh_statistics(self):
        """Refresh statistics display"""
        if not self.server or not self.is_server_running:
            return
        
        try:
            stats = self.server.get_meeting_stats()
            
            # Format statistics
            stats_text = f"""Server Statistics
================

Server Information:
- Host: {stats.get('host', 'Unknown')}
- Port: {stats.get('port', 'Unknown')}
- Uptime: {stats.get('uptime', 0):.1f} seconds
- Status: {'Running' if stats.get('is_running', False) else 'Stopped'}

Connection Statistics:
- Total Connections: {stats.get('total_connections', 0)}
- Active Connections: {stats.get('active_connections', 0)}

User Statistics:
- Online Users: {stats.get('user_stats', {}).get('online_users', 0)}
- Total Users: {stats.get('user_stats', {}).get('total_users', 0)}

Room Statistics:
- Active Rooms: {stats.get('room_stats', {}).get('active_rooms', 0)}
- Total Rooms: {stats.get('room_stats', {}).get('total_rooms', 0)}

File Statistics:
- Total Files: {stats.get('file_stats', {}).get('total_files', 0)}
- Files Uploaded: {stats.get('file_stats', {}).get('files_uploaded', 0)}
- Files Downloaded: {stats.get('file_stats', {}).get('files_downloaded', 0)}

Media Statistics:
- Video Frames Processed: {stats.get('media_stats', {}).get('video_frames_processed', 0)}
- Audio Frames Processed: {stats.get('media_stats', {}).get('audio_frames_processed', 0)}

Meeting Controls:
- Mute All: {'ON' if stats.get('meeting_controls', {}).get('mute_all', False) else 'OFF'}
- Disable Video All: {'ON' if stats.get('meeting_controls', {}).get('disable_video_all', False) else 'OFF'}
- Recording: {'ON' if stats.get('meeting_controls', {}).get('recording', False) else 'OFF'}
- Chat Enabled: {'ON' if stats.get('meeting_controls', {}).get('chat_enabled', True) else 'OFF'}
- File Sharing Enabled: {'ON' if stats.get('meeting_controls', {}).get('file_sharing_enabled', True) else 'OFF'}

Host Information:
- Host Username: {stats.get('host_username', 'Unknown')}
- Host ID: {stats.get('host_id', 'Unknown')}
- Host Connected: {'Yes' if stats.get('is_host_connected', False) else 'No'}
"""
            
            # Update display
            self.stats_text.config(state='normal')
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            self.stats_text.config(state='disabled')
            
        except Exception as e:
            logger.error(f"Error refreshing statistics: {e}")
    
    def start_update_thread(self):
        """Start thread for updating GUI"""
        def update_loop():
            while True:
                try:
                    # Update time
                    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
                    self.root.after(0, lambda: self.time_label.config(text=current_time))
                    
                    # Update participants if server is running
                    if self.is_server_running:
                        self.root.after(0, self.refresh_participants)
                    
                    time.sleep(5)  # Update every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Error in update thread: {e}")
                    time.sleep(5)
        
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
    
    def run(self):
        """Run the GUI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop_server()
        except Exception as e:
            logger.error(f"GUI error: {e}")
        finally:
            if self.server:
                self.server.stop()


def main():
    """Main function to start the host GUI"""
    try:
        app = HostGUI()
        app.run()
    except Exception as e:
        logger.error(f"Failed to start host GUI: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
