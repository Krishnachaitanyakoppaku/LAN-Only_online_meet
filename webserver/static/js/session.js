// Session JavaScript for LAN Communication Hub
let socket;
let currentUser = null;
let currentSession = null;
let localStream = null;
let remoteStreams = new Map();
let isVideoEnabled = true;
let isAudioEnabled = true;
let isScreenSharing = false;
let chatMessages = [];
let participants = new Map();
let files = new Map();
let isHost = false;
let userPermissions = {};

// Check media permissions status
async function checkMediaPermissions() {
    try {
        console.log('🔍 [DEBUG] Checking media permissions...');
        
        if (navigator.permissions) {
            const cameraPermission = await navigator.permissions.query({ name: 'camera' });
            const microphonePermission = await navigator.permissions.query({ name: 'microphone' });
            
            console.log('🔍 [DEBUG] Camera permission:', cameraPermission.state);
            console.log('🔍 [DEBUG] Microphone permission:', microphonePermission.state);
            
            return {
                camera: cameraPermission.state,
                microphone: microphonePermission.state
            };
        } else {
            console.log('🔍 [DEBUG] Permissions API not supported');
            return null;
        }
    } catch (error) {
        console.log('🔍 [DEBUG] Error checking permissions:', error);
        return null;
    }
}

// Initialize session
document.addEventListener('DOMContentLoaded', async function() {
    initializeSession();
    initializeSocket();
    setupEventListeners();
    
    // Check permissions first
    const permissions = await checkMediaPermissions();
    if (permissions) {
        console.log('🔍 [DEBUG] Current permissions:', permissions);
        
        if (permissions.camera === 'denied' || permissions.microphone === 'denied') {
            console.log('🔍 [DEBUG] Permissions denied, showing instructions');
            showPermissionInstructions();
        } else {
            console.log('🔍 [DEBUG] Permissions OK, initializing media');
            initializeMedia();
        }
    } else {
        // Fallback: try to initialize media directly
        console.log('🔍 [DEBUG] Cannot check permissions, trying direct access');
        initializeMedia();
    }
});

// Load server IP and display it
function loadServerIP() {
    fetch('/api/server-info')
        .then(response => response.json())
        .then(data => {
            const serverIPElement = document.getElementById('sessionServerIP');
            if (serverIPElement) {
                serverIPElement.textContent = data.server_ip;
                console.log('🌐 [DEBUG] Server IP loaded:', data.server_ip);
            }
        })
        .catch(error => {
            console.error('🌐 [DEBUG] Failed to load server IP:', error);
            const serverIPElement = document.getElementById('sessionServerIP');
            if (serverIPElement) {
                serverIPElement.textContent = 'Unknown';
            }
        });
}

// Initialize audio context on user interaction (required by browsers)
function initializeAudioContext() {
    if (!window.audioContext) {
        window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        console.log(`🔊 [DEBUG] Audio context created, state: ${window.audioContext.state}`);
    }
    
    if (window.audioContext.state === 'suspended') {
        window.audioContext.resume().then(() => {
            console.log(`🔊 [DEBUG] Audio context resumed on user interaction`);
        }).catch(err => {
            console.error(`🔊 [DEBUG] Failed to resume audio context:`, err);
        });
    }
}

// Add click listener to initialize audio context
document.addEventListener('click', initializeAudioContext, { once: true });
document.addEventListener('keydown', initializeAudioContext, { once: true });

// Initialize session data
function initializeSession() {
    // Get session data from URL or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    currentSession = urlParams.get('session') || localStorage.getItem('currentSession');
    currentUser = urlParams.get('user') || localStorage.getItem('currentUser');
    isHost = localStorage.getItem('isHost') === 'true';
    
    if (!currentSession || !currentUser) {
        // Redirect to main page if no session data
        showMessage('No session data found. Redirecting to main page...', 'error');
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
        return;
    }
    
    // Update UI
    document.getElementById('currentSessionId').textContent = currentSession;
    if (document.getElementById('username')) {
        document.getElementById('username').textContent = currentUser;
    }
    
    // Load and display server IP
    loadServerIP();
    
    // Store in localStorage
    localStorage.setItem('currentSession', currentSession);
    localStorage.setItem('currentUser', currentUser);
    localStorage.setItem('isHost', isHost);
    
    console.log('Session initialized:', { currentUser, currentSession, isHost });
    
    // Initialize host controls after DOM is ready
    setTimeout(() => {
        updateHostControls();
    }, 100);
}

