#!/usr/bin/env python3
"""
Simple Connection Dialog for LAN Collaboration Client
Provides a clean interface for entering server connection details
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QPushButton, QDialogButtonBox,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon


class SimpleConnectionDialog(QDialog):
    """Simple connection dialog for server details."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to Server")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        # Connection info
        self.connection_info = {}
        
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🌐 Connect to Collaboration Server")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Connection form
        form_group = QGroupBox("Server Details")
        form_layout = QFormLayout(form_group)
        
        # Server host
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("localhost or IP address")
        self.host_input.setText("localhost")
        form_layout.addRow("🖥️ Server Host:", self.host_input)
        
        # Server port
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("9000")
        self.port_input.setText("9000")
        form_layout.addRow("🔌 Port:", self.port_input)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Your display name")
        form_layout.addRow("👤 Username:", self.username_input)
        
        layout.addWidget(form_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_connection)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Focus on username field
        self.username_input.setFocus()
    
    def apply_styles(self):
        """Apply dark theme styles."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                padding: 5px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
    
    def accept_connection(self):
        """Validate and accept connection details."""
        host = self.host_input.text().strip()
        port_text = self.port_input.text().strip()
        username = self.username_input.text().strip()
        
        # Validation
        if not host:
            QMessageBox.warning(self, "Invalid Input", "Please enter a server host.")
            self.host_input.setFocus()
            return
        
        if not port_text:
            QMessageBox.warning(self, "Invalid Input", "Please enter a port number.")
            self.port_input.setFocus()
            return
        
        try:
            port = int(port_text)
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid port number (1-65535).")
            self.port_input.setFocus()
            return
        
        if not username:
            QMessageBox.warning(self, "Invalid Input", "Please enter a username.")
            self.username_input.setFocus()
            return
        
        if len(username) > 50:
            QMessageBox.warning(self, "Invalid Input", "Username must be 50 characters or less.")
            self.username_input.setFocus()
            return
        
        # Store connection info
        self.connection_info = {
            'host': host,
            'port': port,
            'username': username
        }
        
        self.accept()
    
    def get_connection_info(self):
        """Get the connection information."""
        return self.connection_info