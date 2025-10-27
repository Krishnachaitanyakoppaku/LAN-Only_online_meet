#!/usr/bin/env python3
"""
Debug host audio sending specifically
"""
import socketio
import time

def debug_host_audio():
    """Debug if host can send audio"""
    print("🧪 Debugging Host Audio Sending...")
    
    host = socketio.Client()
    
    @host.event
    def connect():
        print("🏠 Host connected")
        host.emit('create_session', {'username': 'debug_host'})
    
    @host.event
    def create_success(data):
        print(f"🏠 Host created session: {data['session']}")
        
        # Send audio immediately
        print("🏠 Sending audio data...")
        host.emit('audio_data', {
            'username': 'debug_host',
            'session_id': data['session'],
            'data': '0.1,0.2,0.3,0.4,0.5'
        })
        print("🏠 Audio data sent!")
        
        # Send multiple times to be sure
        for i in range(3):
            time.sleep(1)
            host.emit('audio_data', {
                'username': 'debug_host',
                'session_id': data['session'],
                'data': f'0.{i},0.{i+1},0.{i+2}'
            })
            print(f"🏠 Audio data #{i+2} sent!")
    
    @host.event
    def audio_stream(data):
        print(f"🏠 Host received audio from: {data['username']} (THIS SHOULD NOT HAPPEN)")
    
    try:
        print("🔌 Connecting host...")
        host.connect('http://localhost:5000')
        time.sleep(10)  # Wait to see all server logs
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        host.disconnect()

if __name__ == "__main__":
    debug_host_audio()