// Initialize Socket.IO connection
function initializeSocket() {
    // Auto-connect using the same host/port the client used to access the page
    // This ensures clients connect to the actual server IP, not localhost
    const serverUrl = `http://${window.location.host}`;
    console.log(`Connecting to server at: ${serverUrl}`);
    socket = io(serverUrl);
    
    socket.on('connect', function() {
        console.log('Connected to server');
        updateConnectionStatus('connected');
        
        // Join the session
        socket.emit('join_session', {
            username: currentUser,
            session_id: currentSession
        });
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        updateConnectionStatus('disconnected');
    });
    
    // Session events
    socket.on('join_success', function(data) {
        console.log('Joined session:', data);
        participants.clear();
        data.users.forEach(user => {
            participants.set(user, { name: user, video: false, audio: false, isHost: user === data.host });
        });
        
        // Update host status
        isHost = data.is_host;
        localStorage.setItem('isHost', isHost);
        
        updateParticipantsList();
        updateUserCount();
        
        // Request user permissions if host
        if (isHost) {
            socket.emit('get_user_permissions', {
                host_user: currentUser,
                session_id: currentSession
            });
        }
        
        // Update host controls visibility
        updateHostControls();
    });
    
    socket.on('user_joined', function(data) {
        participants.set(data.user, { name: data.user, video: false, audio: false });
        updateParticipantsList();
        updateUserCount();
        showMessage(`${data.user} joined the session`, 'info');
    });
    
    socket.on('user_left', function(data) {
        participants.delete(data.user);
        removeVideoStream(data.user);
        updateParticipantsList();
        updateUserCount();
        showMessage(`${data.user} left the session`, 'info');
    });
    
    // Chat events
    socket.on('new_message', function(data) {
        addChatMessage(data);
    });
    
    // Video events
    socket.on('video_stream', function(data) {
        console.log(`📹 [DEBUG] Received video stream from ${data.username} (I am ${currentUser})`);
        console.log(`📹 [DEBUG] Video data length: ${data.data ? data.data.length : 'no data'}`);
        console.log(`📹 [DEBUG] Current session: ${currentSession}`);
        
        // Don't display our own video back to ourselves
        if (data.username === currentUser) {
            console.log(`📹 [DEBUG] Ignoring own video from ${data.username}`);
            return;
        }
        
        console.log(`📹 [DEBUG] Displaying video from ${data.username}`);
        displayVideoStream(data.username, data.data);
    });
    
    // Audio events
    socket.on('audio_stream', function(data) {
        console.log(`🎤 [DEBUG] Received audio stream from ${data.username} (I am ${currentUser})`);
        console.log(`🎤 [DEBUG] Audio data: ${data.data ? data.data.substring(0, 50) + '...' : 'no data'}`);
        console.log(`🎤 [DEBUG] Current session: ${currentSession}`);
        
        // Don't play our own audio back to ourselves
        if (data.username === currentUser) {
            console.log(`🎤 [DEBUG] Ignoring own audio from ${data.username}`);
            return;
        }
        
        console.log(`🎤 [DEBUG] Attempting to play audio from ${data.username}`);
        try {
            playAudioStream(data.username, data.data);
            console.log(`🎤 [DEBUG] Audio playback initiated successfully`);
        } catch (error) {
            console.error(`🎤 [DEBUG] Audio playback failed:`, error);
        }
    });
    
    // Screen share events
    socket.on('screen_share_started', function(data) {
        showScreenShare(data.presenter);
    });
    
    socket.on('screen_share_stopped', function() {
        hideScreenShare();
    });
    
    socket.on('screen_update', function(data) {
        updateScreenShare(data.data);
    });
    
    // File events
    socket.on('file_available', function(data) {
        addFileToList(data);
    });
    
    socket.on('file_data', function(data) {
        downloadFile(data);
    });
    
    // Host control events
    socket.on('video_permission_changed', function(data) {
        if (!data.enabled) {
            toggleVideo();
            showMessage(`Your video has been disabled by ${data.controlled_by}`, 'warning');
        }
    });
    
    socket.on('audio_permission_changed', function(data) {
        if (!data.enabled) {
            toggleAudio();
            showMessage(`Your audio has been disabled by ${data.controlled_by}`, 'warning');
        }
    });
    
    socket.on('screen_share_permission_changed', function(data) {
        if (!data.enabled && isScreenSharing) {
            stopScreenShare();
            showMessage(`Your screen sharing has been disabled by ${data.controlled_by}`, 'warning');
        }
    });
    
    socket.on('kicked_from_session', function(data) {
        showMessage(`You have been kicked from the session by ${data.kicked_by}`, 'error');
        setTimeout(() => {
            window.location.href = '/';
        }, 3000);
    });
    
    socket.on('user_permissions_data', function(data) {
        userPermissions = data.permissions;
        updateHostControls();
    });
    
    socket.on('session_logs', function(data) {
        displaySessionLogs(data);
    });
    
    socket.on('permission_error', function(data) {
        showMessage(data.message, 'error');
    });
}

