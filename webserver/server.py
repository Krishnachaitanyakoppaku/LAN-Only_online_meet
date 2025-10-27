#!/usr/bin/env python3
"""
LAN Multi-User Communication Server
Handles all client connections and manages real-time communication
"""

import os
import json
import base64
import threading
import time
import socket
import struct
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lan_communication_secret_key'
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global variables for session management
connected_users = {}
active_sessions = {}
file_transfers = {}
presenter_id = None
screen_share_active = False
upload_logs = []
download_logs = []

# UDP socket for video/audio streaming
UDP_SOCKET = None
UDP_PORT = 5001

# Cache server IP at startup to avoid detection issues during request handling
SERVER_IP = None

def get_host_ip():
    """Get the host machine's IP address that other computers can access"""
    try:
        # First try to get the IP that other computers can access
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Check if this is a local/private IP that other computers can access
        if local_ip.startswith(('192.168.', '10.', '172.')):
            print(f"Detected network IP: {local_ip}")
            return local_ip
        else:
            # If it's not a private IP, try to get the actual network interface IP
            import subprocess
            try:
                # Try Windows ipconfig first
                result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'IPv4 Address' in line and ':' in line:
                            ip = line.split(':')[1].strip()
                            if ip.startswith(('192.168.', '10.', '172.')):
                                print(f"Detected network IP from ipconfig: {ip}")
                                return ip
                
                # Try Linux/Mac ifconfig
                result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'inet ' in line and '127.0.0.1' not in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == 'inet' and i + 1 < len(parts):
                                    ip = parts[i + 1]
                                    if ip.startswith(('192.168.', '10.', '172.')):
                                        print(f"Detected network IP from ifconfig: {ip}")
                                        return ip
                
                # Try hostname -I (Linux)
                result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    ips = result.stdout.strip().split()
                    for ip in ips:
                        if ip.startswith(('192.168.', '10.', '172.')):
                            print(f"Detected network IP from hostname: {ip}")
                            return ip
                            
            except Exception as e:
                print(f"Error running network commands: {e}")
            
            print(f"Using detected IP: {local_ip}")
            return local_ip
            
    except Exception as e:
        print(f"Failed to detect IP, using localhost: {e}")
        return "localhost"

