#!/usr/bin/env python3
"""
LAN Communication System Launcher
Simple GUI to launch server or client applications
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import threading

class SystemLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAN Communication System Launcher")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Process tracking
        self.server_process = None
        self.client_processes = []
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup launcher GUI"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="LAN Communication System", 
                               font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="Multi-User Communication for LAN", 
                                  font=("Arial", 10))
        subtitle_label.pack(pady=(0, 20))
        
        # Server section
        server_frame = ttk.LabelFrame(main_frame, text="Server")
        server_frame.pack(fill=tk.X, pady=(0, 15))
        
        server_inner = ttk.Frame(server_frame)
        server_inner.pack(fill=tk.X, padx=15, pady=15)
        
        ttk.Label(server_inner, text="Start the communication server (run this first)").pack(anchor=tk.W)
        
        server_buttons = ttk.Frame(server_inner)
        server_buttons.pack(fill=tk.X, pady=(10, 0))
        
        self.start_server_btn = ttk.Button(server_buttons, text="Start Server", 
                                          command=self.start_server)
        self.start_server_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_server_btn = ttk.Button(server_buttons, text="Stop Server", 
                                         command=self.stop_server, state=tk.DISABLED)
        self.stop_server_btn.pack(side=tk.LEFT)
        
        self.server_status = ttk.Label(server_inner, text="Server not running")
        self.server_status.pack(anchor=tk.W, pady=(5, 0))
        
        # Client section
        client_frame = ttk.LabelFrame(main_frame, text="Client")
        client_frame.pack(fill=tk.X, pady=(0, 15))
        
        client_inner = ttk.Frame(client_frame)
        client_inner.pack(fill=tk.X, padx=15, pady=15)
        
        ttk.Label(client_inner, text="Connect to a communication server").pack(anchor=tk.W)
        
        client_buttons = ttk.Frame(client_inner)
        client_buttons.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(client_buttons, text="Launch Client", 
                  command=self.launch_client).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(client_buttons, text="Launch Multiple Clients", 
                  command=self.launch_multiple_clients).pack(side=tk.LEFT)
        
        self.client_status = ttk.Label(client_inner, text=f"Active clients: {len(self.client_processes)}")
        self.client_status.pack(anchor=tk.W, pady=(5, 0))
        
        # Tools section
        tools_frame = ttk.LabelFrame(main_frame, text="System Tools")
        tools_frame.pack(fill=tk.X, pady=(0, 15))
        
        tools_inner = ttk.Frame(tools_frame)
        tools_inner.pack(fill=tk.X, padx=15, pady=15)
        
        tools_buttons = ttk.Frame(tools_inner)
        tools_buttons.pack(fill=tk.X)
        
        ttk.Button(tools_buttons, text="System Test", 
                  command=self.run_system_test).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(tools_buttons, text="Install Check", 
                  command=self.run_install_check).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(tools_buttons, text="Documentation", 
                  command=self.open_documentation).pack(side=tk.LEFT)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(control_frame, text="Stop All", 
                  command=self.stop_all).pack(side=tk.LEFT)
        
        ttk.Button(control_frame, text="Exit", 
                  command=self.exit_launcher).pack(side=tk.RIGHT)
        
        # Status update timer
        self.update_status()
        
    def start_server(self):
        """Start the communication server"""
        try:
            if not os.path.exists("server.py"):
                messagebox.showerror("Error", "server.py not found in current directory")
                return
                
            self.server_process = subprocess.Popen([sys.executable, "server.py"])
            
            self.start_server_btn.config(state=tk.DISABLED)
            self.stop_server_btn.config(state=tk.NORMAL)
            self.server_status.config(text="Server starting...")
            
            # Check if server started successfully
            self.root.after(2000, self.check_server_status)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
            
    def check_server_status(self):
        """Check if server is still running"""
        if self.server_process and self.server_process.poll() is None:
            self.server_status.config(text="Server running")
        else:
            self.server_status.config(text="Server failed to start")
            self.start_server_btn.config(state=tk.NORMAL)
            self.stop_server_btn.config(state=tk.DISABLED)
            self.server_process = None
            
    def stop_server(self):
        """Stop the communication server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            except:
                pass
                
            self.server_process = None
            
        self.start_server_btn.config(state=tk.NORMAL)
        self.stop_server_btn.config(state=tk.DISABLED)
        self.server_status.config(text="Server stopped")
        
    def launch_client(self):
        """Launch a single client"""
        try:
            if not os.path.exists("client.py"):
                messagebox.showerror("Error", "client.py not found in current directory")
                return
                
            client_process = subprocess.Popen([sys.executable, "client.py"])
            self.client_processes.append(client_process)
            
            self.update_client_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch client: {str(e)}")
            
    def launch_multiple_clients(self):
        """Launch multiple clients for testing"""
        try:
            count = tk.simpledialog.askinteger("Multiple Clients", 
                                             "How many clients to launch?", 
                                             minvalue=1, maxvalue=10, initialvalue=2)
            if count:
                for i in range(count):
                    self.launch_client()
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch clients: {str(e)}")
            
    def run_system_test(self):
        """Run system test utility"""
        try:
            if not os.path.exists("test_system.py"):
                messagebox.showerror("Error", "test_system.py not found")
                return
                
            subprocess.Popen([sys.executable, "test_system.py"])
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run system test: {str(e)}")
            
    def run_install_check(self):
        """Run installation check"""
        try:
            if not os.path.exists("install.py"):
                messagebox.showerror("Error", "install.py not found")
                return
                
            subprocess.Popen([sys.executable, "install.py"])
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run install check: {str(e)}")
            
    def open_documentation(self):
        """Open documentation"""
        try:
            import webbrowser
            
            if os.path.exists("README.md"):
                # Try to open with default markdown viewer
                if sys.platform.startswith('darwin'):  # macOS
                    subprocess.run(['open', 'README.md'])
                elif sys.platform.startswith('win'):  # Windows
                    os.startfile('README.md')
                else:  # Linux
                    subprocess.run(['xdg-open', 'README.md'])
            else:
                messagebox.showinfo("Documentation", 
                                  "README.md not found. Please check the project directory.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open documentation: {str(e)}")
            
    def update_client_status(self):
        """Update client status display"""
        # Remove finished processes
        self.client_processes = [p for p in self.client_processes if p.poll() is None]
        self.client_status.config(text=f"Active clients: {len(self.client_processes)}")
        
    def update_status(self):
        """Periodic status update"""
        self.update_client_status()
        
        # Check server status
        if self.server_process and self.server_process.poll() is not None:
            # Server has stopped
            if self.stop_server_btn['state'] == tk.NORMAL:
                self.stop_server()
                
        # Schedule next update
        self.root.after(2000, self.update_status)
        
    def stop_all(self):
        """Stop all running processes"""
        # Stop server
        if self.server_process:
            self.stop_server()
            
        # Stop all clients
        for client_process in self.client_processes:
            try:
                client_process.terminate()
            except:
                pass
                
        self.client_processes.clear()
        self.update_client_status()
        
        messagebox.showinfo("Stopped", "All processes have been stopped")
        
    def exit_launcher(self):
        """Exit the launcher"""
        if self.server_process or self.client_processes:
            result = messagebox.askyesno("Exit", 
                                       "There are running processes. Stop them and exit?")
            if result:
                self.stop_all()
            else:
                return
                
        self.root.destroy()
        
    def on_closing(self):
        """Handle window closing"""
        self.exit_launcher()
        
    def run(self):
        """Run the launcher"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    # Import tkinter.simpledialog for multiple clients feature
    import tkinter.simpledialog
    
    launcher = SystemLauncher()
    launcher.run()