// Setup event listeners
function setupEventListeners() {
    // Media controls
    document.getElementById('videoToggle').addEventListener('click', toggleVideo);
    document.getElementById('audioToggle').addEventListener('click', toggleAudio);
    document.getElementById('screenShareBtn').addEventListener('click', toggleScreenShare);
    
    // Chat
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    document.getElementById('chatInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // File upload
    document.getElementById('uploadBtn').addEventListener('click', showFileUploadModal);
    document.getElementById('fileInput').addEventListener('change', handleFileUpload);
    
    // Settings
    document.getElementById('settingsBtn').addEventListener('click', showSettingsModal);
    
    // Logs (host only)
    document.getElementById('logsBtn').addEventListener('click', showSessionLogs);
    
    // Leave session
    document.getElementById('leaveBtn').addEventListener('click', leaveSession);
    
    // Chat toggle
    document.getElementById('chatToggle').addEventListener('click', toggleChat);
    
    // Fullscreen
    document.getElementById('fullscreenBtn').addEventListener('click', toggleFullscreen);
    
    // Modal close events
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
}

// Initialize media devices
async function initializeMedia() {
    try {
        console.log('🎥 [DEBUG] Requesting camera and microphone access...');
        console.log('🎥 [DEBUG] User agent:', navigator.userAgent);
        console.log('🎥 [DEBUG] Is HTTPS:', location.protocol === 'https:');
        
        // Check if getUserMedia is supported
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('getUserMedia is not supported in this browser');
        }
        
        // Request camera and microphone access with detailed constraints
        const constraints = {
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                frameRate: { ideal: 15 }
            },
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        };
        
        console.log('🎥 [DEBUG] Requesting media with constraints:', constraints);
        localStream = await navigator.mediaDevices.getUserMedia(constraints);
        
        console.log('🎥 [DEBUG] Media access granted successfully!');
        console.log('🎥 [DEBUG] Video tracks:', localStream.getVideoTracks().length);
        console.log('🎥 [DEBUG] Audio tracks:', localStream.getAudioTracks().length);
        
        // Log track details
        localStream.getVideoTracks().forEach((track, index) => {
            console.log(`🎥 [DEBUG] Video track ${index}:`, track.label, track.getSettings());
        });
        
        localStream.getAudioTracks().forEach((track, index) => {
            console.log('🎤 [DEBUG] Audio track ${index}:', track.label, track.getSettings());
        });
        
        // Display local video
        displayLocalVideo();
        
        // Start sending video data
        startVideoStreaming();
        
        // Delay audio streaming slightly to ensure everything is ready
        setTimeout(() => {
            startAudioStreaming();
        }, 1000);
        
        showMessage('Camera and microphone access granted!', 'success');
        
    } catch (error) {
        console.error('🎥 [DEBUG] Error accessing media devices:', error);
        
        let errorMessage = 'Could not access camera/microphone. ';
        
        if (error.name === 'NotAllowedError') {
            errorMessage += 'Permission denied. Please allow camera and microphone access and refresh the page.';
            console.log('🎥 [DEBUG] Permission denied - user needs to grant access');
        } else if (error.name === 'NotFoundError') {
            errorMessage += 'No camera or microphone found. Please connect a camera/microphone.';
            console.log('🎥 [DEBUG] No media devices found');
        } else if (error.name === 'NotReadableError') {
            errorMessage += 'Camera/microphone is already in use by another application.';
            console.log('🎥 [DEBUG] Media devices are busy');
        } else if (error.name === 'OverconstrainedError') {
            errorMessage += 'Camera/microphone constraints cannot be satisfied.';
            console.log('🎥 [DEBUG] Media constraints too restrictive');
            
            // Try with simpler constraints
            console.log('🎥 [DEBUG] Retrying with basic constraints...');
            try {
                localStream = await navigator.mediaDevices.getUserMedia({
                    video: true,
                    audio: true
                });
                console.log('🎥 [DEBUG] Basic constraints worked!');
                displayLocalVideo();
                startVideoStreaming();
                setTimeout(() => startAudioStreaming(), 1000);
                showMessage('Camera and microphone access granted with basic settings!', 'success');
                return;
            } catch (retryError) {
                console.error('🎥 [DEBUG] Retry also failed:', retryError);
            }
        } else if (error.name === 'SecurityError') {
            errorMessage += 'Security error. Please use HTTPS or localhost.';
            console.log('🎥 [DEBUG] Security error - may need HTTPS');
        } else {
            errorMessage += `Unknown error: ${error.message}`;
            console.log('🎥 [DEBUG] Unknown error:', error);
        }
        
        showMessage(errorMessage, 'error', 10000);
        
        // Show manual permission instructions
        showPermissionInstructions();
    }
}

