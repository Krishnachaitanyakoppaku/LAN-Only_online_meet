"""
Client GUI for the LAN Video Calling Application
Provides a modern interface for video calling, chat, and file sharing
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available. Video functionality will be limited.")

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available. Image functionality will be limited.")
import threading
import time
from typing import Dict, Any, Optional
from client.main_client import LANVideoClient
from shared.utils import logger, get_local_ip


class VideoDisplay:
    """Video display widget"""
    
    def __init__(self, parent, width=320, height=240):
        self.parent = parent
        self.width = width
        self.height = height
        
        # Create canvas
        self.canvas = tk.Canvas(parent, width=width, height=height, bg="black")
        self.canvas.pack()
        
        # Video frame
        self.current_frame = None
        self.photo = None
    
    def update_frame(self, frame):
        """Update video frame"""
        try:
            if frame is None or not CV2_AVAILABLE or not PIL_AVAILABLE:
                return
            
            # Resize frame to fit display
            frame_resized = cv2.resize(frame, (self.width, self.height))
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            image = Image.fromarray(frame_rgb)
            self.photo = ImageTk.PhotoImage(image)
            
            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_image(self.width//2, self.height//2, image=self.photo)
            
        except Exception as e:
            logger.error(f"Error updating video frame: {e}")


class ClientGUI:
    """Client GUI for video calling"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAN Video Calling Client")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Client instance
        self.client: LANVideoClient = None
        self.is_connected = False
        
        # GUI variables
        self.server_host_var = tk.StringVar(value="127.0.0.1")
        self.server_port_var = tk.StringVar(value="8888")
        self.username_var = tk.StringVar(value="")
        self.room_name_var = tk.StringVar(value="")
        self.chat_message_var = tk.StringVar(value="")
        
        # Video displays
        self.video_displays: Dict[str, VideoDisplay] = {}
        self.local_video_display: Optional[VideoDisplay] = None
        
        # Chat history
        self.chat_history = []
        
        # Create GUI
        self.create_widgets()
        
        # Update thread
        self.update_thread = threading.Thread(target=self.update_display, daemon=True)
        self.update_thread.start()
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Connection frame
        self.create_connection_frame(main_frame)
        
        # Main content frame
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left panel (video and controls)
        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right panel (chat and participants)
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Create panels
        self.create_video_panel(left_panel)
        self.create_controls_panel(left_panel)
        self.create_chat_panel(right_panel)
        self.create_participants_panel(right_panel)
    
    def create_connection_frame(self, parent):
        """Create connection frame"""
        conn_frame = ttk.LabelFrame(parent, text="Connection", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Server settings
        ttk.Label(conn_frame, text="Server:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        server_entry = ttk.Entry(conn_frame, textvariable=self.server_host_var, width=15)
        server_entry.grid(row=0, column=1, padx=(0, 5))
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        port_entry = ttk.Entry(conn_frame, textvariable=self.server_port_var, width=8)
        port_entry.grid(row=0, column=3, padx=(0, 10))
        
        ttk.Label(conn_frame, text="Username:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        username_entry = ttk.Entry(conn_frame, textvariable=self.username_var, width=15)
        username_entry.grid(row=0, column=5, padx=(0, 10))
        
        # Connection buttons
        self.connect_button = ttk.Button(conn_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.grid(row=0, column=6, padx=(0, 5))
        
        self.disconnect_button = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_from_server, state="disabled")
        self.disconnect_button.grid(row=0, column=7)
        
        # Room settings
        ttk.Label(conn_frame, text="Room Name:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        room_entry = ttk.Entry(conn_frame, textvariable=self.room_name_var, width=15)
        room_entry.grid(row=1, column=1, padx=(0, 5), pady=(5, 0))
        
        self.create_room_button = ttk.Button(conn_frame, text="Create Room", command=self.create_room, state="disabled")
        self.create_room_button.grid(row=1, column=2, padx=(0, 5), pady=(5, 0))
        
        self.join_room_button = ttk.Button(conn_frame, text="Join Room", command=self.join_room, state="disabled")
        self.join_room_button.grid(row=1, column=3, padx=(0, 5), pady=(5, 0))
        
        self.leave_room_button = ttk.Button(conn_frame, text="Leave Room", command=self.leave_room, state="disabled")
        self.leave_room_button.grid(row=1, column=4, pady=(5, 0))
    
    def create_video_panel(self, parent):
        """Create video panel"""
        video_frame = ttk.LabelFrame(parent, text="Video", padding="10")
        video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Video grid frame
        self.video_grid_frame = ttk.Frame(video_frame)
        self.video_grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create local video display
        self.local_video_display = VideoDisplay(self.video_grid_frame, 320, 240)
        self.local_video_display.canvas.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add label for local video
        local_label = ttk.Label(self.video_grid_frame, text="You")
        local_label.pack(side=tk.LEFT, padx=(0, 5))
    
    def create_controls_panel(self, parent):
        """Create controls panel"""
        controls_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        controls_frame.pack(fill=tk.X)
        
        # Media controls
        media_frame = ttk.Frame(controls_frame)
        media_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.video_button = ttk.Button(media_frame, text="Start Video", command=self.toggle_video, state="disabled")
        self.video_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.audio_button = ttk.Button(media_frame, text="Start Audio", command=self.toggle_audio, state="disabled")
        self.audio_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.screen_share_button = ttk.Button(media_frame, text="Share Screen", command=self.toggle_screen_share, state="disabled")
        self.screen_share_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # File controls
        file_frame = ttk.Frame(controls_frame)
        file_frame.pack(fill=tk.X)
        
        ttk.Button(file_frame, text="Upload File", command=self.upload_file, state="disabled").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_frame, text="Download File", command=self.download_file, state="disabled").pack(side=tk.LEFT)
    
    def create_chat_panel(self, parent):
        """Create chat panel"""
        chat_frame = ttk.LabelFrame(parent, text="Chat", padding="10")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat history
        self.chat_text = scrolledtext.ScrolledText(chat_frame, height=15, state="disabled")
        self.chat_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat input
        chat_input_frame = ttk.Frame(chat_frame)
        chat_input_frame.pack(fill=tk.X)
        
        chat_entry = ttk.Entry(chat_input_frame, textvariable=self.chat_message_var)
        chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        chat_entry.bind('<Return>', lambda e: self.send_chat_message())
        
        ttk.Button(chat_input_frame, text="Send", command=self.send_chat_message, state="disabled").pack(side=tk.RIGHT)
    
    def create_participants_panel(self, parent):
        """Create participants panel"""
        participants_frame = ttk.LabelFrame(parent, text="Participants", padding="10")
        participants_frame.pack(fill=tk.X)
        
        # Participants list
        self.participants_tree = ttk.Treeview(participants_frame, columns=("status",), show="tree headings")
        self.participants_tree.heading("#0", text="Username")
        self.participants_tree.heading("status", text="Status")
        self.participants_tree.column("#0", width=120)
        self.participants_tree.column("status", width=80)
        self.participants_tree.pack(fill=tk.X)
    
    def connect_to_server(self):
        """Connect to server"""
        try:
            host = self.server_host_var.get().strip()
            port = int(self.server_port_var.get().strip())
            username = self.username_var.get().strip()
            
            if not host or not port or not username:
                messagebox.showerror("Error", "Please enter server host, port, and username")
                return
            
            # Create client
            self.client = LANVideoClient()
            
            # Set up callbacks
            self.client.set_callback('on_connect', self.on_connected)
            self.client.set_callback('on_error', self.on_error)
            self.client.set_callback('on_user_join', self.on_user_join)
            self.client.set_callback('on_user_leave', self.on_user_leave)
            self.client.set_callback('on_chat_message', self.on_chat_message)
            self.client.set_callback('on_frame_received', self.on_video_frame_received)
            
            # Connect
            if self.client.connect(host, port, username):
                self.is_connected = True
                self.connect_button.config(state="disabled")
                self.disconnect_button.config(state="normal")
                self.create_room_button.config(state="normal")
                self.join_room_button.config(state="normal")
                
                self.add_chat_message("System", f"Connecting to {host}:{port}...")
            else:
                messagebox.showerror("Error", "Failed to connect to server")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid port number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}")
    
    def disconnect_from_server(self):
        """Disconnect from server"""
        try:
            if self.client:
                self.client.disconnect()
                self.client = None
            
            self.is_connected = False
            self.connect_button.config(state="normal")
            self.disconnect_button.config(state="disabled")
            self.create_room_button.config(state="disabled")
            self.join_room_button.config(state="disabled")
            self.leave_room_button.config(state="disabled")
            
            # Disable media controls
            self.video_button.config(state="disabled")
            self.audio_button.config(state="disabled")
            self.screen_share_button.config(state="disabled")
            
            # Clear displays
            self.clear_video_displays()
            self.clear_participants()
            
            self.add_chat_message("System", "Disconnected from server")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to disconnect: {e}")
    
    def create_room(self):
        """Create a new room"""
        try:
            room_name = self.room_name_var.get().strip()
            if not room_name:
                messagebox.showerror("Error", "Please enter a room name")
                return
            
            if self.client.create_room(room_name):
                self.add_chat_message("System", f"Creating room '{room_name}'...")
            else:
                messagebox.showerror("Error", "Failed to create room")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create room: {e}")
    
    def join_room(self):
        """Join a room"""
        try:
            room_name = self.room_name_var.get().strip()
            if not room_name:
                messagebox.showerror("Error", "Please enter a room name")
                return
            
            # For now, we'll use room name as room ID (in real implementation, 
            # you'd have a room selection dialog)
            if self.client.join_room(room_name):
                self.add_chat_message("System", f"Joining room '{room_name}'...")
                self.leave_room_button.config(state="normal")
                self.video_button.config(state="normal")
                self.audio_button.config(state="normal")
                self.screen_share_button.config(state="normal")
            else:
                messagebox.showerror("Error", "Failed to join room")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to join room: {e}")
    
    def leave_room(self):
        """Leave current room"""
        try:
            if self.client.leave_room():
                self.add_chat_message("System", "Left room")
                self.leave_room_button.config(state="disabled")
                self.video_button.config(state="disabled")
                self.audio_button.config(state="disabled")
                self.screen_share_button.config(state="disabled")
                
                # Clear video displays
                self.clear_video_displays()
                self.clear_participants()
            else:
                messagebox.showerror("Error", "Failed to leave room")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to leave room: {e}")
    
    def toggle_video(self):
        """Toggle video on/off"""
        try:
            if self.client:
                # This would need to be implemented based on client state
                pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle video: {e}")
    
    def toggle_audio(self):
        """Toggle audio on/off"""
        try:
            if self.client:
                # This would need to be implemented based on client state
                pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle audio: {e}")
    
    def toggle_screen_share(self):
        """Toggle screen sharing"""
        try:
            if self.client:
                # This would need to be implemented based on client state
                pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle screen share: {e}")
    
    def upload_file(self):
        """Upload a file"""
        try:
            file_path = filedialog.askopenfilename()
            if file_path and self.client:
                self.client.upload_file(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload file: {e}")
    
    def download_file(self):
        """Download a file"""
        try:
            # This would need a file selection dialog
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download file: {e}")
    
    def send_chat_message(self):
        """Send chat message"""
        try:
            message = self.chat_message_var.get().strip()
            if message and self.client:
                if self.client.send_chat_message(message):
                    self.chat_message_var.set("")
                else:
                    messagebox.showerror("Error", "Failed to send message")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")
    
    def add_chat_message(self, username: str, message: str):
        """Add message to chat"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            chat_entry = f"[{timestamp}] {username}: {message}\n"
            
            self.chat_text.config(state="normal")
            self.chat_text.insert(tk.END, chat_entry)
            self.chat_text.see(tk.END)
            self.chat_text.config(state="disabled")
            
        except Exception as e:
            logger.error(f"Error adding chat message: {e}")
    
    def clear_video_displays(self):
        """Clear all video displays"""
        try:
            # Clear remote video displays
            for display in self.video_displays.values():
                display.canvas.destroy()
            self.video_displays.clear()
            
            # Clear local video display
            if self.local_video_display:
                self.local_video_display.canvas.delete("all")
                
        except Exception as e:
            logger.error(f"Error clearing video displays: {e}")
    
    def clear_participants(self):
        """Clear participants list"""
        try:
            for item in self.participants_tree.get_children():
                self.participants_tree.delete(item)
        except Exception as e:
            logger.error(f"Error clearing participants: {e}")
    
    # Callback methods
    def on_connected(self, data):
        """Handle connection success"""
        self.add_chat_message("System", f"Connected as {data.get('user_id', 'Unknown')}")
    
    def on_error(self, error):
        """Handle error"""
        self.add_chat_message("Error", error)
    
    def on_user_join(self, user):
        """Handle user join"""
        self.add_chat_message("System", f"{user['username']} joined")
        self.update_participants()
    
    def on_user_leave(self, user):
        """Handle user leave"""
        self.add_chat_message("System", f"{user['username']} left")
        self.update_participants()
    
    def on_chat_message(self, data):
        """Handle chat message"""
        self.add_chat_message(data['username'], data['message'])
    
    def on_video_frame_received(self, user_id, frame):
        """Handle video frame received"""
        try:
            if user_id not in self.video_displays:
                # Create new video display
                display_frame = ttk.Frame(self.video_grid_frame)
                display_frame.pack(side=tk.LEFT, padx=(0, 5))
                
                display = VideoDisplay(display_frame, 320, 240)
                self.video_displays[user_id] = display
                
                # Add label
                user = self.client.get_room_participants().get(user_id, {})
                username = user.get('username', 'Unknown')
                label = ttk.Label(display_frame, text=username)
                label.pack()
            
            # Update display
            self.video_displays[user_id].update_frame(frame)
            
        except Exception as e:
            logger.error(f"Error handling video frame: {e}")
    
    def update_participants(self):
        """Update participants list"""
        try:
            # Clear existing items
            for item in self.participants_tree.get_children():
                self.participants_tree.delete(item)
            
            # Add participants
            if self.client:
                participants = self.client.get_room_participants()
                for user_id, user in participants.items():
                    status = "Online"
                    if user.get('is_muted'):
                        status += " (Muted)"
                    if user.get('is_video_enabled'):
                        status += " (Video)"
                    if user.get('is_audio_enabled'):
                        status += " (Audio)"
                    
                    self.participants_tree.insert("", "end", text=user['username'], values=(status,))
                    
        except Exception as e:
            logger.error(f"Error updating participants: {e}")
    
    def update_display(self):
        """Update display (runs in background thread)"""
        while True:
            try:
                # Update local video display if camera is running
                if self.client and self.client.video_client and self.client.video_client.is_camera_running:
                    # This would need to be implemented to get local camera frame
                    pass
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                logger.error(f"Error in update display: {e}")
                time.sleep(1)
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_connected:
            if messagebox.askokcancel("Quit", "You are connected to a server. Do you want to disconnect and quit?"):
                self.disconnect_from_server()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()


def main():
    """Main function"""
    try:
        app = ClientGUI()
        app.run()
    except Exception as e:
        logger.error(f"Error running client GUI: {e}")
        messagebox.showerror("Error", f"Failed to start client GUI: {e}")


if __name__ == "__main__":
    main()
