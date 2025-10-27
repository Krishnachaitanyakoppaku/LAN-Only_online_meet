#!/usr/bin/env python3
"""
Debug bidirectional media streaming issue
"""

import socketio
import time
import base64

def debug_media_streaming():
    print("🔍 Debugging Bidirectional Media Streaming")
    print("=" * 60)
    
    server_url = "http://172.17.213.107:5000"
    session_id = "172.17.213.107"
    
    # Create two clients to simulate host and participant
    host_client = socketio.Client()
    participant_client = socketio.Client()
    
    host_joined = False
    participant_joined = False
    host_received_media = {"video": False, "audio": False}
    participant_received_media = {"video": False, "audio": False}
    
    print("1️⃣ Setting up host client...")
    
    # Host client events
    @host_client.event
    def connect():
        print("   🏠 Host connected")
        host_client.emit('join_session', {
            'username': 'debug_host',
            'session_id': session_id
        })
    
    @host_client.event
    def join_success(data):
        nonlocal host_joined
        host_joined = True
        print(f"   🏠 Host joined session: {data['session']}")
    
    @host_client.event
    def video_stream(data):
        host_received_media["video"] = True
        print(f"   🏠 Host received video from: {data['username']}")
    
    @host_client.event
    def audio_stream(data):
        host_received_media["audio"] = True
        print(f"   🏠 Host received audio from: {data['username']}")
    
    print("2️⃣ Setting up participant client...")
    
    # Participant client events
    @participant_client.event
    def connect():
        print("   👤 Participant connected")
        participant_client.emit('join_session', {
            'username': 'debug_participant',
            'session_id': session_id
        })
    
    @participant_client.event
    def join_success(data):
        nonlocal participant_joined
        participant_joined = True
        print(f"   👤 Participant joined session: {data['session']}")
    
    @participant_client.event
    def video_stream(data):
        participant_received_media["video"] = True
        print(f"   👤 Participant received video from: {data['username']}")
    
    @participant_client.event
    def audio_stream(data):
        participant_received_media["audio"] = True
        print(f"   👤 Participant received audio from: {data['username']}")
    
    try:
        # Connect both clients
        print("\n3️⃣ Connecting clients...")
        host_client.connect(server_url)
        time.sleep(1)
        participant_client.connect(server_url)
        time.sleep(2)
        
        if not (host_joined and participant_joined):
            print("❌ Failed to join session")
            return
        
        print("\n4️⃣ Testing Host → Participant media streaming...")
        
        # Host sends video
        test_video_data = base64.b64encode(b"fake_host_video_data").decode()
        host_client.emit('video_data', {
            'username': 'debug_host',
            'session_id': session_id,
            'data': test_video_data
        })
        print("   🏠 Host sent video data")
        
        # Host sends audio
        test_audio_data = "0.1,0.2,0.3,0.4,0.5"
        host_client.emit('audio_data', {
            'username': 'debug_host',
            'session_id': session_id,
            'data': test_audio_data
        })
        print("   🏠 Host sent audio data")
        
        time.sleep(2)
        
        print("\n5️⃣ Testing Participant → Host media streaming...")
        
        # Participant sends video
        test_video_data = base64.b64encode(b"fake_participant_video_data").decode()
        participant_client.emit('video_data', {
            'username': 'debug_participant',
            'session_id': session_id,
            'data': test_video_data
        })
        print("   👤 Participant sent video data")
        
        # Participant sends audio
        test_audio_data = "0.6,0.7,0.8,0.9,1.0"
        participant_client.emit('audio_data', {
            'username': 'debug_participant',
            'session_id': session_id,
            'data': test_audio_data
        })
        print("   👤 Participant sent audio data")
        
        time.sleep(3)
        
        print("\n" + "=" * 60)
        print("📊 RESULTS")
        print("=" * 60)
        
        print("Host → Participant:")
        print(f"   Video: {'✅ Received' if participant_received_media['video'] else '❌ Not received'}")
        print(f"   Audio: {'✅ Received' if participant_received_media['audio'] else '❌ Not received'}")
        
        print("\nParticipant → Host:")
        print(f"   Video: {'✅ Received' if host_received_media['video'] else '❌ Not received'}")
        print(f"   Audio: {'✅ Received' if host_received_media['audio'] else '❌ Not received'}")
        
        # Analyze the issue
        print("\n🔍 ANALYSIS:")
        if all(participant_received_media.values()) and all(host_received_media.values()):
            print("✅ Bidirectional media streaming is working correctly!")
        elif all(participant_received_media.values()) and not any(host_received_media.values()):
            print("❌ One-way streaming: Host → Participant works, but Participant → Host doesn't")
            print("   This suggests the host client isn't receiving media streams")
        elif not any(participant_received_media.values()) and all(host_received_media.values()):
            print("❌ One-way streaming: Participant → Host works, but Host → Participant doesn't")
            print("   This suggests the participant client isn't receiving media streams")
        else:
            print("❌ Media streaming has issues in both directions")
        
        print("\n💡 POSSIBLE CAUSES:")
        print("1. Socket.IO room broadcasting issue")
        print("2. Client-side event handler problems")
        print("3. Session management issues")
        print("4. Network/firewall blocking")
        print("5. Browser permissions or audio context issues")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        if host_client.connected:
            host_client.disconnect()
        if participant_client.connected:
            participant_client.disconnect()

if __name__ == "__main__":
    debug_media_streaming()