// Show permission instructions to user
function showPermissionInstructions() {
    const instructions = `
        📋 To enable camera and microphone:
        
        1. Look for camera/microphone icon in browser address bar
        2. Click it and select "Allow"
        3. Refresh the page
        
        Or go to browser settings:
        • Chrome: Settings > Privacy > Site Settings > Camera/Microphone
        • Firefox: Settings > Privacy > Permissions > Camera/Microphone
        • Safari: Preferences > Websites > Camera/Microphone
    `;
    
    console.log('🎥 [DEBUG] Permission instructions:', instructions);
    
    // Create a modal with instructions
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Camera/Microphone Access Required</h3>
                <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <p>To participate in the video call, please enable camera and microphone access:</p>
                <ol>
                    <li>Look for the camera/microphone icon in your browser's address bar</li>
                    <li>Click it and select "Allow"</li>
                    <li>Refresh the page</li>
                </ol>
                <p><strong>Alternative:</strong> Go to your browser settings and enable camera/microphone for this site.</p>
                <button class="btn btn-primary" onclick="location.reload()">Refresh Page</button>
                <button class="btn btn-secondary" onclick="retryMediaAccess()">Try Again</button>
                <button class="btn btn-info" onclick="testMediaAccess()">Test Camera/Mic</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// Retry media access
async function retryMediaAccess() {
    console.log('🎥 [DEBUG] Retrying media access...');
    document.querySelectorAll('.modal').forEach(modal => modal.remove());
    await initializeMedia();
}

// Test media access function
async function testMediaAccess() {
    console.log('🧪 [DEBUG] Starting media access test...');
    
    try {
        // Test basic media access
        console.log('🧪 [DEBUG] Testing basic getUserMedia...');
        const testStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });
        
        console.log('🧪 [DEBUG] Basic test successful!');
        console.log('🧪 [DEBUG] Video tracks:', testStream.getVideoTracks().length);
        console.log('🧪 [DEBUG] Audio tracks:', testStream.getAudioTracks().length);
        
        // Show success message
        showMessage('✅ Camera and microphone access test successful!', 'success');
        
        // Stop test stream
        testStream.getTracks().forEach(track => track.stop());
        
        // Now try to initialize the actual media
        console.log('🧪 [DEBUG] Initializing actual media stream...');
        await initializeMedia();
        
    } catch (error) {
        console.error('🧪 [DEBUG] Media test failed:', error);
        
        let errorMsg = '❌ Media access test failed: ';
        
        switch (error.name) {
            case 'NotAllowedError':
                errorMsg += 'Permission denied. Please allow camera/microphone access.';
                break;
            case 'NotFoundError':
                errorMsg += 'No camera or microphone found.';
                break;
            case 'NotReadableError':
                errorMsg += 'Camera/microphone is busy or unavailable.';
                break;
            case 'SecurityError':
                errorMsg += 'Security error. Try using HTTPS or localhost.';
                break;
            default:
                errorMsg += error.message;
        }
        
        showMessage(errorMsg, 'error', 8000);
        showPermissionInstructions();
    }
}

// Display local video
function displayLocalVideo() {
    const videoGrid = document.getElementById('videoGrid');
    const localVideoContainer = document.createElement('div');
    localVideoContainer.className = 'video-container';
    localVideoContainer.id = 'localVideoContainer';
    
    const video = document.createElement('video');
    video.srcObject = localStream;
    video.autoplay = true;
    video.muted = true; // Mute local video to prevent feedback
    
    const overlay = document.createElement('div');
    overlay.className = 'video-overlay';
    overlay.innerHTML = `
        <i class="fas fa-user"></i>
        <span>${currentUser} (You)</span>
    `;
    
    const controls = document.createElement('div');
    controls.className = 'video-controls';
    controls.innerHTML = `
        <button class="video-control-btn" id="localVideoToggle">
            <i class="fas fa-video"></i>
        </button>
        <button class="video-control-btn" id="localAudioToggle">
            <i class="fas fa-microphone"></i>
        </button>
    `;
    
    localVideoContainer.appendChild(video);
    localVideoContainer.appendChild(overlay);
    localVideoContainer.appendChild(controls);
    videoGrid.appendChild(localVideoContainer);
    
    // Add event listeners for local controls
    document.getElementById('localVideoToggle').addEventListener('click', toggleVideo);
    document.getElementById('localAudioToggle').addEventListener('click', toggleAudio);
}

// Start video streaming
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
            console.log(`📹 Sent video frame from ${currentUser} to session ${currentSession}`);
        }
        
        if (isVideoEnabled) {
            requestAnimationFrame(captureFrame);
        }
    }
    
    captureFrame();
}

