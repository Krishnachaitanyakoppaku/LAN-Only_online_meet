// Add this to the session.html template or session.js to create a media test button

// Add media test button to the UI
function addMediaTestButton() {
    const controlsContainer = document.querySelector('.media-controls') || document.querySelector('.controls');
    
    if (controlsContainer) {
        const testButton = document.createElement('button');
        testButton.id = 'mediaTestBtn';
        testButton.className = 'btn btn-info';
        testButton.innerHTML = '<i class="fas fa-video"></i> Test Camera/Mic';
        testButton.onclick = testMediaAccess;
        
        controlsContainer.appendChild(testButton);
        console.log('🔧 [DEBUG] Added media test button');
    }
}

// Test media access function
async function testMediaAccess() {
    console.log('🧪 [DEBUG] Starting media access test...');
    
    const testButton = document.getElementById('mediaTestBtn');
    if (testButton) {
        testButton.disabled = true;
        testButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    }
    
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
    } finally {
        if (testButton) {
            testButton.disabled = false;
            testButton.innerHTML = '<i class="fas fa-video"></i> Test Camera/Mic';
        }
    }
}

// Add the button when page loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(addMediaTestButton, 1000); // Add after other elements are loaded
});

// Also add to existing session initialization
if (typeof initializeSession === 'function') {
    const originalInitializeSession = initializeSession;
    initializeSession = function() {
        originalInitializeSession();
        setTimeout(addMediaTestButton, 500);
    };
}