#!/usr/bin/env python3
"""
Ultra-simple connection dialog that definitely works
"""

import sys
import time
import socket
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QLabel, QPushButton, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt

DEFAULT_TCP_PORT = 9000

class SimpleConnectionDialog(QDialog):
    """Ultra-simple connection dialog with zero styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to Server")
        self.setModal(True)
        
        # ZERO styling - pure system default
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the simplest possible connection dialog."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("LAN Collaboration Client - Connect")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        # Server IP
        self.server_ip_input = QLineEdit()
        self.server_ip_input.setText("localhost")
        form_layout.addRow("Server IP:", self.server_ip_input)
        
        # Server Port
        self.server_port_input = QLineEdit()
        self.server_port_input.setText(str(DEFAULT_TCP_PORT))
        form_layout.addRow("Server Port:", self.server_port_input)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setText(f"User_{int(time.time()) % 1000}")
        form_layout.addRow("Username:", self.username_input)
        
        layout.addLayout(form_layout)
        
        # Helper buttons
        helper_layout = QHBoxLayout()
        
        localhost_btn = QPushButton("Use Localhost")
        localhost_btn.clicked.connect(lambda: self.server_ip_input.setText("localhost"))
        helper_layout.addWidget(localhost_btn)
        
        local_ip_btn = QPushButton("Use Local IP")
        local_ip_btn.clicked.connect(self.set_local_ip)
        helper_layout.addWidget(local_ip_btn)
        
        layout.addLayout(helper_layout)
        
        # Options
        self.join_with_video = QCheckBox("Join with video")
        self.join_with_audio = QCheckBox("Join with audio")
        layout.addWidget(self.join_with_video)
        layout.addWidget(self.join_with_audio)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self.accept)
        connect_btn.setDefault(True)
        button_layout.addWidget(connect_btn)
        
        layout.addLayout(button_layout)
    
    def set_local_ip(self):
        """Set the local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            self.server_ip_input.setText(local_ip)
        except Exception:
            QMessageBox.warning(self, "IP Detection", "Could not detect local IP address")
    
    def get_connection_info(self):
        """Get connection information."""
        return {
            'host': self.server_ip_input.text().strip(),
            'port': int(self.server_port_input.text().strip()),
            'username': self.username_input.text().strip(),
            'join_with_video': self.join_with_video.isChecked(),
            'join_with_audio': self.join_with_audio.isChecked()
        }

def test_dialog():
    """Test the simple dialog."""
    app = QApplication(sys.argv)
    
    dialog = SimpleConnectionDialog()
    
    print("Testing simple connection dialog...")
    print("Can you type in the Server IP field?")
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        info = dialog.get_connection_info()
        print(f"Connection info: {info}")
    else:
        print("Dialog cancelled")

if __name__ == "__main__":
    test_dialog()