// Start audio streaming
function startAudioStreaming() {
    console.log('🎤 Starting audio streaming...');
    
    if (!localStream) {
        console.error('🎤 No localStream available for audio');
        return;
    }
    
    const audioTrack = localStream.getAudioTracks()[0];
    if (!audioTrack) {
        console.error('🎤 No audio track available');
        return;
    }
    
    console.log('🎤 Audio track found:', audioTrack.label);
    
    try {
        // Create audio context for processing
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        console.log('🎤 Audio context created, state:', audioContext.state);
        
        // Resume audio context if suspended (required by some browsers)
        if (audioContext.state === 'suspended') {
            audioContext.resume().then(() => {
                console.log('🎤 Audio context resumed');
            });
        }
        
        const source = audioContext.createMediaStreamSource(localStream);
        const processor = audioContext.createScriptProcessor(4096, 1, 1);
        
        let audioFrameCount = 0;
        
        processor.onaudioprocess = function(e) {
            if (isAudioEnabled && currentUser && currentSession) {
                const inputData = e.inputBuffer.getChannelData(0);
                const dataArray = new Float32Array(inputData);
                
                // Check if there's actual audio data (not just silence)
                const hasAudio = dataArray.some(sample => Math.abs(sample) > 0.001);
                
                if (hasAudio) {
                    // Convert to string and send
                    const dataString = Array.from(dataArray).map(x => x.toString()).join(',');
                    console.log(`🎤 [DEBUG] Sending audio data (${dataString.length} chars) from ${currentUser} to session ${currentSession}`);
                    
                    socket.emit('audio_data', {
                        username: currentUser,
                        session_id: currentSession,
                        data: dataString
                    });
                    
                    audioFrameCount++;
                    if (audioFrameCount % 50 === 0) { // Log every 50th frame to avoid spam
                        console.log(`🎤 [DEBUG] Sent audio frame #${audioFrameCount} from ${currentUser} to session ${currentSession}`);
                    }
                } else {
                    // Log when no audio is detected (for debugging silence issues)
                    if (audioFrameCount % 100 === 0) {
                        console.log(`🎤 [DEBUG] No audio detected in frame #${audioFrameCount}`);
                    }
                }
            } else {
                if (!isAudioEnabled) console.log('🎤 Audio disabled');
                if (!currentUser) console.log('🎤 No currentUser');
                if (!currentSession) console.log('🎤 No currentSession');
            }
        };
        
        source.connect(processor);
        processor.connect(audioContext.destination);
        
        console.log('🎤 Audio streaming setup complete');
        
    } catch (error) {
        console.error('🎤 Error setting up audio streaming:', error);
    }
}

// Display video stream from other users
function displayVideoStream(username, data) {
    let videoContainer = document.getElementById(`video-${username}`);
    
    if (!videoContainer) {
        videoContainer = document.createElement('div');
        videoContainer.className = 'video-container';
        videoContainer.id = `video-${username}`;
        
        const canvas = document.createElement('canvas');
        canvas.id = `canvas-${username}`;
        
        const overlay = document.createElement('div');
        overlay.className = 'video-overlay';
        overlay.innerHTML = `
            <i class="fas fa-user"></i>
            <span>${username}</span>
        `;
        
        videoContainer.appendChild(canvas);
        videoContainer.appendChild(overlay);
        
        document.getElementById('videoGrid').appendChild(videoContainer);
    }
    
    // Update canvas with received image
    const canvas = document.getElementById(`canvas-${username}`);
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
    };
    
    img.src = data;
}

// Remove video stream
function removeVideoStream(username) {
    const videoContainer = document.getElementById(`video-${username}`);
    if (videoContainer) {
        videoContainer.remove();
    }
}

// Play audio stream
function playAudioStream(username, data) {
    console.log(`🔊 [DEBUG] Attempting to play audio from: ${username}`);
    
    try {
        // Convert the comma-separated string back to Float32Array
        const audioArray = new Float32Array(data.split(',').map(x => parseFloat(x)));
        console.log(`🔊 [DEBUG] Audio array length: ${audioArray.length}`);
        
        // Create audio context if not exists
        if (!window.audioContext) {
            window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log(`🔊 [DEBUG] Created new audio context, state: ${window.audioContext.state}`);
        }
        
        // Resume audio context if suspended (required by browsers for autoplay policy)
        if (window.audioContext.state === 'suspended') {
            console.log(`🔊 [DEBUG] Audio context suspended, attempting to resume...`);
            window.audioContext.resume().then(() => {
                console.log(`🔊 [DEBUG] Audio context resumed successfully`);
                playAudioBuffer(audioArray, username);
            }).catch(err => {
                console.error(`🔊 [DEBUG] Failed to resume audio context:`, err);
            });
        } else {
            playAudioBuffer(audioArray, username);
        }
        
    } catch (error) {
        console.error(`🔊 [DEBUG] Error playing audio from ${username}:`, error);
    }
}