class SessionManager:
    """Manages user sessions and room operations"""
    
    def __init__(self):
        self.sessions = {}
        self.user_sessions = {}
    
    def create_session(self, session_id, host_user):
        """Create a new session"""
        self.sessions[session_id] = {
            'host': host_user,
            'users': [host_user],
            'created_at': datetime.now(),
            'presenter': None,
            'screen_share': False,
            'user_permissions': {
                host_user: {
                    'video_enabled': True,
                    'audio_enabled': True,
                    'screen_share_enabled': True,
                    'is_host': True
                }
            }
        }
        self.user_sessions[host_user] = session_id
        return True
    
    def join_session(self, session_id, user):
        """Join an existing session"""
        print(f"Attempting to join session: {session_id}")
        print(f"Available sessions: {list(self.sessions.keys())}")
        
        # Try exact match first
        if session_id in self.sessions:
            # Check if user is already in the session
            if user in self.sessions[session_id]['users']:
                print(f"User {user} is already in session {session_id}")
                return True
            
            self.sessions[session_id]['users'].append(user)
            self.user_sessions[user] = session_id
            
            # Set default permissions for new user
            self.sessions[session_id]['user_permissions'][user] = {
                'video_enabled': True,
                'audio_enabled': True,
                'screen_share_enabled': True,
                'is_host': False
            }
            print(f"Successfully added user {user} to session {session_id}")
            return True
        
        # Try to find session with different IP format (localhost vs actual IP)
        for existing_session_id in self.sessions.keys():
            # Handle localhost variations
            if (existing_session_id == "localhost" or existing_session_id == "127.0.0.1") and session_id not in ["localhost", "127.0.0.1"]:
                print(f"Found localhost session {existing_session_id}, allowing join with IP {session_id}")
                return self.join_session(existing_session_id, user)
            elif existing_session_id not in ["localhost", "127.0.0.1"] and (session_id == "localhost" or session_id == "127.0.0.1"):
                print(f"Found IP session {existing_session_id}, allowing join with localhost")
                return self.join_session(existing_session_id, user)
            
            # Handle IP address variations (e.g., different network interfaces)
            if self.is_same_host(existing_session_id, session_id):
                print(f"Found matching host session {existing_session_id} for {session_id}")
                return self.join_session(existing_session_id, user)
        
        print(f"Session {session_id} not found")
        return False
    
    def is_same_host(self, ip1, ip2):
        """Check if two IP addresses refer to the same host"""
        try:
            import socket
            # Get all possible IPs for this host
            hostname = socket.gethostname()
            host_ips = set()
            
            # Add localhost variations
            host_ips.update(['localhost', '127.0.0.1', '0.0.0.0'])
            
            # Add actual host IPs
            try:
                host_ips.add(socket.gethostbyname(hostname))
                # Get all network interfaces
                import subprocess
                result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    ips = result.stdout.strip().split()
                    host_ips.update(ips)
            except:
                pass
            
            # Check if both IPs belong to this host
            return ip1 in host_ips and ip2 in host_ips
        except:
            return False
    
    def leave_session(self, user):
        """Leave current session"""
        if user in self.user_sessions:
            session_id = self.user_sessions[user]
            if session_id in self.sessions:
                self.sessions[session_id]['users'].remove(user)
                if user in self.sessions[session_id]['user_permissions']:
                    del self.sessions[session_id]['user_permissions'][user]
                
                # If host leaves, transfer host to first remaining user
                if self.sessions[session_id]['host'] == user and len(self.sessions[session_id]['users']) > 0:
                    new_host = self.sessions[session_id]['users'][0]
                    self.sessions[session_id]['host'] = new_host
                    self.sessions[session_id]['user_permissions'][new_host]['is_host'] = True
                
                if not self.sessions[session_id]['users']:
                    del self.sessions[session_id]
            del self.user_sessions[user]
            return session_id
        return None
    
    def get_session_users(self, session_id):
        """Get all users in a session"""
        if session_id in self.sessions:
            return self.sessions[session_id]['users']
        return []
    
    def get_session_host(self, session_id):
        """Get the host of a session"""
        if session_id in self.sessions:
            return self.sessions[session_id]['host']
        return None
    
    def is_host(self, user, session_id):
        """Check if user is the host of a session"""
        if session_id in self.sessions:
            return self.sessions[session_id]['host'] == user
        return False
    
    def update_user_permission(self, session_id, target_user, permission, value):
        """Update user permission (host only)"""
        if session_id in self.sessions and target_user in self.sessions[session_id]['user_permissions']:
            self.sessions[session_id]['user_permissions'][target_user][permission] = value
            return True
        return False
    
    def get_user_permissions(self, session_id, user):
        """Get user permissions"""
        if session_id in self.sessions and user in self.sessions[session_id]['user_permissions']:
            return self.sessions[session_id]['user_permissions'][user]
        return None

session_manager = SessionManager()

def setup_udp_socket():
    """Setup UDP socket for video/audio streaming"""
    global UDP_SOCKET
    try:
        UDP_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        UDP_SOCKET.bind(('0.0.0.0', UDP_PORT))
        print(f"UDP socket listening on port {UDP_PORT}")
        return True
    except Exception as e:
        print(f"Failed to setup UDP socket: {e}")
        return False

def start_udp_listener():
    """Start UDP listener thread for video/audio data"""
    def udp_listener():
        while True:
            try:
                data, addr = UDP_SOCKET.recvfrom(65536)
                # Process incoming video/audio data
                process_media_data(data, addr)
            except Exception as e:
                print(f"UDP listener error: {e}")
                break
    
    if UDP_SOCKET:
        thread = threading.Thread(target=udp_listener, daemon=True)
        thread.start()

def process_media_data(data, addr):
    """Process incoming media data and broadcast to other clients"""
    try:
        # Parse media data (simplified - in real implementation, you'd have proper headers)
        # For now, just broadcast to all connected users
        socketio.emit('media_data', {
            'data': base64.b64encode(data).decode('utf-8'),
            'from': addr[0]
        }, broadcast=True)
    except Exception as e:
        print(f"Error processing media data: {e}")

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/join')
def join():
    """Join session page"""
    return render_template('join.html')

@app.route('/host')
def host():
    """Host session page"""
    return render_template('host.html')

@app.route('/session')
def session():
    """Session page"""
    return render_template('session.html')

