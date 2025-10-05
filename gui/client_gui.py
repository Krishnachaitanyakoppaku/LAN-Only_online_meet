"""
Client GUI for the LAN Video Calling Application
Provides a modern interface for video calling, chat, and file sharing
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, font
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
        
        self.parent.configure(bg="black")
        self.canvas = tk.Canvas(self.parent, width=width, height=height, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.last_frame = None
        self.canvas.bind('<Configure>', self._on_resize)
        
        # Video frame
        self.current_frame = None
        self.photo = None
        self.placeholder_text = None
        self.placeholder_bg = "#37474F"
    
    def update_frame(self, frame):
        """Update video frame"""
        try:
            if frame is None or not CV2_AVAILABLE or not PIL_AVAILABLE:
                return
            
            self.last_frame = frame
            self._render_current()
            
        except Exception as e:
            logger.error(f"Error updating video frame: {e}")

    def show_placeholder(self, initial: str):
        """Show a placeholder tile with the user's initial when video is off."""
        try:
            self.canvas.delete("all")
            self.canvas.configure(bg=self.placeholder_bg)
            # Background rectangle
            self.canvas.create_rectangle(0, 0, self.width, self.height, fill=self.placeholder_bg, outline=self.placeholder_bg)
            # Draw initial
            initial = (initial or "?").strip()[:1].upper()
            # Dynamic font size based on tile size
            size = max(24, int(min(self.width, self.height) * 0.5))
            font_id = ("Helvetica", size, "bold")
            self.canvas.create_text(self.width//2, self.height//2, text=initial, fill="white", font=font_id)
        except Exception as e:
            logger.error(f"Error showing placeholder: {e}")

    def _on_resize(self, event):
        self.width = max(1, event.width)
        self.height = max(1, event.height)
        self._render_current()

    def _render_current(self):
        try:
            if self.last_frame is None or not CV2_AVAILABLE or not PIL_AVAILABLE:
                return
            # Fit image to current canvas size
            frame_resized = cv2.resize(self.last_frame, (self.width, self.height))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame_rgb)
            self.photo = ImageTk.PhotoImage(image)
            self.canvas.delete("all")
            self.canvas.create_image(self.width//2, self.height//2, image=self.photo)
        except Exception as e:
            logger.error(f"Error rendering current frame: {e}")


class ClientGUI:
    """Client GUI for video calling"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAN Video Call")
        self.root.geometry("1200x800")
        self.root.configure(bg="#212121")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Client instance
        self.client: LANVideoClient = None
        self.is_connected = False
        self.is_host = False
        
        # Media state
        self.is_video_on = False
        self.is_audio_on = False
        self.is_screen_sharing = False
        
        # GUI variables
        self.server_host_var = tk.StringVar(value="127.0.0.1")
        self.server_port_var = tk.StringVar(value="8888")
        self.username_var = tk.StringVar(value="")
        self.login_frame = None
        self.chat_message_var = tk.StringVar(value="")
        
        # Video displays
        self.video_displays: Dict[str, VideoDisplay] = {}
        self.local_video_display: Optional[VideoDisplay] = None
        self.user_last_video_ts: Dict[str, float] = {}
        self.page_index = 0
        self.tiles_per_page = 6
        self.screen_share_active = False
        self.screen_share_user_id: Optional[str] = None
        self.screen_share_display: Optional[VideoDisplay] = None
        
        # Chat history
        self.chat_history = []
        
        # Create GUI
        self.show_login_screen()

    def show_login_screen(self):
        if self.login_frame:
            self.login_frame.destroy()

        self.login_frame = tk.Frame(self.root, bg="#2B2B2B")
        self.login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        title_font = font.Font(family="Helvetica", size=16, weight="bold")
        label_font = font.Font(family="Helvetica", size=10)
        
        tk.Label(self.login_frame, text="Join a Meeting", font=title_font, bg="#2B2B2B", fg="white").pack(pady=20)

        entry_style = {"bg": "#424242", "fg": "white", "insertbackground": "white", "bd": 1, "relief": "solid"}
        
        tk.Label(self.login_frame, text="Server IP", font=label_font, bg="#2B2B2B", fg="white").pack(padx=20, anchor='w')
        server_entry = tk.Entry(self.login_frame, textvariable=self.server_host_var, font=label_font, **entry_style)
        server_entry.pack(padx=20, pady=5, fill='x')

        tk.Label(self.login_frame, text="Port", font=label_font, bg="#2B2B2B", fg="white").pack(padx=20, anchor='w')
        port_entry = tk.Entry(self.login_frame, textvariable=self.server_port_var, font=label_font, **entry_style)
        port_entry.pack(padx=20, pady=5, fill='x')

        tk.Label(self.login_frame, text="Username", font=label_font, bg="#2B2B2B", fg="white").pack(padx=20, anchor='w')
        username_entry = tk.Entry(self.login_frame, textvariable=self.username_var, font=label_font, **entry_style)
        username_entry.pack(padx=20, pady=5, fill='x')
        username_entry.bind('<Return>', lambda e: self.connect_to_server())

        self.connect_button = tk.Button(self.login_frame, text="Join", command=self.connect_to_server, bg="#007BFF", fg="white", font=label_font)
        self.connect_button.pack(pady=20, padx=20, fill='x')

    def show_meeting_ui(self):
        if self.login_frame:
            self.login_frame.destroy()
            self.login_frame = None

        # --- Main container (screen share on top, videos below) ---
        self.video_container = tk.Frame(self.root, bg="#212121")
        self.video_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Screen share area (hidden by default)
        self.screen_share_frame = tk.Frame(self.video_container, bg="#111111")
        self.screen_share_frame.pack(fill=tk.X, side=tk.TOP)
        self.screen_share_frame.pack_forget()

        # --- Bottom control bar ---
        self.control_bar = tk.Frame(self.root, bg="#2B2B2B", height=70)
        self.control_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.control_bar.pack_propagate(False)

        self.setup_controls()
        self.setup_video_grid()

    def setup_controls(self):
        control_font = font.Font(family="Helvetica", size=10)
        button_style = {
            "bg": "#2B2B2B", "fg": "#FFFFFF", "activebackground": "#404040",
            "activeforeground": "#FFFFFF", "bd": 0, "font": control_font,
            "padx": 10, "pady": 5
        }

        left_frame = tk.Frame(self.control_bar, bg=self.control_bar.cget('bg'))
        left_frame.pack(side=tk.LEFT, padx=10)
        self.audio_button = tk.Button(left_frame, text="🎤 Unmute", **button_style, command=self.toggle_audio)
        self.audio_button.pack(side=tk.LEFT, padx=5)
        self.video_button = tk.Button(left_frame, text="📹 Start Video", **button_style, command=self.toggle_video)
        self.video_button.pack(side=tk.LEFT, padx=5)

        center_frame = tk.Frame(self.control_bar, bg=self.control_bar.cget('bg'))
        center_frame.pack(side=tk.LEFT, expand=True, padx=20)
        self.screen_share_button = tk.Button(center_frame, text="🔼 Share Screen", **button_style, command=self.toggle_screen_share)
        self.screen_share_button.pack(side=tk.LEFT, padx=5)
        tk.Button(center_frame, text="💬 Chat", **button_style).pack(side=tk.LEFT, padx=5) # Placeholder
        # Pagination controls
        self.prev_page_btn = tk.Button(center_frame, text="◀ Prev", **button_style, command=self.prev_page)
        self.prev_page_btn.pack(side=tk.LEFT, padx=5)
        self.page_label = tk.Label(center_frame, text="Page 1", bg=self.control_bar.cget('bg'), fg="#BBBBBB", font=control_font)
        self.page_label.pack(side=tk.LEFT, padx=5)
        self.next_page_btn = tk.Button(center_frame, text="Next ▶", **button_style, command=self.next_page)
        self.next_page_btn.pack(side=tk.LEFT, padx=5)

        right_frame = tk.Frame(self.control_bar, bg=self.control_bar.cget('bg'))
        right_frame.pack(side=tk.RIGHT, padx=10)
        leave_btn = tk.Button(right_frame, text="Leave", bg="#E53935", fg="white", activebackground="#C62828", bd=0, font=control_font, padx=20, pady=5, command=self.disconnect_from_server)
        leave_btn.pack(side=tk.RIGHT, padx=10)

    def setup_video_grid(self):
        self.video_grid_frame = tk.Frame(self.video_container, bg="#212121")
        self.video_grid_frame.pack(fill=tk.BOTH, expand=True)

        local_frame = tk.Frame(self.video_grid_frame, bg="black", borderwidth=1, relief="solid")
        self.local_video_display = VideoDisplay(local_frame, 320, 240)
        tk.Label(local_frame, text="You", bg="#424242", fg="white", anchor="sw", padx=8, pady=4).pack(side="bottom", fill="x")
        
        self.update_video_grid()
    
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
            self.client.set_callback('on_local_frame', self.on_local_frame)
            # Screen share callback from VideoClient
            self.client.video_client.set_display_callback('on_screen_share', self.on_screen_share)
            
            # Connect
            if self.client.connect(host, port, username):
                self.is_connected = True
                self.show_meeting_ui()
                self.root.title(f"LAN Video Call - {username}")
                logger.info(f"Connecting to {host}:{port}...")
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
            self.is_video_on = False
            self.is_audio_on = False
            self.is_screen_sharing = False

            # Destroy meeting UI and show login screen
            if self.video_container: self.video_container.destroy()
            if self.control_bar: self.control_bar.destroy()
            self.clear_video_displays()
            self.video_displays.clear()
            self.local_video_display = None

            self.show_login_screen()
            self.root.title("LAN Video Call")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to disconnect: {e}")
    
    def update_media_controls_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.video_button.config(state=state)
        self.audio_button.config(state=state)
        self.screen_share_button.config(state=state)
    
    def toggle_video(self):
        """Toggle video on/off"""
        try:
            if not self.client or not self.is_connected:
                return

            if self.is_video_on:
                if self.client.stop_video():
                    self.is_video_on = False
                    self.video_button.config(text="📹 Start Video")
            else:
                success = self.client.start_video()
                if success:
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
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle video: {e}")
    
    def toggle_audio(self):
        """Toggle audio on/off"""
        try:
            if not self.client or not self.is_connected:
                return

            if self.is_audio_on:
                if self.client.stop_audio():
                    self.is_audio_on = False
                    self.audio_button.config(text="🎤 Unmute")
            else:
                if self.client.start_audio():
                    self.is_audio_on = True
                    self.audio_button.config(text="🎤 Mute")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle audio: {e}")
    
    def toggle_screen_share(self):
        """Toggle screen sharing"""
        try:
            if not self.client or not self.is_connected:
                return

            if self.is_screen_sharing:
                if self.client.stop_screen_share():
                    self.is_screen_sharing = False
                    self.screen_share_button.config(text="🔼 Share Screen")
            else:
                if self.client.start_screen_share():
                    self.is_screen_sharing = True
                    self.screen_share_button.config(text="⏹ Stop Sharing")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle screen share: {e}")
    
    def upload_file(self):
        """Upload a file"""
        try:
            if self.client and self.is_connected:
                file_path = filedialog.askopenfilename()
                if file_path:
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
        # This is a placeholder as chat is now in a separate window in the host GUI
        # For client, we can log to console or implement a similar pop-up
        logger.info(f"Chat from {username}: {message}")
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
        """Clear all video displays."""
        for display in self.video_displays.values():
            display.parent.destroy()
        self.video_displays.clear()

        if self.local_video_display:
            self.local_video_display.update_frame(np.zeros((240, 320, 3), dtype=np.uint8))
        self.update_video_grid()

    def update_video_grid(self):
        """Rearranges participant videos with pagination and placeholders."""
        if not self.local_video_display:
            return

        # Build ordered list of user_ids to display
        participants = self.client.get_room_participants() if self.client else {}
        user_ids = list(participants.keys())

        # Ensure local user at front if logged in
        ordered = []
        if self.client and self.client.user_id:
            ordered.append(self.client.user_id)
        # Active speakers (excluding local if already in)
        speakers = self.client.get_active_speakers() if self.client else []
        for uid in speakers:
            if uid not in ordered:
                ordered.append(uid)
        # Add the rest
        for uid in user_ids:
            if uid not in ordered:
                ordered.append(uid)

        # Pagination
        total_tiles = len(ordered)
        total_pages = max(1, (total_tiles + self.tiles_per_page - 1) // self.tiles_per_page)
        self.page_index = max(0, min(self.page_index, total_pages - 1))
        start = self.page_index * self.tiles_per_page
        end = min(start + self.tiles_per_page, total_tiles)
        page_user_ids = ordered[start:end]

        # Clear grid
        for widget in self.video_grid_frame.winfo_children():
            widget.grid_forget()

        # Layout: choose rows/cols to best fit count up to 6
        count = len(page_user_ids)
        if count <= 1:
            cols, rows = 1, 1
        elif count == 2:
            cols, rows = 2, 1
        elif count == 3:
            cols, rows = 3, 1
        elif count == 4:
            cols, rows = 2, 2
        else:
            cols, rows = 3, 2
        for i in range(cols): self.video_grid_frame.grid_columnconfigure(i, weight=1)
        for i in range(rows): self.video_grid_frame.grid_rowconfigure(i, weight=1)

        # Ensure all frames exist and render placeholder if needed
        tiles = []
        for uid in page_user_ids:
            if uid == self.client.user_id:
                tiles.append((uid, self.local_video_display))
            else:
                if uid not in self.video_displays:
                    p_frame = tk.Frame(self.video_grid_frame, bg="black", borderwidth=1, relief="solid")
                    display = VideoDisplay(p_frame, 320, 240)
                    self.video_displays[uid] = display
                    username = participants.get(uid, {}).get('username', 'Unknown')
                    tk.Label(p_frame, text=username, bg="#424242", fg="white", anchor="sw", padx=8, pady=4).pack(side="bottom", fill="x")
                tiles.append((uid, self.video_displays[uid]))

        # Place tiles on grid
        for index, (uid, display) in enumerate(tiles):
            row = index // cols
            col = index % cols
            # Parent frame is either existing parent (for local) or display.parent
            parent_widget = display.parent if uid != self.client.user_id else display.parent
            parent_widget.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            # Placeholder logic: if no recent video, show initial
            last_ts = self.user_last_video_ts.get(uid)
            has_recent_video = last_ts is not None and (time.time() - last_ts) < 2.0
            if not has_recent_video:
                username = 'You' if uid == self.client.user_id else participants.get(uid, {}).get('username', 'User')
                initial = (username[:1] if username else '?')
                display.show_placeholder(initial)
            else:
                display._render_current()

        # Update page label and buttons
        self.page_label.config(text=f"Page {self.page_index + 1} / {total_pages}")
        self.prev_page_btn.config(state=("normal" if self.page_index > 0 else "disabled"))
        self.next_page_btn.config(state=("normal" if self.page_index < total_pages - 1 else "disabled"))
    
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
        logger.info(f"Successfully joined the meeting as {self.username_var.get()}.")
        room = data.get('room')
        self.is_host = bool(data.get('is_host'))
        # Show extra host-only controls if host
        if self.is_host:
            # Enable already-present controls; could add more in future
            pass
        if room:
            logger.info(f"Meeting Room: {room.get('room_name')}")
    
    def on_error(self, error):
        """Handle error"""
        messagebox.showerror("Server Error", error)
    
    def on_user_join(self, user):
        """Handle user join"""
        logger.info(f"User joined: {user['username']}")
        self.update_video_grid()
    
    def on_user_leave(self, user):
        """Handle user leave"""
        logger.info(f"User left: {user['username']}")
        user_id = user.get('user_id')
        if user_id in self.video_displays:
            self.video_displays[user_id].parent.destroy()
            del self.video_displays[user_id]
        self.update_video_grid()
    
    def on_chat_message(self, data):
        """Handle chat message"""
        logger.info(f"Chat from {data['username']}: {data['message']}")
    
    def on_video_frame_received(self, user_id, frame):
        """Handle video frame received"""
        try:
            if user_id not in self.video_displays:
                p_frame = tk.Frame(self.video_grid_frame, bg="black", borderwidth=1, relief="solid")
                display = VideoDisplay(p_frame, 320, 240)
                self.video_displays[user_id] = display
                
                user = self.client.get_room_participants().get(user_id, {})
                username = user.get('username', 'Unknown')
                tk.Label(p_frame, text=username, bg="#424242", fg="white", anchor="sw", padx=8, pady=4).pack(side="bottom", fill="x")
                self.update_video_grid()
            
            # Update display
            self.video_displays[user_id].update_frame(frame)
            self.user_last_video_ts[user_id] = time.time()
            # If user is on current page, keep tiles fresh
            self.update_video_grid()
            
        except Exception as e:
            logger.error(f"Error handling video frame: {e}")
    
    def on_local_frame(self, frame):
        """Handle local video frame for self-view."""
        if self.local_video_display:
            self.local_video_display.update_frame(frame)
            self.user_last_video_ts[self.client.user_id] = time.time()
            self.update_video_grid()

    def on_screen_share(self, user_id, frame):
        """Display screen share prominently above the grid."""
        try:
            self.screen_share_active = True
            self.screen_share_user_id = user_id
            # Create display if needed
            if not self.screen_share_display:
                self.screen_share_frame.pack(fill=tk.X, side=tk.TOP)
                display_frame = tk.Frame(self.screen_share_frame, bg="black", borderwidth=1, relief="solid")
                display_frame.pack(fill=tk.X, padx=5, pady=5)
                # Make it wider and a decent height
                self.screen_share_display = VideoDisplay(display_frame, width=960, height=540)
                tk.Label(display_frame, text="Screen Share", bg="#424242", fg="white", anchor="w", padx=8, pady=4).pack(side="bottom", fill="x")
            # Update frame
            self.screen_share_display.update_frame(frame)
        except Exception as e:
            logger.error(f"Error displaying screen share: {e}")

    def prev_page(self):
        if self.page_index > 0:
            self.page_index -= 1
            self.update_video_grid()

    def next_page(self):
        # Compute max pages
        participants = self.client.get_room_participants() if self.client else {}
        total_tiles = len(participants)
        total_pages = max(1, (total_tiles + self.tiles_per_page - 1) // self.tiles_per_page)
        if self.page_index < total_pages - 1:
            self.page_index += 1
            self.update_video_grid()
    
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