// Helper function to play audio buffer
function playAudioBuffer(audioArray, username) {
    try {
        // Create audio buffer
        const audioBuffer = window.audioContext.createBuffer(1, audioArray.length, 44100);
        audioBuffer.copyToChannel(audioArray, 0);
        
        // Create buffer source and play
        const source = window.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(window.audioContext.destination);
        
        // Add event listeners for debugging
        source.onended = () => {
            console.log(`🔊 [DEBUG] Audio playback ended for ${username}`);
        };
        
        source.start();
        console.log(`🔊 [DEBUG] Playing audio from ${username}, ${audioArray.length} samples, context state: ${window.audioContext.state}`);
        
    } catch (error) {
        console.error(`🔊 [DEBUG] Error in playAudioBuffer for ${username}:`, error);
    }
}

// Toggle video
function toggleVideo() {
    isVideoEnabled = !isVideoEnabled;
    
    if (localStream) {
        const videoTrack = localStream.getVideoTracks()[0];
        if (videoTrack) {
            videoTrack.enabled = isVideoEnabled;
        }
    }
    
    const btn = document.getElementById('videoToggle');
    const icon = btn.querySelector('i');
    
    if (isVideoEnabled) {
        icon.className = 'fas fa-video';
        btn.classList.add('active');
    } else {
        icon.className = 'fas fa-video-slash';
        btn.classList.remove('active');
    }
    
    // Update local video controls
    const localBtn = document.getElementById('localVideoToggle');
    if (localBtn) {
        const localIcon = localBtn.querySelector('i');
        localIcon.className = isVideoEnabled ? 'fas fa-video' : 'fas fa-video-slash';
    }
}

// Toggle audio
function toggleAudio() {
    isAudioEnabled = !isAudioEnabled;
    
    if (localStream) {
        const audioTrack = localStream.getAudioTracks()[0];
        if (audioTrack) {
            audioTrack.enabled = isAudioEnabled;
        }
    }
    
    // If enabling audio and we haven't started streaming yet, start it now
    if (isAudioEnabled && !window.audioStreamingStarted) {
        console.log('🎤 Starting audio streaming due to user interaction');
        startAudioStreaming();
        window.audioStreamingStarted = true;
    }
    
    const btn = document.getElementById('audioToggle');
    const icon = btn.querySelector('i');
    
    if (isAudioEnabled) {
        icon.className = 'fas fa-microphone';
        btn.classList.add('active');
    } else {
        icon.className = 'fas fa-microphone-slash';
        btn.classList.remove('active');
    }
    
    // Update local audio controls
    const localBtn = document.getElementById('localAudioToggle');
    if (localBtn) {
        const localIcon = localBtn.querySelector('i');
        localIcon.className = isAudioEnabled ? 'fas fa-microphone' : 'fas fa-microphone-slash';
    }
}

// Toggle screen share
async function toggleScreenShare() {
    if (isScreenSharing) {
        stopScreenShare();
    } else {
        await startScreenShare();
    }
}

// Start screen share
async function startScreenShare() {
    try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
            video: true,
            audio: false
        });
        
        isScreenSharing = true;
        
        // Notify server
        socket.emit('start_screen_share', {
            username: currentUser,
            session_id: currentSession
        });
        
        // Start capturing screen
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const video = document.createElement('video');
        video.srcObject = screenStream;
        video.play();
        
        function captureScreen() {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);
                
                const dataURL = canvas.toDataURL('image/jpeg', 0.8);
                socket.emit('screen_data', {
                    session_id: currentSession,
                    data: dataURL
                });
            }
            
            if (isScreenSharing) {
                requestAnimationFrame(captureScreen);
            }
        }
        
        captureScreen();
        
        // Handle screen share end
        screenStream.getVideoTracks()[0].addEventListener('ended', () => {
            stopScreenShare();
        });
        
        // Update UI
        const btn = document.getElementById('screenShareBtn');
        btn.classList.add('active');
        btn.innerHTML = '<i class="fas fa-stop"></i><span>Stop Sharing</span>';
        
    } catch (error) {
        console.error('Error starting screen share:', error);
        showMessage('Could not start screen sharing', 'error');
    }
}

// Stop screen share
function stopScreenShare() {
    isScreenSharing = false;
    
    socket.emit('stop_screen_share', {
        session_id: currentSession
    });
    
    // Update UI
    const btn = document.getElementById('screenShareBtn');
    btn.classList.remove('active');
    btn.innerHTML = '<i class="fas fa-desktop"></i><span>Share Screen</span>';
}

// Show screen share
function showScreenShare(presenter) {
    const container = document.getElementById('screenShareContainer');
    const presenterSpan = document.getElementById('screenSharePresenter');
    
    presenterSpan.textContent = `Screen sharing by: ${presenter}`;
    container.style.display = 'flex';
}

// Hide screen share
function hideScreenShare() {
    const container = document.getElementById('screenShareContainer');
    container.style.display = 'none';
}

// Update screen share
function updateScreenShare(data) {
    const img = document.getElementById('screenShareImage');
    img.src = data;
}

// Send chat message
function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    socket.emit('send_message', {
        username: currentUser,
        message: message,
        session_id: currentSession
    });
    
    input.value = '';
}

