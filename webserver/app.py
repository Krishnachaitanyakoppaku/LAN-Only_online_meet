#!/usr/bin/env python3
"""
Simple Working LAN Meeting Web Server
All buttons and features working properly
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import json
import time
from datetime import datetime
import socket

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lan-meeting-key'
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   logger=True, 
                   engineio_logger=True,
                   async_mode='threading')

# Global state
clients = {}
chat_history = []
shared_files = {}
presenter_id = None
host_video = False
host_audio = False
host_screen = False

# Create uploads directory
os.makedirs('uploads', exist_ok=True)

@app.route('/')
def index():
    return render_template('client_simple.html')

@app.route('/host')
def host():
    return render_template('host_simple.html')

@app.route('/client')
def client():
    return render_template('client_simple.html')

@app.route('/test')
def test_socketio():
    return render_template('test_socketio.html')

@app.route('/socket.io.js')
def socketio_js():
    """Serve Socket.IO JavaScript file manually if needed"""
    try:
        # Try to serve from flask-socketio
        return send_from_directory(socketio.static_folder, 'socket.io.js')
    except:
        # Fallback - redirect to CDN
        from flask import redirect
        return redirect('https://cdn.socket.io/4.7.2/socket.io.min.js')

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'running',
        'participants': len(clients),
        'host_video': host_video,
        'host_audio': host_audio,
        'host_screen_sharing': host_screen
    })

@app.route('/api/files')
def get_files():
    return jsonify(list(shared_files.values()))

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        filename = file.filename
        file_path = os.path.join('uploads', filename)
        file.save(file_path)
        
        file_info = {
            'name': filename,
            'size': os.path.getsize(file_path),
            'shared_by': request.form.get('shared_by', 'Unknown'),
            'share_time': datetime.now().isoformat()
        }
        
        shared_files[filename] = file_info
        socketio.emit('file_shared', file_info)
        
        return jsonify({'success': True, 'file_info': file_info})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        if filename in shared_files:
            return send_from_directory('uploads', filename, as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Socket events
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    if request.sid in clients:
        client_info = clients[request.sid]
        del clients[request.sid]
        socketio.emit('user_left', {
            'client_id': request.sid,
            'name': client_info.get('name', 'Unknown')
        })

@socketio.on('join_meeting')
def handle_join_meeting(data):
    try:
        client_name = data.get('name', 'Anonymous')
        is_host = data.get('isHost', False)
        
        clients[request.sid] = {
            'name': client_name,
            'video_enabled': False,
            'audio_enabled': False,
            'screen_sharing': False,
            'is_host': is_host,
            'join_time': datetime.now().isoformat()
        }
        
        join_room('meeting')
        
        # Send current state
        emit('meeting_joined', {
            'client_id': request.sid,
            'participants': [{'id': k, **v} for k, v in clients.items()],
            'chat_history': chat_history,
            'shared_files': list(shared_files.values()),
            'presenter': presenter_id
        })
        
        # Notify others
        socketio.emit('user_joined', {
            'client_id': request.sid,
            'name': client_name,
            'is_host': is_host
        }, include_self=False)
        
        print(f"User {client_name} joined (Host: {is_host})")
        
    except Exception as e:
        print(f"Error in join_meeting: {e}")

@socketio.on('chat_message')
def handle_chat_message(data):
    try:
        message = {
            'sender': data.get('sender', 'Anonymous'),
            'message': data.get('message', ''),
            'timestamp': datetime.now().isoformat(),
            'client_id': request.sid
        }
        
        chat_history.append(message)
        socketio.emit('chat_message', message)
        print(f"Chat from {message['sender']}: {message['message']}")
        
    except Exception as e:
        print(f"Error in chat: {e}")

@socketio.on('video_frame')
def handle_video_frame(data):
    try:
        # Broadcast video frame to ALL clients (including host if it's from client)
        socketio.emit('video_frame', {
            'client_id': request.sid,
            'frame_data': data.get('frame_data'),
            'sender_name': clients.get(request.sid, {}).get('name', 'Unknown'),
            'is_host': clients.get(request.sid, {}).get('is_host', False)
        }, broadcast=True, include_self=False)
        
        print(f"Broadcasting video from {clients.get(request.sid, {}).get('name', 'Unknown')}")
    except Exception as e:
        print(f"Error in video_frame: {e}")

@socketio.on('screen_frame')
def handle_screen_frame(data):
    try:
        # Broadcast screen frame to ALL clients
        socketio.emit('screen_frame', {
            'presenter_id': request.sid,
            'frame_data': data.get('frame_data'),
            'presenter_name': clients.get(request.sid, {}).get('name', 'Unknown'),
            'is_host': clients.get(request.sid, {}).get('is_host', False)
        }, broadcast=True, include_self=False)
        
        print(f"Broadcasting screen from {clients.get(request.sid, {}).get('name', 'Unknown')}")
    except Exception as e:
        print(f"Error in screen_frame: {e}")

@socketio.on('host_media_update')
def handle_host_media_update(data):
    global host_video, host_audio, host_screen
    try:
        if clients.get(request.sid, {}).get('is_host', False):
            host_video = data.get('video_enabled', False)
            host_audio = data.get('audio_enabled', False)
            host_screen = data.get('screen_sharing', False)
            
            socketio.emit('host_status_update', {
                'video_enabled': host_video,
                'audio_enabled': host_audio,
                'screen_sharing': host_screen
            }, include_self=False)
            
            print(f"Host media: video={host_video}, audio={host_audio}, screen={host_screen}")
    except Exception as e:
        print(f"Error in host_media_update: {e}")

@socketio.on('audio_frame')
def handle_audio_frame(data):
    try:
        # Broadcast audio frame to ALL other clients
        socketio.emit('audio_frame', {
            'client_id': request.sid,
            'audio_data': data.get('audio_data'),
            'sender_name': clients.get(request.sid, {}).get('name', 'Unknown'),
            'is_host': clients.get(request.sid, {}).get('is_host', False)
        }, broadcast=True, include_self=False)
        
        # Don't print for audio as it's too frequent
    except Exception as e:
        print(f"Error in audio_frame: {e}")

@socketio.on('host_action')
def handle_host_action(data):
    try:
        if not clients.get(request.sid, {}).get('is_host', False):
            return
            
        action = data.get('action')
        
        if action == 'mute_all':
            socketio.emit('host_command', {
                'action': 'mute',
                'message': 'Muted by host'
            }, include_self=False)
            
        elif action == 'disable_video_all':
            socketio.emit('host_command', {
                'action': 'disable_video',
                'message': 'Video disabled by host'
            }, include_self=False)
            
        elif action == 'end_meeting':
            socketio.emit('host_command', {
                'action': 'end_meeting',
                'message': 'Meeting ended by host'
            }, include_self=False)
            
        print(f"Host action: {action}")
        
    except Exception as e:
        print(f"Error in host_action: {e}")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

if __name__ == '__main__':
    local_ip = get_local_ip()
    port = 5000
    
    print("🌐 LAN Meeting Web Server")
    print("=" * 40)
    print(f"📱 Host: http://localhost:{port}/host")
    print(f"👥 Client: http://localhost:{port}/client")
    print(f"🌍 LAN: http://{local_ip}:{port}/")
    print("✅ Server running - no browser auto-open")
    print("=" * 40)
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)