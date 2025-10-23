#!/usr/bin/env python3
"""
Simple video test to verify camera and display functionality
"""

import cv2
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import queue

class VideoTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Video Test")
        self.root.geometry("500x400")
        self.root.configure(bg='#2d2d2d')
        
        # Video state
        self.video_enabled = False
        self.video_cap = None
        self.current_photo = None
        self.frame_queue = queue.Queue(maxsize=2)
        
        # Create GUI
        self.create_gui()
        
        # Start display update timer
        self.update_display_timer()
        
    def create_gui(self):
        # Video display
        self.video_label = tk.Label(self.root, 
                                   text="Click 'Start Video' to begin",
                                   font=('Arial', 14),
                                   fg='white', bg='#000000',
                                   width=50, height=20)
        self.video_label.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Control button
        self.video_btn = tk.Button(self.root, text="Start Video", 
                                  command=self.toggle_video,
                                  bg='#404040', fg='white', 
                                  font=('Arial', 12, 'bold'),
                                  padx=20, pady=10)
        self.video_btn.pack(pady=10)
        
    def toggle_video(self):
        if not self.video_enabled:
            self.start_video()
        else:
            self.stop_video()
            
    def start_video(self):
        try:
            print("Starting video capture...")
            self.video_cap = cv2.VideoCapture(0)
            if not self.video_cap.isOpened():
                print("ERROR: Cannot access camera")
                return
                
            self.video_enabled = True
            self.video_btn.config(text="Stop Video", bg='#51cf66')
            
            # Start video thread
            threading.Thread(target=self.video_loop, daemon=True).start()
            print("Video started successfully")
            
        except Exception as e:
            print(f"Error starting video: {e}")
            
    def stop_video(self):
        print("Stopping video...")
        self.video_enabled = False
        self.video_btn.config(text="Start Video", bg='#404040')
        
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
            
        # Clear display
        self.video_label.config(image="", text="Click 'Start Video' to begin")
        print("Video stopped")
        
    def video_loop(self):
        print("Video loop started")
        frame_count = 0
        while self.video_enabled and self.video_cap:
            try:
                ret, frame = self.video_cap.read()
                if not ret:
                    print("Failed to read frame")
                    break
                    
                frame_count += 1
                if frame_count % 30 == 0:  # Print every 30 frames
                    print(f"Frame {frame_count}: {frame.shape}")
                    
                # Resize and convert
                display_frame = cv2.resize(frame, (400, 300))
                display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                
                # Put frame in queue for display
                try:
                    self.frame_queue.put_nowait(display_frame_rgb)
                except queue.Full:
                    # Skip frame if queue is full
                    pass
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Video loop error: {e}")
                break
                
        print("Video loop ended")
        
    def update_display_timer(self):
        """Update display from queue in main thread"""
        try:
            # Get frame from queue
            frame_rgb = self.frame_queue.get_nowait()
            
            # Create photo
            pil_image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update display
            self.video_label.configure(image=photo, text="")
            self.video_label.image = photo  # Keep reference
            print("Display updated successfully")
            
        except queue.Empty:
            # No frame available
            pass
        except Exception as e:
            print(f"Display update error: {e}")
            import traceback
            traceback.print_exc()
        
        # Schedule next update
        if self.video_enabled:
            self.root.after(33, self.update_display_timer)  # ~30 FPS
        else:
            self.root.after(100, self.update_display_timer)  # Check less frequently when stopped
            
    def run(self):
        print("Starting video test application...")
        self.root.mainloop()

if __name__ == "__main__":
    app = VideoTest()
    app.run()