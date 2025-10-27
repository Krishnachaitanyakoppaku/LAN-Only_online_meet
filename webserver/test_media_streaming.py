#!/usr/bin/env python3
"""
Test media streaming functionality
"""
import socketio
import time
import threading
import base64

def test_media_streaming():
    """Test media streaming between clients"""
    print("🧪 Testing Media Streaming...")
    
    # Create two clients - host and participant
    host_client = socketio.Client()
    participant_client = socketio.Client()
    
    host_events = []
    participant_events = []
    
    # Host client events
    @host_client.event
    def connect():
        print("🏠 Host connected")
        host_client.emit('create_session', {'username': 'test_host'})
    
    @host_client.event
    def create_success(data):
        print(f"🏠 Host created session: {data['session']}")
        host_events.append('session_created')
        
        # Send test video data
        test_video_data = base64.b64encode(b"fake_video_data").decode()
        host_client.emit('video_data', {
            'username': 'test_host',
            'session_id': data['session'],
            'data': test_video_data
        })
        print("🏠 Host sent video data")
    
    @host_client.event
    def video_stream(data):
        print(f"🏠 Host received video from: {data['username']}")
        host_events.append(f"video_from_{data['username']}")
    
    @host_client.event
    def audio_stream(data):
        print(f"🏠 Host received audio from: {data['username']}")
        host_events.append(f"audio_from_{data['username']}")
    
    # Participant client events
    @participant_client.event
    def connect():
        print("👤 Participant connected")
        participant_client.emit('join_session', {
            'username': 'test_participant',
            'session_id': 'main_session'
        })
    
    @participant_client.event
    def join_success(data):
        print(f"👤 Participant joined session: {data['session']}")
        participant_events.append('session_joined')
        
        # Send test video data
        test_video_data = base64.b64encode(b"fake_participant_video").decode()
        participant_client.emit('video_data', {
            'username': 'test_participant',
            'session_id': data['session'],
            'data': test_video_data
        })
        print("👤 Participant sent video data")
        
        # Send test audio data
        test_audio_data = "0.1,0.2,0.3,0.4,0.5"
        participant_client.emit('audio_data', {
            'username': 'test_participant',
            'session_id': data['session'],
            'data': test_audio_data
        })
        print("👤 Participant sent audio data")
    
    @participant_client.event
    def video_stream(data):
        print(f"👤 Participant received video from: {data['username']}")
        participant_events.append(f"video_from_{data['username']}")
    
    @participant_client.event
    def audio_stream(data):
        print(f"👤 Participant received audio from: {data['username']}")
        participant_events.append(f"audio_from_{data['username']}")
    
    try:
        # Connect both clients
        print("🔌 Connecting clients...")
        host_client.connect('http://localhost:5000')
        time.sleep(2)
        
        participant_client.connect('http://localhost:5000')
        time.sleep(5)  # Wait for all events
        
        # Check results
        print("\n📊 Test Results:")
        print(f"Host events: {host_events}")
        print(f"Participant events: {participant_events}")
        
        # Verify media streaming
        if 'video_from_test_participant' in host_events:
            print("✅ Host received participant's video")
        else:
            print("❌ Host did NOT receive participant's video")
            
        if 'audio_from_test_participant' in host_events:
            print("✅ Host received participant's audio")
        else:
            print("❌ Host did NOT receive participant's audio")
            
        if 'video_from_test_host' in participant_events:
            print("✅ Participant received host's video")
        else:
            print("❌ Participant did NOT receive host's video")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        host_client.disconnect()
        participant_client.disconnect()

if __name__ == "__main__":
    test_media_streaming()