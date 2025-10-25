#!/usr/bin/env python3
"""
LAN Meeting Web Server
A web-based interface for the LAN communication system
Completely offline - no internet required
"""

import os
import json
import base64
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import cv2
import numpy as np
from PIL import Image
import io

# Import your existing server logic
# from server import LANCommunicationServer

class LANMeetingWebServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'lan-meeting-secret-key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Meeting state
        self.clients = {}
        self.chat_history = []
        self.shared_files = {}
        self.presenter_id = None
        self.host_id = 'host'
        
        # Media state
        self.host_video_enabled = False
        self.host_audio_enabled = False
        self.host_screen_sharing = False
        
        self.setup_routes()
        self.setup_socket_events()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main meeting interface"""
            return render_template('meeting.html')
            
        @self.app.route('/host')
        def host():
            """Host control panel"""
            return render_template('host.html')
            
        @self.app.route('/client')
        def client():
            """Client interface"""
            return render_template('client.html')
            
        @self.app.route('/api/status')
        def status():
            """Get server status"""
            return jsonify({
                'status': 'running',
                'participants': len(self.clients),
                'host_video': self.host_video_enabled,
                'host_audio': self.host_audio_enabled,
                'host_screen_sharing': self.host_screen_sharing,
                'presenter': self.presenter_id
            })
            
        @self.app.route('/api/files')
        def get_files():
            """Get shared files list"""
            return jsonify(list(self.shared_files.values()))
            
        @self.app.route('/upload', methods=['POST'])
        def upload_file():
            """Handle file upload"""
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            # Save file and add to shared files
            filename = file.filename
            file_path = os.path.join('uploads', filename)
            os.makedirs('uploads', exist_ok=True)
            file.save(file_path)
            
            file_info = {
                'name': filename,
                'size': os.path.getsize(file_path),
                'path': file_path,
                'shared_by': request.form.get('shared_by', 'Unknown'),
                'share_time': datetime.now().isoformat()
            }
            
            self.shared_files[filename] = file_info
            
            # Notify all clients
            self.socketio.emit('file_shared', file_info)
            
            return jsonify({'success': True, 'file_info': file_info})
            
        @self.app.route('/download/<filename>')
        def download_file(filename):
            """Handle file download"""
            if filename in self.shared_files:
                file_info = self.shared_files[filename]
                return send_from_directory('uploads', filename, as_attachment=True)
            return jsonify({'error': 'File not found'}), 404
            
    def setup_socket_events(self):
        """Setup SocketIO events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
            if request.sid in self.clients:
                client_info = self.clients[request.sid]
                del self.clients[request.sid]
                emit('user_left', {
                    'client_id': request.sid,
                    'name': client_info.get('name', 'Unknown')
                }, broadcast=True)
                
        @self.socketio.on('join_meeting')
        def handle_join_meeting(data):
            """Handle client joining meeting"""
            client_name = data.get('name', 'Anonymous')
            self.clients[request.sid] = {
                'name': client_name,
                'video_enabled': False,
                'audio_enabled': False,
                'screen_sharing': False,
                'join_time': datetime.now().isoformat()
            }
            
            join_room('meeting')
            
            # Send current state to new client
            emit('meeting_joined', {
                'client_id': request.sid,
                'participants': list(self.clients.values()),
                'chat_history': self.chat_history,
                'shared_files': list(self.shared_files.values()),
                'presenter': self.presenter_id
            })
            
            # Notify others
            emit('user_joined', {
                'client_id': request.sid,
                'name': client_name
            }, broadcast=True, include_self=False)
            
        @self.socketio.on('chat_message')
        def handle_chat_message(data):
            """Handle chat message"""
            message = {
                'sender': data.get('sender', 'Anonymous'),
                'message': data.get('message', ''),
                'timestamp': datetime.now().isoformat(),
                'client_id': request.sid
            }
            
            self.chat_history.append(message)
            emit('chat_message', message, broadcast=True)
            
        @self.socketio.on('video_frame')
        def handle_video_frame(data):
            """Handle video frame from client"""
            # Broadcast video frame to all other clients
            emit('video_frame', {
                'client_id': request.sid,
                'frame_data': data.get('frame_data')
            }, broadcast=True, include_self=False)
            
        @self.socketio.on('screen_frame')
        def handle_screen_frame(data):
            """Handle screen sharing frame"""
            if request.sid == self.presenter_id or request.sid == self.host_id:
                emit('screen_frame', {
                    'presenter_id': request.sid,
                    'frame_data': data.get('frame_data')
                }, broadcast=True, include_self=False)
                
        @self.socketio.on('request_presenter')
        def handle_request_presenter(data):
            """Handle presenter request"""
            if self.presenter_id is None:
                self.presenter_id = request.sid
                if request.sid in self.clients:
                    self.clients[request.sid]['screen_sharing'] = True
                    
                emit('presenter_granted', broadcast=False)
                emit('presenter_changed', {
                    'presenter_id': request.sid,
                    'presenter_name': self.clients[request.sid]['name']
                }, broadcast=True, include_self=False)
            else:
                emit('presenter_denied', {
                    'reason': 'Another user is already presenting'
                }, broadcast=False)
                
        @self.socketio.on('stop_presenting')
        def handle_stop_presenting():
            """Handle stop presenting"""
            if request.sid == self.presenter_id:
                self.presenter_id = None
                if request.sid in self.clients:
                    self.clients[request.sid]['screen_sharing'] = False
                    
                emit('presentation_stopped', broadcast=True)
                
        @self.socketio.on('media_status_update')
        def handle_media_status_update(data):
            """Handle media status update"""
            if request.sid in self.clients:
                self.clients[request.sid].update({
                    'video_enabled': data.get('video_enabled', False),
                    'audio_enabled': data.get('audio_enabled', False),
                    'screen_sharing': data.get('screen_sharing', False)
                })
                
                emit('participant_updated', {
                    'client_id': request.sid,
                    'status': self.clients[request.sid]
                }, broadcast=True)
                
        @self.socketio.on('host_action')
        def handle_host_action(data):
            """Handle host actions (mute, disable video, etc.)"""
            action = data.get('action')
            target_client = data.get('target_client')
            
            if action and target_client:
                emit('host_command', {
                    'action': action,
                    'message': data.get('message', '')
                }, room=target_client)
                
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the web server"""
        print(f"🌐 LAN Meeting Web Server starting...")
        print(f"📱 Host Interface: http://localhost:{port}/host")
        print(f"👥 Client Interface: http://localhost:{port}/client")
        print(f"🔗 Meeting Room: http://localhost:{port}/")
        print(f"🌍 LAN Access: http://{self.get_local_ip()}:{port}/")
        print("✅ No internet required - completely offline!")
        
        self.socketio.run(self.app, host=host, port=port, debug=debug)
        
    def get_local_ip(self):
        """Get local IP address"""
        import socket
        try:
            # Connect to a dummy address to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "localhost"

if __name__ == "__main__":
    server = LANMeetingWebServer()
    server.run(debug=True)