#!/usr/bin/env python3
"""
LAN Meeting Client Launcher - GUI Version
Simple graphical tool to join meetings by entering server IP
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import socket
import threading
import requests
import time

class MeetingJoiner:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎥 LAN Meeting - Join Meeting")
        self.root.geometry("500x400")
        self.root.configure(bg='#2d2d2d')
        self.root.resizable(False, False)
        
        # Center window
        self.center_window()
        
        self.setup_gui()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"500x400+{x}+{y}")
        
    def setup_gui(self):
        """Setup the GUI interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#2d2d2d', padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, 
                              text="🎥 LAN Meeting Client", 
                              font=('Segoe UI', 20, 'bold'),
                              fg='#0078d4', bg='#2d2d2d')
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(main_frame, 
                                 text="Join a meeting by entering the server IP address", 
                                 font=('Segoe UI', 11),
                                 fg='#cccccc', bg='#2d2d2d')
        subtitle_label.pack(pady=(0, 30))
        
        # Server IP input section
        ip_frame = tk.Frame(main_frame, bg='#2d2d2d')
        ip_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(ip_frame, 
                text="🌐 Server IP Address:", 
                font=('Segoe UI', 12, 'bold'),
                fg='white', bg='#2d2d2d').pack(anchor=tk.W, pady=(0, 8))
        
        self.ip_entry = tk.Entry(ip_frame, 
                                font=('Segoe UI', 14),
                                bg='#3d3d3d', fg='white',
                                relief='flat', borderwidth=0,
                                insertbackground='white')
        self.ip_entry.pack(fill=tk.X, ipady=12)
        self.ip_entry.insert(0, "192.168.1.")
        self.ip_entry.bind('<Return>', lambda e: self.test_connection())
        
        # Examples
        examples_label = tk.Label(ip_frame, 
                                 text="💡 Examples: 192.168.1.100, 10.0.0.5, 172.16.1.10", 
                                 font=('Segoe UI', 9),
                                 fg='#888888', bg='#2d2d2d')
        examples_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Status display
        self.status_frame = tk.Frame(main_frame, bg='#3d3d3d', relief='flat', bd=1)
        self.status_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.status_label = tk.Label(self.status_frame, 
                                    text="💡 Enter server IP address and click 'Test Connection'", 
                                    font=('Segoe UI', 10),
                                    fg='#cccccc', bg='#3d3d3d',
                                    wraplength=400)
        self.status_label.pack(pady=15)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#2d2d2d')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.test_btn = tk.Button(button_frame, 
                                 text="🔍 Test Connection",
                                 command=self.test_connection,
                                 bg='#6c757d', fg='white',
                                 font=('Segoe UI', 11, 'bold'),
                                 relief='flat', borderwidth=0,
                                 padx=20, pady=10,
                                 cursor='hand2')
        self.test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.join_btn = tk.Button(button_frame, 
                                 text="🚀 Join Meeting",
                                 command=self.join_meeting,
                                 bg='#0078d4', fg='white',
                                 font=('Segoe UI', 11, 'bold'),
                                 relief='flat', borderwidth=0,
                                 padx=20, pady=10,
                                 cursor='hand2',
                                 state=tk.DISABLED)
        self.join_btn.pack(side=tk.RIGHT)
        
        # Server info display (initially hidden)
        self.info_frame = tk.Frame(main_frame, bg='#2d2d2d')
        
        self.info_label = tk.Label(self.info_frame, 
                                  text="", 
                                  font=('Segoe UI', 10),
                                  fg='#28a745', bg='#2d2d2d',
                                  justify=tk.LEFT)
        self.info_label.pack(pady=(10, 0))
        
        # Footer
        footer_frame = tk.Frame(main_frame, bg='#2d2d2d')
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        tk.Label(footer_frame, 
                text="✅ Completely offline • 🔒 LAN only • 📱 Works on any device", 
                font=('Segoe UI', 9),
                fg='#888888', bg='#2d2d2d').pack()
        
        # Focus on IP entry
        self.ip_entry.focus()
        self.ip_entry.select_range(len("192.168.1."), tk.END)
        
    def validate_ip(self, ip):
        """Validate IP address format"""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False
            
    def test_connection(self):
        """Test connection to server"""
        server_input = self.ip_entry.get().strip()
        
        if not server_input:
            self.update_status("❌ Please enter a server IP address", "#dc3545")
            return
            
        # Parse IP and port
        server_ip = server_input
        port = 5000
        
        if ':' in server_input:
            try:
                server_ip, port_str = server_input.split(':')
                port = int(port_str)
            except ValueError:
                self.update_status("❌ Invalid format. Use: IP:PORT or just IP", "#dc3545")
                return
        
        if not self.validate_ip(server_ip):
            self.update_status("❌ Invalid IP address format", "#dc3545")
            return
            
        # Disable button and show testing status
        self.test_btn.config(state=tk.DISABLED, text="🔍 Testing...")
        self.update_status("🔍 Testing connection...", "#ffd43b")
        
        # Test in background thread
        threading.Thread(target=self._test_connection_thread, 
                        args=(server_ip, port), daemon=True).start()
        
    def _test_connection_thread(self, server_ip, port):
        """Test connection in background thread"""
        try:
            # Test HTTP connection first
            response = requests.get(f"http://{server_ip}:{port}/api/status", timeout=5)
            if response.status_code == 200:
                server_info = response.json()
                self.root.after(0, self._connection_success, server_ip, port, server_info)
            else:
                self.root.after(0, self._connection_failed, server_ip, port, "Server not responding")
        except requests.exceptions.RequestException:
            # Fallback: test socket connection
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((server_ip, port))
                sock.close()
                
                if result == 0:
                    self.root.after(0, self._connection_success, server_ip, port, None)
                else:
                    self.root.after(0, self._connection_failed, server_ip, port, "Connection refused")
            except Exception as e:
                self.root.after(0, self._connection_failed, server_ip, port, str(e))
                
    def _connection_success(self, server_ip, port, server_info):
        """Handle successful connection"""
        self.test_btn.config(state=tk.NORMAL, text="🔍 Test Connection")
        self.join_btn.config(state=tk.NORMAL)
        
        status_text = f"✅ Connected to {server_ip}:{port}"
        self.update_status(status_text, "#28a745")
        
        # Show server info if available
        if server_info:
            info_text = f"📊 Meeting Status:\n"
            info_text += f"👥 Participants: {server_info.get('participants', 0)}\n"
            info_text += f"📹 Host Video: {'On' if server_info.get('host_video') else 'Off'}\n"
            info_text += f"🖥️ Screen Sharing: {'Active' if server_info.get('host_screen_sharing') else 'Inactive'}"
            
            self.info_label.config(text=info_text)
            self.info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.server_ip = server_ip
        self.server_port = port
        
    def _connection_failed(self, server_ip, port, error):
        """Handle failed connection"""
        self.test_btn.config(state=tk.NORMAL, text="🔍 Test Connection")
        self.join_btn.config(state=tk.DISABLED)
        
        status_text = f"❌ Cannot connect to {server_ip}:{port}\n"
        status_text += f"Error: {error}\n\n"
        status_text += "🔧 Troubleshooting:\n"
        status_text += "• Make sure the server is running\n"
        status_text += "• Check if you're on the same network\n"
        status_text += "• Verify the IP address is correct"
        
        self.update_status(status_text, "#dc3545")
        self.info_frame.pack_forget()
        
    def update_status(self, text, color):
        """Update status display"""
        self.status_label.config(text=text, fg=color)
        
    def join_meeting(self):
        """Join the meeting"""
        if not hasattr(self, 'server_ip'):
            messagebox.showerror("Error", "Please test connection first")
            return
            
        meeting_url = f"http://{self.server_ip}:{self.server_port}/client"
        
        try:
            webbrowser.open(meeting_url)
            
            # Show success message
            result = messagebox.showinfo("Meeting Opened", 
                                       f"Meeting opened in browser!\n\n"
                                       f"URL: {meeting_url}\n\n"
                                       f"Next Steps:\n"
                                       f"1. Enter your name\n"
                                       f"2. Choose camera/microphone settings\n"
                                       f"3. Click 'Join Meeting'\n"
                                       f"4. Enjoy your meeting! 🎉\n\n"
                                       f"Close this window?")
            
            if result:
                self.root.quit()
                
        except Exception as e:
            messagebox.showerror("Browser Error", 
                               f"Could not open browser automatically.\n\n"
                               f"Please open your browser manually and go to:\n"
                               f"{meeting_url}\n\n"
                               f"Error: {str(e)}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    """Main function"""
    try:
        app = MeetingJoiner()
        app.run()
    except KeyboardInterrupt:
        print("Application closed by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()