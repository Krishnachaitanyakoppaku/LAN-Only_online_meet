#!/usr/bin/env python3
"""
LAN Meeting Web Server - Complete Implementation
A fully functional web-based interface for LAN communication
All buttons and features working properly
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
import socket

class LANMeetingWebServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'lan-meeting-secret-key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Meeting state
        self.clients = {}  # {client_id: client_info}
        self.chat_history = []
        self.shared_files = {}
        self.presenter_id = None
        self.host_id = 'host'
        
        # Host media state
        self.host_video_enabled = False
        self.host_audio_enabled = False
        self.host_screen_sharing = False
        
        # Meeting settings
        self.meeting_active = True
        self.allow_video = True
        self.allow_audio = True
        self.allow_screen_share = True
        self.allow_file_sharing = True
        
        # Create uploads directory
        os.makedirs('uploads', exist_ok=True)
        
        self.setup_routes()
        self.setup_socket_events()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main meeting interface"""
            return render_template('client.html')
            
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
                'presenter': self.presenter_id,
                'meeting_active': self.meeting_active,
                'settings': {
                    'allow_video': self.allow_video,
                    'allow_audio': self.allow_audio,
                    'allow_screen_share': self.allow_screen_share,
                    'allow_file_sharing': self.allow_file_sharing
                }
            })
            
        @self.app.route('/api/files')
        def get_files():
            """Get shared files list"""
            return jsonify(list(self.shared_files.values()))
            
        @self.app.route('/upload', methods=['POST'])
        def upload_file():
            """Handle file upload"""
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'No file provided'}), 400
                    
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                    
                # Save file and add to shared files
                filename = file.filename
                file_path = os.path.join('uploads', filename)
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
                self.socketio.emit('file_shared', file_info, broadcast=True)
                
                return jsonify({'success': True, 'file_info': file_info})
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
            
        @self.app.route('/download/<filename>')
        def download_file(filename):
            """Handle file download"""
            try:
                if filename in self.shared_files:
                    return send_from_directory('uploads', filename, as_attachment=True)
                return jsonify({'error': 'File not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
            
    def setup_socket_events(self):
        """Setup SocketIO events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            emit('connected', {'client_id': request.sid})
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
            if request.sid in self.clients:
                client_info = self.clients[request.sid]
                del self.clients[request.sid]
                
                # Notify others about user leaving
                self.socketio.emit('user_left', {
                    'client_id': request.sid,
                    'name': client_info.get('name', 'Unknown')
                }, broadcast=True)
                
                # Update participant count
                self.socketio.emit('participant_count_update', {
                    'count': len(self.clients)
                }, broadcast=True)
                
        @self.socketio.on('join_meeting')
        def handle_join_meeting(data):
            """Handle client joining meeting"""
            try:
                client_name = data.get('name', 'Anonymous')
                is_host = data.get('isHost', False)
                
                # Store client info
                self.clients[request.sid] = {
                    'name': client_name,
                    'video_enabled': False,
                    'audio_enabled': False,
                    'screen_sharing': False,
                    'join_time': datetime.now().isoformat(),
                    'is_host': is_host
                }
                
                join_room('meeting')
                
                # Send current state to new client
                emit('meeting_joined', {
                    'client_id': request.sid,
                    'participants': [{'id': k, **v} for k, v in self.clients.items()],
                    'chat_history': self.chat_history,
                    'shared_files': list(self.shared_files.values()),
                    'presenter': self.presenter_id,
                    'host_status': {
                        'video': self.host_video_enabled,
                        'audio': self.host_audio_enabled,
                        'screen_sharing': self.host_screen_sharing
                    }
                })
                
                # Notify others about new user
                self.socketio.emit('user_joined', {
                    'client_id': request.sid,
                    'name': client_name,
                    'is_host': is_host
                }, broadcast=True, include_self=False)
                
                # Update participant count
                self.socketio.emit('participant_count_update', {
                    'count': len(self.clients)
                }, broadcast=True)
                
                print(f"User {client_name} joined the meeting")
                
            except Exception as e:
                print(f"Error in join_meeting: {e}")
                emit('error', {'message': 'Failed to join meeting'})
                
        @self.socketio.on('chat_message')
        def handle_chat_message(data):
            """Handle chat message"""
            try:
                sender = data.get('sender', 'Anonymous')
                message_text = data.get('message', '')
                
                if not message_text.strip():
                    return
                    
                message = {
                    'sender': sender,
                    'message': message_text,
                    'timestamp': datetime.now().isoformat(),
                    'client_id': request.sid
                }
                
                self.chat_history.append(message)
                self.socketio.emit('chat_message', message, broadcast=True)
                
                print(f"Chat from {sender}: {message_text}")
                
            except Exception as e:
                print(f"Error in chat_message: {e}")
                
        @self.socketio.on('video_frame')
        def handle_video_frame(data):
            """Handle video frame from client"""
            try:
                frame_data = data.get('frame_data')
                if frame_data:
                    # Broadcast video frame to all other clients
                    self.socketio.emit('video_frame', {
                        'client_id': request.sid,
                        'frame_data': frame_data,
                        'sender_name': self.clients.get(request.sid, {}).get('name', 'Unknown')
                    }, broadcast=True, include_self=False)
                    
            except Exception as e:
                print(f"Error in video_frame: {e}")
                
        @self.socketio.on('screen_frame')
        def handle_screen_frame(data):
            """Handle screen sharing frame"""
            try:
                # Only allow if user is presenter or host
                if request.sid == self.presenter_id or self.clients.get(request.sid, {}).get('is_host', False):
                    frame_data = data.get('frame_data')
                    if frame_data:
                        self.socketio.emit('screen_frame', {
                            'presenter_id': request.sid,
                            'frame_data': frame_data,
                            'presenter_name': self.clients.get(request.sid, {}).get('name', 'Unknown')
                        }, broadcast=True, include_self=False)
                        
            except Exception as e:
                print(f"Error in screen_frame: {e}")
                
        @self.socketio.on('request_presenter')
        def handle_request_presenter():
            """Handle presenter request"""
            try:
                if self.presenter_id is None:
                    self.presenter_id = request.sid
                    if request.sid in self.clients:
                        self.clients[request.sid]['screen_sharing'] = True
                        
                    emit('presenter_granted')
                    self.socketio.emit('presenter_changed', {
                        'presenter_id': request.sid,
                        'presenter_name': self.clients[request.sid]['name']
                    }, broadcast=True, include_self=False)
                    
                    print(f"Presenter granted to {self.clients[request.sid]['name']}")
                else:
                    emit('presenter_denied', {
                        'reason': 'Another user is already presenting'
                    })
                    
            except Exception as e:
                print(f"Error in request_presenter: {e}")
                
        @self.socketio.on('stop_presenting')
        def handle_stop_presenting():
            """Handle stop presenting"""
            try:
                if request.sid == self.presenter_id:
                    self.presenter_id = None
                    if request.sid in self.clients:
                        self.clients[request.sid]['screen_sharing'] = False
                        
                    self.socketio.emit('presentation_stopped', {
                        'former_presenter': request.sid
                    }, broadcast=True)
                    
                    print(f"Presentation stopped by {self.clients.get(request.sid, {}).get('name', 'Unknown')}")
                    
            except Exception as e:
                print(f"Error in stop_presenting: {e}")
                
        @self.socketio.on('media_status_update')
        def handle_media_status_update(data):
            """Handle media status update"""
            try:
                if request.sid in self.clients:
                    self.clients[request.sid].update({
                        'video_enabled': data.get('video_enabled', False),
                        'audio_enabled': data.get('audio_enabled', False),
                        'screen_sharing': data.get('screen_sharing', False)
                    })
                    
                    # Broadcast status update
                    self.socketio.emit('participant_updated', {
                        'client_id': request.sid,
                        'status': self.clients[request.sid]
                    }, broadcast=True)
                    
            except Exception as e:
                print(f"Error in media_status_update: {e}")
                
        @self.socketio.on('host_action')
        def handle_host_action(data):
            """Handle host actions (mute, disable video, etc.)"""
            try:
                # Verify sender is host
                if not self.clients.get(request.sid, {}).get('is_host', False):
                    emit('error', {'message': 'Only host can perform this action'})
                    return
                    
                action = data.get('action')
                target_client = data.get('target_client')
                
                if action == 'mute_all':
                    self.socketio.emit('host_command', {
                        'action': 'mute',
                        'message': 'You have been muted by the host'
                    }, broadcast=True, include_self=False)
                    
                elif action == 'disable_video_all':
                    self.socketio.emit('host_command', {
                        'action': 'disable_video',
                        'message': 'Your video has been disabled by the host'
                    }, broadcast=True, include_self=False)
                    
                elif action == 'end_meeting':
                    self.meeting_active = False
                    self.socketio.emit('host_command', {
                        'action': 'end_meeting',
                        'message': 'Meeting ended by host'
                    }, broadcast=True, include_self=False)
                    
                elif action and target_client:
                    self.socketio.emit('host_command', {
                        'action': action,
                        'message': data.get('message', '')
                    }, room=target_client)
                    
                print(f"Host action: {action}")
                
            except Exception as e:
                print(f"Error in host_action: {e}")
                
        @self.socketio.on('host_media_update')
        def handle_host_media_update(data):
            """Handle host media status updates"""
            try:
                # Verify sender is host
                if not self.clients.get(request.sid, {}).get('is_host', False):
                    return
                    
                # Update host media state
                self.host_video_enabled = data.get('video_enabled', False)
                self.host_audio_enabled = data.get('audio_enabled', False)
                self.host_screen_sharing = data.get('screen_sharing', False)
                
                # Broadcast host status update
                self.socketio.emit('host_status_update', {
                    'video_enabled': self.host_video_enabled,
                    'audio_enabled': self.host_audio_enabled,
                    'screen_sharing': self.host_screen_sharing
                }, broadcast=True, include_self=False)
                
                print(f"Host media update: video={self.host_video_enabled}, audio={self.host_audio_enabled}, screen={self.host_screen_sharing}")
                
            except Exception as e:
                print(f"Error in host_media_update: {e}")
                
    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "localhost"
            
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the web server"""
        local_ip = self.get_local_ip()
        
        print("🌐 LAN Meeting Web Server starting...")
        print("=" * 50)
        print(f"📱 Host Interface: http://localhost:{port}/host")
        print(f"👥 Client Interface: http://localhost:{port}/client")
        print(f"🔗 Meeting Room: http://localhost:{port}/")
        print(f"🌍 LAN Access: http://{local_ip}:{port}/")
        print("✅ No internet required - completely offline!")
        print("=" * 50)
        
        try:
            self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
        except Exception as e:
            print(f"Error starting server: {e}")

if __name__ == "__main__":
    server = LANMeetingWebServer()
    server.run(debug=False)