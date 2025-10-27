#!/usr/bin/env python3
"""
Test room broadcasting to ensure audio goes to the right clients
"""
import socketio
import time
import threading

def test_room_broadcasting():
    """Test that audio is broadcasted correctly between clients"""
    print("🧪 Testing Room Broadcasting...")
    
    # Create host and client
    host = socketio.Client()
    client = socketio.Client()
    
    host_received = []
    client_received = []
    
    # Host events
    @host.event
    def connect():
        print("🏠 Host connected")
        host.emit('create_session', {'username': 'test_host'})
    
    session_created = {'session_id': None}
    
    @host.event
    def create_success(data):
        print(f"🏠 Host created session: {data['session']}")
        session_created['session_id'] = data['session']
    
    @host.event
    def audio_stream(data):
        print(f"🏠 Host received audio from: {data['username']}")
        host_received.append(data['username'])
    
    # Client events
    @client.event
    def connect():
        print("👤 Client connected")
        client.emit('join_session', {
            'username': 'test_client',
            'session_id': 'main_session'
        })
    
    @client.event
    def join_success(data):
        print(f"👤 Client joined session: {data['session']}")
        
        # Send test audio from client
        client.emit('audio_data', {
            'username': 'test_client',
            'session_id': data['session'],
            'data': '0.4,0.5,0.6'
        })
        print("👤 Client sent audio data")
        
        # Now send audio from host (both are in session)
        if session_created['session_id']:
            time.sleep(1)  # Small delay
            host.emit('audio_data', {
                'username': 'test_host',
                'session_id': session_created['session_id'],
                'data': '0.1,0.2,0.3'
            })
            print("🏠 Host sent audio data (after client joined)")
    
    @client.event
    def audio_stream(data):
        print(f"👤 Client received audio from: {data['username']}")
        client_received.append(data['username'])
    
    try:
        # Connect both
        print("🔌 Connecting host...")
        host.connect('http://localhost:5000')
        time.sleep(2)
        
        print("🔌 Connecting client...")
        client.connect('http://localhost:5000')
        time.sleep(5)  # Wait longer to see all logs
        
        # Results
        print("\n📊 Broadcasting Test Results:")
        print(f"Host received audio from: {host_received}")
        print(f"Client received audio from: {client_received}")
        
        # Check expected behavior
        if 'test_client' in host_received:
            print("✅ Host correctly received client's audio")
        else:
            print("❌ Host did NOT receive client's audio")
            
        if 'test_host' in client_received:
            print("✅ Client correctly received host's audio")
        else:
            print("❌ Client did NOT receive host's audio")
            
        # Check for self-reception (should NOT happen)
        if 'test_host' in host_received:
            print("❌ Host incorrectly received its own audio")
        else:
            print("✅ Host correctly did NOT receive its own audio")
            
        if 'test_client' in client_received:
            print("❌ Client incorrectly received its own audio")
        else:
            print("✅ Client correctly did NOT receive its own audio")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        host.disconnect()
        client.disconnect()

if __name__ == "__main__":
    test_room_broadcasting()