@app.route('/quick-join')
def quick_join_page():
    """Quick join page"""
    return render_template('quick-join.html')

@app.route('/simple-join')
def simple_join_page():
    """Simple join page - like your WebSocket example"""
    return render_template('simple-join.html')

@app.route('/simple-host')
def simple_host_page():
    """Simple host page"""
    return render_template('simple-host.html')

@app.route('/connection-test')
def connection_test_page():
    """Connection test page"""
    return render_template('connection-test.html')

@app.route('/find-meeting')
def session_discovery_page():
    """Session discovery page - enter session ID to connect to server"""
    return render_template('session-discovery.html')

@app.route('/api/server-info')
def server_info():
    """Get server information including IP address"""
    return jsonify({
        'server_ip': SERVER_IP or get_host_ip(),
        'server_port': 5000,
        'udp_port': 5001
    })

@app.route('/api/sessions')
def list_sessions():
    """List available sessions for joining"""
    return jsonify({
        'sessions': [
            {
                'id': session_id,
                'host': session_data['host'],
                'user_count': len(session_data['users']),
                'created_at': session_data['created_at'].isoformat() if session_data.get('created_at') else None
            }
            for session_id, session_data in session_manager.sessions.items()
        ],
        'server_ip': get_host_ip(),
        'total_sessions': len(session_manager.sessions)
    })