// Add chat message
function addChatMessage(data) {
    chatMessages.push(data);
    
    const messagesContainer = document.getElementById('chatMessages');
    const messageElement = document.createElement('div');
    messageElement.className = 'chat-message';
    
    const isOwnMessage = data.username === currentUser;
    
    messageElement.innerHTML = `
        <div class="message-header">
            <span class="message-sender">${data.username}</span>
            <span class="message-time">${formatTime(data.timestamp)}</span>
        </div>
        <div class="message-content ${isOwnMessage ? 'own' : ''}">${escapeHtml(data.message)}</div>
    `;
    
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Handle file upload
function handleFileUpload(event) {
    const files = event.target.files;
    
    for (let file of files) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const fileData = e.target.result;
            
            socket.emit('upload_file', {
                username: currentUser,
                filename: file.name,
                file_data: fileData,
                session_id: currentSession
            });
            
            showMessage(`Uploading ${file.name}...`, 'info');
        };
        
        reader.readAsDataURL(file);
    }
    
    // Reset input
    event.target.value = '';
    closeFileUploadModal();
}

// Add file to list
function addFileToList(data) {
    files.set(data.file_id, data);
    
    const filesList = document.getElementById('filesList');
    const fileElement = document.createElement('div');
    fileElement.className = 'file-item';
    fileElement.id = `file-${data.file_id}`;
    
    fileElement.innerHTML = `
        <div class="file-icon">
            <i class="fas fa-file"></i>
        </div>
        <div class="file-info">
            <div class="file-name">${escapeHtml(data.filename)}</div>
            <div class="file-meta">${data.uploader} • ${formatFileSize(data.size)}</div>
        </div>
        <div class="file-actions">
            <button class="file-action-btn" onclick="downloadFileById('${data.file_id}')" title="Download">
                <i class="fas fa-download"></i>
            </button>
        </div>
    `;
    
    filesList.appendChild(fileElement);
}

// Download file by ID
function downloadFileById(fileId) {
    socket.emit('download_file', {
        file_id: fileId,
        username: currentUser
    });
}

// Download file
function downloadFile(data) {
    const link = document.createElement('a');
    link.href = data.data;
    link.download = data.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showMessage(`Downloaded ${data.filename}`, 'success');
}

// Update participants list
function updateParticipantsList() {
    const participantsList = document.getElementById('participantsList');
    participantsList.innerHTML = '';
    
    participants.forEach((participant, username) => {
        const participantElement = document.createElement('div');
        participantElement.className = 'participant-item';
        
        const avatar = username.charAt(0).toUpperCase();
        const isHostUser = participant.isHost;
        const permissions = userPermissions[username] || {};
        
        participantElement.innerHTML = `
            <div class="participant-avatar ${isHostUser ? 'host-avatar' : ''}">${avatar}</div>
            <div class="participant-info">
                <div class="participant-name">
                    ${username}
                    ${isHostUser ? '<span class="host-badge">(Host)</span>' : ''}
                </div>
                <div class="participant-status">Online</div>
            </div>
            <div class="participant-controls">
                ${isHost && !isHostUser ? `
                    <button class="participant-control-btn ${permissions.video_enabled ? '' : 'disabled'}" 
                            onclick="toggleUserVideo('${username}', ${permissions.video_enabled})" 
                            title="Toggle Video">
                        <i class="fas fa-video"></i>
                    </button>
                    <button class="participant-control-btn ${permissions.audio_enabled ? '' : 'disabled'}" 
                            onclick="toggleUserAudio('${username}', ${permissions.audio_enabled})" 
                            title="Toggle Audio">
                        <i class="fas fa-microphone"></i>
                    </button>
                    <button class="participant-control-btn ${permissions.screen_share_enabled ? '' : 'disabled'}" 
                            onclick="toggleUserScreenShare('${username}', ${permissions.screen_share_enabled})" 
                            title="Toggle Screen Share">
                        <i class="fas fa-desktop"></i>
                    </button>
                    <button class="participant-control-btn kick-btn" 
                            onclick="kickUser('${username}')" 
                            title="Kick User">
                        <i class="fas fa-user-times"></i>
                    </button>
                ` : `
                    <button class="participant-control-btn" title="Video">
                        <i class="fas fa-video ${permissions.video_enabled ? '' : 'disabled'}"></i>
                    </button>
                    <button class="participant-control-btn" title="Audio">
                        <i class="fas fa-microphone ${permissions.audio_enabled ? '' : 'disabled'}"></i>
                    </button>
                `}
            </div>
        `;
        
        participantsList.appendChild(participantElement);
    });
}

// Update user count
function updateUserCount() {
    const userCount = document.getElementById('userCount');
    userCount.textContent = participants.size;
}

