"""
Host GUI for the LAN Video Calling Application
Provides meeting control and monitoring capabilities for the host
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, font
import threading
import time
from typing import Dict, Any, Optional
try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk
    MEDIA_LIBS_AVAILABLE = True
except ImportError:
    MEDIA_LIBS_AVAILABLE = False

from server.host_server import HostServer
from client.main_client import LANVideoClient
from shared.utils import logger, get_local_ip
from .client_gui import VideoDisplay


class HostGUI:
    """Host GUI for meeting control and monitoring"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAN Video Call - Host")
        self.root.geometry("1200x800")
        self.root.configure(bg="#212121")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Server instance
        self.server: Optional[HostServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.is_server_running = False

        # Client instance for host participation
        self.client: Optional[LANVideoClient] = None
        self.is_client_connected = False
        self.is_video_on = False
        self.is_audio_on = False

        # Video displays
        self.video_displays: Dict[str, VideoDisplay] = {}
        self.local_video_display: Optional[VideoDisplay] = None
        
        # GUI variables
        self.host_username = "Host"
        self.server_port = 8888
        
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

        # Child windows
        self.settings_window = None
        self.participants_window = None
        self.chat_window = None
        self.stats_window = None

        self.setup_gui()
        self.start_update_thread()
    
    def setup_gui(self):
        """Setup the GUI layout"""
        # --- Main container for video feeds ---
        self.video_container = tk.Frame(self.root, bg="#212121")
        self.video_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Bottom control bar ---
        self.control_bar = tk.Frame(self.root, bg="#2B2B2B", height=70)
        self.control_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.control_bar.pack_propagate(False) # Prevent resizing

        self.setup_controls()
        self.setup_video_grid()

        # Start server automatically
        self.start_server()

    def setup_controls(self):
        """Sets up the buttons in the bottom control bar."""
        control_font = font.Font(family="Helvetica", size=10)
        button_style = {
            "bg": "#2B2B2B", "fg": "#FFFFFF", "activebackground": "#404040",
            "activeforeground": "#FFFFFF", "bd": 0, "font": control_font,
            "padx": 10, "pady": 5
        }

        # --- Left Controls ---
        left_frame = tk.Frame(self.control_bar, bg=self.control_bar.cget('bg'))
        left_frame.pack(side=tk.LEFT, padx=10)

        self.audio_button = tk.Button(left_frame, text="🎤 Unmute", **button_style, command=self.toggle_audio)
        self.audio_button.pack(side=tk.LEFT, padx=5)

        self.video_button = tk.Button(left_frame, text="📹 Start Video", **button_style, command=self.toggle_video)
        self.video_button.pack(side=tk.LEFT, padx=5)

        # --- Center Controls ---
        center_frame = tk.Frame(self.control_bar, bg=self.control_bar.cget('bg'))
        center_frame.pack(side=tk.LEFT, expand=True, padx=20)

        tk.Button(center_frame, text="👥 Participants", **button_style, command=self.open_participants_window).pack(side=tk.LEFT, padx=5)
        tk.Button(center_frame, text="💬 Chat", **button_style, command=self.open_chat_window).pack(side=tk.LEFT, padx=5)
        tk.Button(center_frame, text="🔼 Share Screen", **button_style).pack(side=tk.LEFT, padx=5) # Placeholder
        tk.Button(center_frame, text="📈 Stats", **button_style, command=self.open_stats_window).pack(side=tk.LEFT, padx=5)
        tk.Button(center_frame, text="⚙️ Settings", **button_style, command=self.open_settings_window).pack(side=tk.LEFT, padx=5)

        # --- Right Controls ---
        right_frame = tk.Frame(self.control_bar, bg=self.control_bar.cget('bg'))
        right_frame.pack(side=tk.RIGHT, padx=10)

        leave_btn = tk.Button(right_frame, text="Leave", bg="#E53935", fg="white", activebackground="#C62828", bd=0, font=control_font, padx=20, pady=5, command=self.on_closing)
        leave_btn.pack(side=tk.RIGHT, padx=10)

    def setup_video_grid(self):
        """Sets up the grid for participant videos."""
        self.video_grid_frame = tk.Frame(self.video_container, bg="#212121")
        self.video_grid_frame.pack(fill=tk.BOTH, expand=True)

        # Host's local video display
        local_video_frame = tk.Frame(self.video_grid_frame, bg="black", borderwidth=1, relief="solid")
        self.local_video_display = VideoDisplay(local_video_frame, 320, 240)
        tk.Label(local_video_frame, text=f"{self.host_username} (You)", bg="#424242", fg="white", anchor="sw", padx=8, pady=4).pack(side="bottom", fill="x")
        
        self.update_video_grid()

    def on_local_frame(self, frame):
        """Callback for receiving local camera frame."""
        if self.local_video_display:
            self.local_video_display.update_frame(frame)

    def on_video_frame_received(self, user_id, frame_data):
        """Handle video frame received from another participant."""
        if user_id not in self.video_displays:
            p_frame = tk.Frame(self.video_grid_frame, bg="black", borderwidth=1, relief="solid")
            display = VideoDisplay(p_frame, 320, 240)
            self.video_displays[user_id] = display
            
            username = 'Unknown'
            if self.server:
                user = self.server.user_manager.get_user(user_id)
                if user:
                    username = user.username

            tk.Label(p_frame, text=username, bg="#424242", fg="white", anchor="sw", padx=8, pady=4).pack(side="bottom", fill="x")
            self.update_video_grid()
        
        self.video_displays[user_id].update_frame(frame_data)

    def open_settings_window(self):
        """Opens a new window for host meeting settings."""
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Meeting Settings")
        self.settings_window.geometry("350x300")
        self.settings_window.configure(bg="#2B2B2B")
        self.settings_window.resizable(False, False)

        title_font = font.Font(family="Helvetica", size=12, weight="bold")
        check_font = font.Font(family="Helvetica", size=10)
        
        settings_frame = tk.Frame(self.settings_window, bg="#2B2B2B", padx=20, pady=20)
        settings_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(settings_frame, text="Host Controls", font=title_font, bg="#2B2B2B", fg="white").pack(anchor='w', pady=(0, 10))

        check_style = {"bg": "#2B2B2B", "fg": "white", "selectcolor": "#212121", "activebackground": "#2B2B2B", "activeforeground": "white", "font": check_font}
        
        tk.Checkbutton(settings_frame, text="Mute All Participants", variable=self.mute_all_var, command=self.toggle_mute_all, **check_style).pack(anchor='w')
        tk.Checkbutton(settings_frame, text="Disable Video for All", variable=self.disable_video_all_var, command=self.toggle_disable_video_all, **check_style).pack(anchor='w')
        tk.Checkbutton(settings_frame, text="Enable meeting chat", variable=self.chat_enabled_var, command=self.toggle_chat, **check_style).pack(anchor='w')
        tk.Checkbutton(settings_frame, text="Enable File Sharing", variable=self.file_sharing_enabled_var, command=self.toggle_file_sharing, **check_style).pack(anchor='w')
        tk.Checkbutton(settings_frame, text="Start Recording", variable=self.recording_var, command=self.toggle_recording, **check_style).pack(anchor='w', pady=(0, 15))

        tk.Button(settings_frame, text="Close", bg="#424242", fg="white", command=self.settings_window.destroy).pack(side=tk.RIGHT)

    def open_participants_window(self):
        """Opens a window to show the participant list."""
        if self.participants_window and self.participants_window.winfo_exists():
            self.participants_window.lift()
            return

        self.participants_window = tk.Toplevel(self.root)
        self.participants_window.title("Participants")
        self.participants_window.geometry("400x500")
        self.participants_window.configure(bg="#2B2B2B")
        
        # Participants list
        self.participants_tree = ttk.Treeview(self.participants_window, 
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
        
        self.participants_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Action buttons
        action_frame = tk.Frame(self.participants_window, bg="#2B2B2B")
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(action_frame, text="Mute Selected", command=self.mute_selected_participant, bg="#424242", fg="white").pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(action_frame, text="Kick Selected", command=self.kick_selected_participant, bg="#E53935", fg="white").pack(side=tk.LEFT, padx=(0, 5))

    def open_chat_window(self):
        """Opens a window for chat."""
        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_window.lift()
            return

        self.chat_window = tk.Toplevel(self.root)
        self.chat_window.title("Meeting Chat")
        self.chat_window.geometry("400x500")
        self.chat_window.configure(bg="#2B2B2B")
        
        # Chat messages display
        self.chat_display = scrolledtext.ScrolledText(self.chat_window, height=20, state='disabled', bg="#212121", fg="white")
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Chat input
        input_frame = tk.Frame(self.chat_window, bg="#2B2B2B")
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        chat_entry = tk.Entry(input_frame, bg="#424242", fg="white", insertbackground="white")
        chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        tk.Button(input_frame, text="Send", bg="#424242", fg="white").pack(side=tk.RIGHT)

    def open_stats_window(self):
        """Opens a window for server statistics."""
        if self.stats_window and self.stats_window.winfo_exists():
            self.stats_window.lift()
            return

        self.stats_window = tk.Toplevel(self.root)
        self.stats_window.title("Server Statistics")
        self.stats_window.geometry("500x600")
        self.stats_window.configure(bg="#2B2B2B")
        
        # Statistics display
        self.stats_text = scrolledtext.ScrolledText(self.stats_window, height=20, state='disabled', bg="#212121", fg="white")
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Refresh button
        tk.Button(self.stats_window, text="Refresh Statistics", command=self.refresh_statistics, bg="#424242", fg="white").pack(pady=5)
    
    def start_server(self):
        """Start the host server"""
        try:
            # Create and start server
            self.server = HostServer("0.0.0.0", self.server_port, self.host_username)
            
            # Start server in separate thread
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            self.is_server_running = True
            self.root.title(f"LAN Video Call - Host ({self.host_username}) - Running on port {self.server_port}")

            # Automatically connect host as a client
            self.connect_host_client()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
            logger.error(f"Failed to start server: {e}")
            self.root.destroy()
    
    def stop_server(self):
        """Stop the host server"""
        try:
            # Disconnect host client first
            if self.client and self.is_client_connected:
                self.client.disconnect()

            if self.server and self.is_server_running:
                self.server.stop()
                self.server = None
            
            self.is_server_running = False

            # Reset client state
            self.client = None
            self.is_client_connected = False
            self.clear_video_displays()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")
            logger.error(f"Failed to stop server: {e}")

    def connect_host_client(self):
        """Connect the host as a client to its own server."""
        if not MEDIA_LIBS_AVAILABLE:
            messagebox.showwarning("Warning", "Media libraries (OpenCV, Pillow) not found. Host video participation will be disabled.")
            return

        try:
            host = "127.0.0.1"
            port = self.server_port

            self.client = LANVideoClient()
            self.client.set_callback('on_connect', lambda d: logger.info("Host client connected."))
            self.client.set_callback('on_error', lambda e: logger.error(f"Host client error: {e}"))
            self.client.set_callback('on_frame_received', self.on_video_frame_received)
            self.client.set_callback('on_local_frame', self.on_local_frame)

            if self.client.connect(host, port, self.host_username):
                self.is_client_connected = True
                logger.info(f"Host '{self.host_username}' successfully connected as a participant.")
            else:
                messagebox.showerror("Host Client Error", "Could not connect as a participant.")

        except Exception as e:
            messagebox.showerror("Host Client Error", f"Failed to connect as participant: {e}")
            logger.error(f"Host client connection failed: {e}")

    def toggle_video(self):
        if not self.client or not self.is_client_connected: return
        if self.is_video_on:
            if self.client.stop_video():
                self.is_video_on = False
                self.video_button.config(text="📹 Start Video")
        else:
            if self.client.start_video():
                self.is_video_on = True
                self.video_button.config(text="📹 Stop Video")
            else:
                error_msg = """Could not start camera. This is usually a permission issue on Linux.

Troubleshooting steps:
1. Run: python fix_camera_permissions.py
2. Or manually: sudo usermod -a -G video $USER
3. Log out and log back in
4. Check if another app is using the camera
5. Try: ls -la /dev/video*

For more help, see the troubleshooting guide."""
                messagebox.showerror("Camera Error", error_msg)

    def toggle_audio(self):
        if not self.client or not self.is_client_connected: return
        if self.is_audio_on:
            if self.client.stop_audio():
                self.is_audio_on = False
                self.audio_button.config(text="🎤 Unmute")
        else:
            if self.client.start_audio():
                self.is_audio_on = True
                self.audio_button.config(text="🎤 Mute")

    
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
    
    def toggle_disable_video_all(self):
        """Toggle disable video for all participants"""
        if self.server and self.is_server_running:
            self.server.disable_video_all_participants(self.disable_video_all_var.get())
    
    def toggle_recording(self):
        """Toggle recording"""
        if self.server and self.is_server_running:
            if self.recording_var.get():
                self.server.start_recording()
            else:
                self.server.stop_recording()
    
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
    
    def refresh_participants(self):
        """Refresh participants list"""
        if not self.server or not self.is_server_running or not (self.participants_window and self.participants_window.winfo_exists()):
            return
        
        try:
            # Clear existing items
            for item in self.participants_tree.get_children():
                self.participants_tree.delete(item)
            
            # Get participants from server
            stats = self.server.get_meeting_stats()
            users = stats.get('user_stats', {}).get('users', {})
            
            # Add participants
            for user_id, user_info in users.items():
                username = user_info.get('username', 'Unknown')
                if user_id == self.server.host_id:
                    username += " (Host)"
                self.participants_tree.insert('', 'end', values=(
                    username,
                    user_id,
                    user_info.get('room_id', 'N/A'),
                    time.strftime('%H:%M:%S', time.localtime(user_info.get('last_seen', 0))),
                    'Online' if user_info.get('is_online', False) else 'Offline'
                ))
            
        except Exception as e:
            logger.error(f"Error refreshing participants: {e}")
    
    def update_video_grid(self):
        """Rearranges the participant videos in a grid."""
        all_frames = [self.local_video_display.parent] + [d.parent for d in self.video_displays.values()]
        
        for widget in self.video_grid_frame.winfo_children():
            widget.grid_forget()

        total_participants = len(all_frames)
        if total_participants == 0:
            return

        import math
        cols = math.ceil(math.sqrt(total_participants))
        rows = math.ceil(total_participants / cols)

        for i in range(cols): self.video_grid_frame.grid_columnconfigure(i, weight=1)
        for i in range(rows): self.video_grid_frame.grid_rowconfigure(i, weight=1)

        for index, p_frame in enumerate(all_frames):
            row = index // cols
            col = index % cols
            p_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

    def clear_video_displays(self):
        """Clear all video displays."""
        for display in self.video_displays.values():
            display.parent.destroy()
        self.video_displays.clear()

        if self.local_video_display:
            # Create a blank frame
            self.local_video_display.update_frame(np.zeros((240, 320, 3), dtype=np.uint8))
        self.update_video_grid()

    def mute_selected_participant(self):
        """Mute selected participant"""
        selection = self.participant_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a participant")
            return
        
        # Implementation for muting individual participants
        messagebox.showinfo("Info", "Individual participant muting is handled by the server logic, not yet implemented as a direct GUI action.")
    
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
        if not self.server or not self.is_server_running or not (self.stats_window and self.stats_window.winfo_exists()):
            return
        
        try:
            stats = self.server.get_meeting_stats()
            
            # Format statistics
            stats_text = f"""Server Statistics
================

Server Information:
- Host: {stats.get('host', 'Unknown')}
- Port: {self.server_port}
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
- Storage Used: {stats.get('file_stats', {}).get('total_storage_used_formatted', '0 B')}

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
- Host Username: {self.host_username}
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
                    # Update participants if server is running
                    if self.is_server_running:
                        self.root.after(0, self.refresh_participants)
                        self.root.after(0, self.update_video_grid)
                    
                    time.sleep(5)  # Update every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Error in update thread: {e}")
                    time.sleep(5)
        
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()

    def on_closing(self):
        """Handle window closing."""
        if messagebox.askokcancel("Quit", "Do you want to stop the server and quit?"):
            self.stop_server()
            self.root.destroy()

    def run(self):
        """Run the GUI"""
        self.root.mainloop()


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