@app.route('/api/debug/sessions')
def debug_sessions():
    """Debug endpoint to view active sessions"""
    return jsonify({
        'active_sessions': {
            session_id: {
                'host': session_data['host'],
                'users': session_data['users'],
                'created_at': session_data['created_at'].isoformat() if session_data.get('created_at') else None,
                'user_count': len(session_data['users'])
            }
            for session_id, session_data in session_manager.sessions.items()
        },
        'connected_users': list(connected_users.keys()),
        'server_ip': SERVER_IP or get_host_ip(),
        'total_sessions': len(session_manager.sessions),
        'total_users': len(connected_users)
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'success'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")
    # Clean up user data
    user_id = None
    for uid, sid in connected_users.items():
        if sid == request.sid:
            user_id = uid
            break
    
    if user_id:
        # Don't immediately remove user from session on disconnect
        # Instead, just update their connection status
        print(f"User {user_id} disconnected, but keeping session alive")
        
        # Remove from connected_users but keep in session
        del connected_users[user_id]
        
        # Only notify other users, don't remove from session yet
        # Sessions will be cleaned up after a timeout or manual leave
        if user_id in session_manager.user_sessions:
            session_id = session_manager.user_sessions[user_id]
            socketio.emit('user_disconnected', {
                'user': user_id,
                'session': session_id
            }, room=session_id)

@socketio.on('join_session')
def handle_join_session(data):
    """Handle user joining a session"""
    username = data.get('username')
    session_id = data.get('session_id')
    
    print(f"Join session request: username={username}, session_id={session_id}")
    print(f"Current connected users: {list(connected_users.keys())}")
    print(f"Current sessions: {list(session_manager.sessions.keys())}")
    
    if not username:
        print("Join session error: Missing username")
        emit('join_error', {'message': 'Username required'})
        return
    
    # If no session_id provided, try to auto-join the main session
    if not session_id:
        # Try main session first
        if "main_session" in session_manager.sessions:
            session_id = "main_session"
            print(f"Auto-joining main session: {session_id}")
        else:
            # Fall back to first available session
            available_sessions = list(session_manager.sessions.keys())
            if available_sessions:
                session_id = available_sessions[0]
                print(f"Auto-joining first available session: {session_id}")
            else:
                emit('join_error', {'message': 'No active sessions available. Please ask the host to create a session first.'})
                return
    
    # Check if username is already connected
    if username in connected_users:
        print(f"User {username} is already connected, updating connection")
    
    # Store user connection
    connected_users[username] = request.sid
    
    # Join session
    if session_manager.join_session(session_id, username):
        join_room(session_id)
        
        print(f"User {username} successfully joined session {session_id}")
        print(f"Session host: {session_manager.get_session_host(session_id)}")
        print(f"Is {username} host: {session_manager.is_host(username, session_id)}")
        
        # Notify other users
        socketio.emit('user_joined', {
            'user': username,
            'session': session_id,
            'users': session_manager.get_session_users(session_id)
        }, room=session_id)
        
        emit('join_success', {
            'session': session_id,
            'users': session_manager.get_session_users(session_id),
            'host': session_manager.get_session_host(session_id),
            'is_host': session_manager.is_host(username, session_id)
        })
    else:
        print(f"Join session error: Session {session_id} not found")
        print(f"Available sessions: {list(session_manager.sessions.keys())}")
        
        # Provide helpful error message with server IP
        available_sessions = list(session_manager.sessions.keys())
        if available_sessions:
            error_msg = f'Session "{session_id}" not found. Available sessions: {", ".join(available_sessions)}. Please check the session ID or ask the host to share the correct session ID.'
        else:
            error_msg = f'Session "{session_id}" not found. No active sessions available. Please ask the host to create a session first.\n\n💡 The correct session ID should be the server IP: {SERVER_IP}'
        
        emit('join_error', {'message': error_msg})

@socketio.on('quick_join')
def handle_quick_join(data):
    """Handle quick join - automatically join the first available session"""
    username = data.get('username')
    
    print(f"Quick join request: username={username}")
    
    if not username:
        print("Quick join error: Missing username")
        emit('join_error', {'message': 'Username required'})
        return
    
    # Find first available session
    available_sessions = list(session_manager.sessions.keys())
    if not available_sessions:
        emit('join_error', {'message': 'No active sessions available. Please ask the host to create a session first.'})
        return
    
    session_id = available_sessions[0]
    print(f"Quick joining session: {session_id}")
    
    # Store user connection
    connected_users[username] = request.sid
    
    # Join session
    if session_manager.join_session(session_id, username):
        join_room(session_id)
        
        print(f"User {username} successfully quick-joined session {session_id}")
        
        # Notify other users
        socketio.emit('user_joined', {
            'user': username,
            'session': session_id,
            'users': session_manager.get_session_users(session_id)
        }, room=session_id)
        
        emit('join_success', {
            'session': session_id,
            'users': session_manager.get_session_users(session_id),
            'host': session_manager.get_session_host(session_id),
            'is_host': session_manager.is_host(username, session_id)
        })
    else:
        emit('join_error', {'message': 'Failed to join session'})

@socketio.on('leave_session')
def handle_leave_session(data):
    """Handle user explicitly leaving a session"""
    username = data.get('username')
    
    if username and username in session_manager.user_sessions:
        session_id = session_manager.leave_session(username)
        
        # Remove from connected users if still connected
        if username in connected_users:
            del connected_users[username]
        
        # Notify other users
        if session_id:
            socketio.emit('user_left', {
                'user': username,
                'session': session_id
            }, room=session_id)
        
        emit('leave_success', {'message': 'Left session successfully'})
    else:
        emit('leave_error', {'message': 'Not in any session'})

@socketio.on('create_session')
def handle_create_session(data):
    """Handle creating a new session"""
    username = data.get('username')
    custom_session_id = data.get('session_id')
    
    # Use a simple default session name - no need for complex IP detection
    if custom_session_id and custom_session_id.strip():
        session_id = custom_session_id.strip()
    else:
        session_id = "main_session"  # Simple default session
    
    print(f"Create session request: username={username}, session_id={session_id}")
    
    if not username:
        print("Create session error: Missing username")
        emit('create_error', {'message': 'Username required'})
        return
    
    # Check if session already exists
    if session_id in session_manager.sessions:
        print(f"Session {session_id} already exists, trying to join instead")
        # Try to join existing session
        if session_manager.join_session(session_id, username):
            connected_users[username] = request.sid
            join_room(session_id)
            
            emit('join_success', {
                'session': session_id,
                'users': session_manager.get_session_users(session_id),
                'host': session_manager.get_session_host(session_id),
                'is_host': session_manager.is_host(username, session_id)
            })
            
            # Notify other users
            socketio.emit('user_joined', {
                'user': username,
                'session': session_id,
                'users': session_manager.get_session_users(session_id)
            }, room=session_id)
        else:
            emit('create_error', {'message': 'Session exists but cannot join'})
        return
    
    # Store user connection
    connected_users[username] = request.sid
    
    # Create session
    if session_manager.create_session(session_id, username):
        join_room(session_id)
        
        print(f"Session {session_id} created successfully by {username}")
        print(f"Session data: {session_manager.sessions[session_id]}")
        
        emit('create_success', {
            'session': session_id,
            'users': session_manager.get_session_users(session_id),
            'is_host': True
        })
    else:
        print(f"Create session error: Failed to create session {session_id}")
        emit('create_error', {'message': 'Failed to create session'})

@socketio.on('send_message')
def handle_message(data):
    """Handle chat messages"""
    username = data.get('username')
    message = data.get('message')
    session_id = data.get('session_id')
    
    if username and message and session_id:
        message_data = {
            'username': username,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Broadcast to all users in session
        socketio.emit('new_message', message_data, room=session_id)

@socketio.on('start_screen_share')
def handle_start_screen_share(data):
    """Handle starting screen share"""
    username = data.get('username')
    session_id = data.get('session_id')
    
    global presenter_id, screen_share_active
    
    if username and session_id:
        presenter_id = username
        screen_share_active = True
        
        socketio.emit('screen_share_started', {
            'presenter': username,
            'session': session_id
        }, room=session_id)

@socketio.on('stop_screen_share')
def handle_stop_screen_share(data):
    """Handle stopping screen share"""
    session_id = data.get('session_id')
    
    global presenter_id, screen_share_active
    
    if session_id:
        presenter_id = None
        screen_share_active = False
        
        socketio.emit('screen_share_stopped', {
            'session': session_id
        }, room=session_id)

@socketio.on('screen_data')
def handle_screen_data(data):
    """Handle screen sharing data"""
    session_id = data.get('session_id')
    screen_data = data.get('data')
    
    if session_id and screen_data:
        # Broadcast screen data to all users except sender
        socketio.emit('screen_update', {
            'data': screen_data
        }, room=session_id, include_self=False)

@socketio.on('upload_file')
def handle_file_upload(data):
    """Handle file upload"""
    username = data.get('username')
    filename = data.get('filename')
    file_data = data.get('file_data')
    session_id = data.get('session_id')
    
    if username and filename and file_data and session_id:
        # Store file data
        file_id = f"{username}_{int(time.time())}"
        file_transfers[file_id] = {
            'filename': filename,
            'data': file_data,
            'uploader': username,
            'upload_time': datetime.now().isoformat(),
            'size': len(file_data)
        }
        
        # Log upload
        upload_logs.append({
            'timestamp': datetime.now().isoformat(),
            'user': username,
            'filename': filename,
            'size': len(file_data),
            'session_id': session_id
        })
        
        # Notify all users about new file
        socketio.emit('file_available', {
            'file_id': file_id,
            'filename': filename,
            'uploader': username,
            'size': len(file_data)
        }, room=session_id)

@socketio.on('download_file')
def handle_file_download(data):
    """Handle file download request"""
    file_id = data.get('file_id')
    username = data.get('username')
    session_id = data.get('session_id')
    
    if file_id in file_transfers:
        file_info = file_transfers[file_id]
        
        # Log download
        download_logs.append({
            'timestamp': datetime.now().isoformat(),
            'user': username,
            'filename': file_info['filename'],
            'size': file_info['size'],
            'session_id': session_id
        })
        
        emit('file_data', {
            'file_id': file_id,
            'filename': file_info['filename'],
            'data': file_info['data'],
            'size': file_info['size']
        })

@socketio.on('video_data')
def handle_video_data(data):
    """Handle video streaming data"""
    username = data.get('username')
    video_data = data.get('data')
    session_id = data.get('session_id')
    
    if username and video_data and session_id:
        # Broadcast video data to all users except sender
        socketio.emit('video_stream', {
            'username': username,
            'data': video_data
        }, room=session_id, include_self=False)

@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle audio streaming data"""
    username = data.get('username')
    audio_data = data.get('data')
    session_id = data.get('session_id')
    
    if username and audio_data and session_id:
        # Check if user has audio permission
        permissions = session_manager.get_user_permissions(session_id, username)
        if permissions and not permissions.get('audio_enabled', True):
            return
        
        # Broadcast audio data to all users except sender
        socketio.emit('audio_stream', {
            'username': username,
            'data': audio_data
        }, room=session_id, include_self=False)

# Host Control Events
@socketio.on('toggle_user_video')
def handle_toggle_user_video(data):
    """Host toggles user's video permission"""
    host_user = data.get('host_user')
    target_user = data.get('target_user')
    session_id = data.get('session_id')
    enabled = data.get('enabled')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can control user permissions'})
        return
    
    if session_manager.update_user_permission(session_id, target_user, 'video_enabled', enabled):
        # Notify the target user
        socketio.emit('video_permission_changed', {
            'enabled': enabled,
            'controlled_by': host_user
        }, room=connected_users.get(target_user))
        
        # Notify all users in session
        socketio.emit('user_permission_updated', {
            'user': target_user,
            'permission': 'video',
            'enabled': enabled,
            'controlled_by': host_user
        }, room=session_id)

@socketio.on('toggle_user_audio')
def handle_toggle_user_audio(data):
    """Host toggles user's audio permission"""
    host_user = data.get('host_user')
    target_user = data.get('target_user')
    session_id = data.get('session_id')
    enabled = data.get('enabled')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can control user permissions'})
        return
    
    if session_manager.update_user_permission(session_id, target_user, 'audio_enabled', enabled):
        # Notify the target user
        socketio.emit('audio_permission_changed', {
            'enabled': enabled,
            'controlled_by': host_user
        }, room=connected_users.get(target_user))
        
        # Notify all users in session
        socketio.emit('user_permission_updated', {
            'user': target_user,
            'permission': 'audio',
            'enabled': enabled,
            'controlled_by': host_user
        }, room=session_id)

@socketio.on('toggle_user_screen_share')
def handle_toggle_user_screen_share(data):
    """Host toggles user's screen share permission"""
    host_user = data.get('host_user')
    target_user = data.get('target_user')
    session_id = data.get('session_id')
    enabled = data.get('enabled')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can control user permissions'})
        return
    
    if session_manager.update_user_permission(session_id, target_user, 'screen_share_enabled', enabled):
        # Notify the target user
        socketio.emit('screen_share_permission_changed', {
            'enabled': enabled,
            'controlled_by': host_user
        }, room=connected_users.get(target_user))
        
        # Notify all users in session
        socketio.emit('user_permission_updated', {
            'user': target_user,
            'permission': 'screen_share',
            'enabled': enabled,
            'controlled_by': host_user
        }, room=session_id)

@socketio.on('kick_user')
def handle_kick_user(data):
    """Host kicks a user from the session"""
    host_user = data.get('host_user')
    target_user = data.get('target_user')
    session_id = data.get('session_id')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can kick users'})
        return
    
    # Notify the target user
    socketio.emit('kicked_from_session', {
        'reason': 'Kicked by host',
        'kicked_by': host_user
    }, room=connected_users.get(target_user))
    
    # Remove user from session
    session_manager.leave_session(target_user)
    
    # Notify all users in session
    socketio.emit('user_kicked', {
        'user': target_user,
        'kicked_by': host_user
    }, room=session_id)

@socketio.on('get_session_logs')
def handle_get_session_logs(data):
    """Host requests session logs"""
    host_user = data.get('host_user')
    session_id = data.get('session_id')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can view logs'})
        return
    
    emit('session_logs', {
        'upload_logs': upload_logs[-50:],  # Last 50 uploads
        'download_logs': download_logs[-50:]  # Last 50 downloads
    })

@socketio.on('get_user_permissions')
def handle_get_user_permissions(data):
    """Get user permissions for host control panel"""
    host_user = data.get('host_user')
    session_id = data.get('session_id')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can view permissions'})
        return
    
    session_data = session_manager.sessions.get(session_id, {})
    permissions = {}
    
    for user in session_data.get('users', []):
        user_perms = session_data.get('user_permissions', {}).get(user, {})
        permissions[user] = {
            'video_enabled': user_perms.get('video_enabled', True),
            'audio_enabled': user_perms.get('audio_enabled', True),
            'screen_share_enabled': user_perms.get('screen_share_enabled', True),
            'is_host': user_perms.get('is_host', False)
        }
    
    emit('user_permissions_data', {
        'permissions': permissions,
        'host': session_data.get('host')
    })

if __name__ == '__main__':
    # Initialize server IP at startup
    SERVER_IP = get_host_ip()
    print(f"Server IP detected: {SERVER_IP}")
    
    # Setup UDP socket for media streaming
    if setup_udp_socket():
        start_udp_listener()
    
    print("Starting LAN Communication Server...")
    print(f"Server will be available at: http://{SERVER_IP}:5000")
    print("UDP streaming port: 5001")
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