// Update connection status
function updateConnectionStatus(status) {
    const indicator = document.getElementById('connectionIndicator');
    if (!indicator) return;
    
    const icon = indicator.querySelector('i');
    const text = indicator.querySelector('span');
    
    switch(status) {
        case 'connected':
            icon.className = 'fas fa-circle';
            icon.style.color = '#28a745';
            text.textContent = 'Connected';
            break;
        case 'disconnected':
            icon.className = 'fas fa-circle';
            icon.style.color = '#dc3545';
            text.textContent = 'Disconnected';
            break;
    }
}

// Modal functions
function showFileUploadModal() {
    document.getElementById('fileUploadModal').style.display = 'block';
}

function closeFileUploadModal() {
    document.getElementById('fileUploadModal').style.display = 'none';
}

function showSettingsModal() {
    document.getElementById('settingsModal').style.display = 'block';
}

function closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
}

function toggleChat() {
    const chatContent = document.getElementById('chatContent');
    const toggle = document.getElementById('chatToggle');
    const icon = toggle.querySelector('i');
    
    if (chatContent.style.display === 'none') {
        chatContent.style.display = 'flex';
        icon.className = 'fas fa-chevron-down';
    } else {
        chatContent.style.display = 'none';
        icon.className = 'fas fa-chevron-up';
    }
}

function toggleFullscreen() {
    const container = document.getElementById('screenShareContainer');
    
    if (!document.fullscreenElement) {
        container.requestFullscreen().catch(err => {
            console.error('Error attempting to enable fullscreen:', err);
        });
    } else {
        document.exitFullscreen();
    }
}

// Leave session
function leaveSession() {
    if (confirm('Are you sure you want to leave the session?')) {
        // Stop all media
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
        }
        
        // Clear session data
        localStorage.removeItem('currentSession');
        localStorage.removeItem('currentUser');
        
        // Redirect to main page
        window.location.href = '/';
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function showMessage(message, type = 'info', duration = 5000) {
    // Create a simple notification system
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        border-left: 4px solid ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, duration);
}

// Host Control Functions
function toggleUserVideo(username, currentState) {
    socket.emit('toggle_user_video', {
        host_user: currentUser,
        target_user: username,
        session_id: currentSession,
        enabled: !currentState
    });
}

function toggleUserAudio(username, currentState) {
    socket.emit('toggle_user_audio', {
        host_user: currentUser,
        target_user: username,
        session_id: currentSession,
        enabled: !currentState
    });
}

function toggleUserScreenShare(username, currentState) {
    socket.emit('toggle_user_screen_share', {
        host_user: currentUser,
        target_user: username,
        session_id: currentSession,
        enabled: !currentState
    });
}

function kickUser(username) {
    if (confirm(`Are you sure you want to kick ${username} from the session?`)) {
        socket.emit('kick_user', {
            host_user: currentUser,
            target_user: username,
            session_id: currentSession
        });
    }
}

function updateHostControls() {
    console.log('Updating host controls, isHost:', isHost);
    
    // Update participants list with new permissions
    updateParticipantsList();
    
    // Show/hide host controls
    const hostControls = document.querySelectorAll('.host-control');
    console.log('Found host controls:', hostControls.length);
    hostControls.forEach(control => {
        control.style.display = isHost ? 'block' : 'none';
        console.log('Setting control display:', control.id, isHost ? 'block' : 'none');
    });
    
    // Update logs button visibility
    const logsBtn = document.getElementById('logsBtn');
    if (logsBtn) {
        logsBtn.style.display = isHost ? 'block' : 'none';
        console.log('Setting logs button display:', isHost ? 'block' : 'none');
    } else {
        console.log('Logs button not found');
    }
}

function showSessionLogs() {
    socket.emit('get_session_logs', {
        host_user: currentUser,
        session_id: currentSession
    });
}

function displaySessionLogs(data) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 800px;">
            <div class="modal-header">
                <h3>Session Logs</h3>
                <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="logs-section">
                    <h4>Upload Logs (Last 50)</h4>
                    <div class="logs-container">
                        ${data.upload_logs.map(log => `
                            <div class="log-entry">
                                <span class="log-time">${new Date(log.timestamp).toLocaleString()}</span>
                                <span class="log-user">${log.user}</span>
                                <span class="log-action">uploaded</span>
                                <span class="log-file">${log.filename}</span>
                                <span class="log-size">(${formatFileSize(log.size)})</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="logs-section">
                    <h4>Download Logs (Last 50)</h4>
                    <div class="logs-container">
                        ${data.download_logs.map(log => `
                            <div class="log-entry">
                                <span class="log-time">${new Date(log.timestamp).toLocaleString()}</span>
                                <span class="log-user">${log.user}</span>
                                <span class="log-action">downloaded</span>
                                <span class="log-file">${log.filename}</span>
                                <span class="log-size">(${formatFileSize(log.size)})</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'block';
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
    }
});
