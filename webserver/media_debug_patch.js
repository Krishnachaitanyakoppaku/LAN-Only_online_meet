// Media Streaming Debug Patch
// Add this code to static/js/session.js to debug the bidirectional media issue

// Enhanced video stream handler with debugging
socket.on('video_stream', function(data) {
    console.log(`📹 [DEBUG] Received video stream from ${data.username} (I am ${currentUser})`);
    console.log(`📹 [DEBUG] Video data length: ${data.data ? data.data.length : 'no data'}`);
    console.log(`📹 [DEBUG] Session: ${currentSession}`);
    
    // Don't display our own video back to ourselves
    if (data.username === currentUser) {
        console.log(`📹 [DEBUG] Ignoring own video from ${data.username}`);
        return;
    }
    
    console.log(`📹 [DEBUG] Displaying video from ${data.username}`);
    displayVideoStream(data.username, data.data);
});

// Enhanced audio stream handler with debugging
socket.on('audio_stream', function(data) {
    console.log(`🎤 [DEBUG] Received audio stream from ${data.username} (I am ${currentUser})`);
    console.log(`🎤 [DEBUG] Audio data: ${data.data ? data.data.substring(0, 50) + '...' : 'no data'}`);
    console.log(`🎤 [DEBUG] Session: ${currentSession}`);
    
    // Don't play our own audio back to ourselves
    if (data.username === currentUser) {
        console.log(`🎤 [DEBUG] Ignoring own audio from ${data.username}`);
        return;
    }
    
    console.log(`🎤 [DEBUG] Playing audio from ${data.username}`);
    try {
        playAudioStream(data.username, data.data);
        console.log(`🎤 [DEBUG] Audio playback successful`);
    } catch (error) {
        console.error(`🎤 [DEBUG] Audio playback failed:`, error);
    }
});

// Add debugging to video sending
function startVideoStreaming() {
    if (!localStream) return;
    
    const videoTrack = localStream.getVideoTracks()[0];
    if (!videoTrack) return;
    
    // Create canvas to capture video frames
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const video = document.createElement('video');
    video.srcObject = localStream;
    video.play();
    
    function captureFrame() {
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0);
            
            // Convert canvas to base64 and send
            const dataURL = canvas.toDataURL('image/jpeg', 0.8);
            console.log(`📹 [DEBUG] Sending video data (${dataURL.length} chars) from ${currentUser} to session ${currentSession}`);
            
            socket.emit('video_data', {
                username: currentUser,
                session_id: currentSession,
                data: dataURL
            });
        }
        
        if (isVideoEnabled) {
            requestAnimationFrame(captureFrame);
        }
    }
    
    captureFrame();
}

// Add debugging to audio sending
function startAudioStreaming() {
    if (!localStream) return;
    
    const audioTrack = localStream.getAudioTracks()[0];
    if (!audioTrack) return;
    
    // Create audio context for processing
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(localStream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    
    processor.onaudioprocess = function(e) {
        if (isAudioEnabled) {
            const inputData = e.inputBuffer.getChannelData(0);
            const dataArray = new Float32Array(inputData);
            
            // Convert to base64 and send
            const dataString = Array.from(dataArray).map(x => x.toString()).join(',');
            console.log(`🎤 [DEBUG] Sending audio data (${dataString.length} chars) from ${currentUser} to session ${currentSession}`);
            
            socket.emit('audio_data', {
                username: currentUser,
                session_id: currentSession,
                data: dataString
            });
        }
    };
    
    source.connect(processor);
    processor.connect(audioContext.destination);
}

// Enhanced playAudioStream with better error handling
function playAudioStream(username, data) {
    console.log(`🔊 [DEBUG] Attempting to play audio from: ${username}`);
    
    try {
        // Convert the comma-separated string back to Float32Array
        const audioArray = new Float32Array(data.split(',').map(x => parseFloat(x)));
        console.log(`🔊 [DEBUG] Audio array length: ${audioArray.length}`);
        
        // Create audio context if not exists
        if (!window.audioContext) {
            window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log(`🔊 [DEBUG] Created new audio context`);
        }
        
        // Resume audio context if suspended (required by browsers)
        if (window.audioContext.state === 'suspended') {
            window.audioContext.resume().then(() => {
                console.log(`🔊 [DEBUG] Audio context resumed`);
            });
        }
        
        // Create audio buffer
        const audioBuffer = window.audioContext.createBuffer(1, audioArray.length, 44100);
        audioBuffer.copyToChannel(audioArray, 0);
        
        // Create buffer source and play
        const source = window.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(window.audioContext.destination);
        source.start();
        
        console.log(`🔊 [DEBUG] Playing audio from ${username}, ${audioArray.length} samples`);
    } catch (error) {
        console.error(`🔊 [DEBUG] Error playing audio from ${username}:`, error);
    }
}

// Add connection status debugging
socket.on('connect', function() {
    console.log(`🔌 [DEBUG] Socket connected, ID: ${socket.id}`);
});

socket.on('disconnect', function() {
    console.log(`🔌 [DEBUG] Socket disconnected`);
});

// Add room join debugging
socket.on('join_success', function(data) {
    console.log(`🏠 [DEBUG] Joined session successfully:`, data);
    console.log(`🏠 [DEBUG] Session ID: ${data.session}`);
    console.log(`🏠 [DEBUG] Users in session: ${data.users}`);
    console.log(`🏠 [DEBUG] Is host: ${data.is_host}`);
});

// Add user join/leave debugging
socket.on('user_joined', function(data) {
    console.log(`👤 [DEBUG] User joined:`, data);
});

socket.on('user_left', function(data) {
    console.log(`👤 [DEBUG] User left:`, data);
});

// Add media permission debugging
socket.on('video_permission_changed', function(data) {
    console.log(`📹 [DEBUG] Video permission changed:`, data);
});

socket.on('audio_permission_changed', function(data) {
    console.log(`🎤 [DEBUG] Audio permission changed:`, data);
});