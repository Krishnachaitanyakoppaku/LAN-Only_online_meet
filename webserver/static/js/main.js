// Main JavaScript for LAN Communication Hub
let socket;
let currentUser = null;
let currentSession = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    setupEventListeners();
    updateConnectionStatus('connecting');
    checkForSessionParameter();
    loadServerInfo();
});

// Load server information
function loadServerInfo() {
    fetch('/api/server-info')
        .then(response => response.json())
        .then(data => {
            const serverIPElement = document.getElementById('serverIP');
            if (serverIPElement) {
                serverIPElement.innerHTML = `
                    <i class="fas fa-server"></i>
                    <span>Server IP: ${data.server_ip}</span>
                `;
            }
        })
        .catch(error => {
            console.error('Failed to load server info:', error);
            const serverIPElement = document.getElementById('serverIP');
            if (serverIPElement) {
                serverIPElement.innerHTML = `
                    <i class="fas fa-server"></i>
                    <span>Server IP: Unknown</span>
                `;
            }
        });
}

// Check if user came with a session parameter
function checkForSessionParameter() {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session');
    
    if (sessionId) {
        // Auto-fill the join form with the session ID
        const joinSessionIdInput = document.getElementById('joinSessionId');
        if (joinSessionIdInput) {
            joinSessionIdInput.value = sessionId;
            showMessage(`Session ID auto-filled: ${sessionId}`, 'info', 5000);
        }
    }
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
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        updateConnectionStatus('disconnected');
    });
    
    socket.on('connect_error', function(error) {
        console.error('Connection error:', error);
        updateConnectionStatus('error');
        showMessage('Connection failed. Please check if the server is running.', 'error');
    });
    
    // Session events
    socket.on('create_success', function(data) {
        currentUser = document.getElementById('hostUsername').value;
        currentSession = data.session;
        
        // Show session ID to user
        showMessage(`Session created successfully! Session ID: ${data.session}`, 'success', 10000);
        
        // Store session data
        localStorage.setItem('currentUser', currentUser);
        localStorage.setItem('currentSession', currentSession);
        localStorage.setItem('isHost', data.is_host);
        
        // Show session info modal
        showSessionInfo(data.session, data.users, data.is_host);
    });
    
    socket.on('create_error', function(data) {
        showMessage(data.message, 'error');
    });
    
    socket.on('join_success', function(data) {
        currentUser = document.getElementById('joinUsername').value;
        currentSession = data.session;
        
        // Store session data
        localStorage.setItem('currentUser', currentUser);
        localStorage.setItem('currentSession', currentSession);
        localStorage.setItem('isHost', data.is_host);
        
        showMessage('Joined session successfully!', 'success');
        setTimeout(() => {
            window.location.href = '/session';
        }, 1000);
    });
    
    socket.on('join_error', function(data) {
        showMessage(data.message, 'error', 10000); // Show error for 10 seconds
        
        // Also show troubleshooting tips
        setTimeout(() => {
            showMessage('💡 Tip: Make sure the host has created the session first, and you\'re using the correct session ID (server IP address)', 'info', 8000);
        }, 2000);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Host form
    const hostForm = document.getElementById('hostForm');
    if (hostForm) {
        hostForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('hostUsername').value.trim();
            const sessionId = document.getElementById('sessionId').value.trim();
            
            if (!username) {
                showMessage('Please enter a username', 'error');
                return;
            }
            
            socket.emit('create_session', {
                username: username,
                session_id: sessionId || undefined
            });
        });
    }
    
    // Join form
    const joinForm = document.getElementById('joinForm');
    if (joinForm) {
        joinForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('joinUsername').value.trim();
            const sessionId = document.getElementById('joinSessionId').value.trim();
            
            if (!username) {
                showMessage('Please enter a username', 'error');
                return;
            }
            
            socket.emit('join_session', {
                username: username,
                session_id: sessionId || undefined // Send undefined if empty
            });
        });
    }
    
    // Modal close events
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
}

// Modal functions
function showHostModal() {
    document.getElementById('hostModal').style.display = 'block';
    document.getElementById('hostUsername').focus();
}

function closeHostModal() {
    document.getElementById('hostModal').style.display = 'none';
    document.getElementById('hostForm').reset();
}

function showJoinModal() {
    document.getElementById('joinModal').style.display = 'block';
    document.getElementById('joinUsername').focus();
}

function closeJoinModal() {
    document.getElementById('joinModal').style.display = 'none';
    document.getElementById('joinForm').reset();
}

// Show session info modal
function showSessionInfo(sessionId, users, isHost) {
    // Create session info modal if it doesn't exist
    let modal = document.getElementById('sessionInfoModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'sessionInfoModal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Session Created Successfully!</h3>
                    <button class="close-btn" onclick="closeSessionInfoModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="session-details">
                        <div class="session-id-section">
                            <label>Session ID (Host IP):</label>
                            <div class="session-id-display">
                                <input type="text" id="sessionIdDisplay" readonly value="${sessionId}">
                                <button class="btn btn-sm" onclick="copySessionId()">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </div>
                        </div>
                        <div class="session-url-section">
                            <label>Share this URL:</label>
                            <div class="session-url-display">
                                <input type="text" id="sessionUrlDisplay" readonly value="${window.location.origin}?session=${sessionId}">
                                <button class="btn btn-sm" onclick="copySessionUrl()">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </div>
                        </div>
                        <div class="participants-info">
                            <p><strong>Participants:</strong> ${users.length}</p>
                            <ul>
                                ${users.map(user => `<li>${user}${user === users[0] ? ' (Host)' : ''}</li>`).join('')}
                            </ul>
                        </div>
                        ${isHost ? `
                        <div class="host-info">
                            <div class="host-badge">
                                <i class="fas fa-crown"></i>
                                <span>You are the Host</span>
                            </div>
                            <p>As host, you can control all participants' video, audio, and screen sharing permissions.</p>
                        </div>
                        ` : ''}
                    </div>
                    <div class="session-actions">
                        <button class="btn btn-primary btn-full" onclick="enterSession()">
                            <i class="fas fa-sign-in-alt"></i>
                            Enter Session
                        </button>
                        <button class="btn btn-secondary btn-full" onclick="closeSessionInfoModal()">
                            <i class="fas fa-times"></i>
                            Stay Here
                        </button>
                        <button class="btn btn-info btn-full" onclick="checkServerStatus()" style="margin-top: 10px;">
                            <i class="fas fa-info-circle"></i>
                            Check Server Status
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Update the modal content
    document.getElementById('sessionIdDisplay').value = sessionId;
    document.getElementById('sessionUrlDisplay').value = `${window.location.origin}?session=${sessionId}`;
    
    modal.style.display = 'block';
}

function closeSessionInfoModal() {
    const modal = document.getElementById('sessionInfoModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function copySessionId() {
    const sessionId = document.getElementById('sessionIdDisplay').value;
    copyToClipboard(sessionId);
}

function copySessionUrl() {
    const sessionUrl = document.getElementById('sessionUrlDisplay').value;
    copyToClipboard(sessionUrl);
}

function enterSession() {
    window.location.href = '/session';
}

// Connection status updates
function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connectionStatus');
    if (!statusElement) return;
    
    const icon = statusElement.querySelector('i');
    const text = statusElement.querySelector('span');
    
    switch(status) {
        case 'connected':
            icon.className = 'fas fa-circle';
            icon.style.color = '#28a745';
            text.textContent = 'Connected';
            break;
        case 'connecting':
            icon.className = 'fas fa-circle';
            icon.style.color = '#ffc107';
            text.textContent = 'Connecting...';
            break;
        case 'disconnected':
            icon.className = 'fas fa-circle';
            icon.style.color = '#dc3545';
            text.textContent = 'Disconnected';
            break;
        case 'error':
            icon.className = 'fas fa-exclamation-triangle';
            icon.style.color = '#dc3545';
            text.textContent = 'Connection Error';
            break;
    }
}

// Message display system
function showMessage(message, type = 'info', duration = 5000) {
    const container = document.getElementById('messageContainer');
    if (!container) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}`;
    messageElement.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer; font-size: 1.2rem; margin-left: 10px;">&times;</button>
        </div>
    `;
    
    container.appendChild(messageElement);
    
    // Auto remove after duration
    setTimeout(() => {
        if (messageElement.parentElement) {
            messageElement.remove();
        }
    }, duration);
}

// Utility functions
function generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9);
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

// Animation utilities
function animateElement(element, animation, duration = 300) {
    element.style.animation = `${animation} ${duration}ms ease`;
    setTimeout(() => {
        element.style.animation = '';
    }, duration);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Escape key closes modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (modal.style.display === 'block') {
                modal.style.display = 'none';
            }
        });
    }
    
    // Enter key submits forms
    if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
        const form = e.target.closest('form');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
});

// Auto-generate session ID if empty
document.addEventListener('input', function(e) {
    if (e.target.id === 'sessionId' && e.target.value === '') {
        e.target.placeholder = 'Auto-generated: ' + generateSessionId();
    }
});

// Copy session ID to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showMessage('Copied to clipboard!', 'success', 2000);
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
        showMessage('Failed to copy to clipboard', 'error', 2000);
    });
}

// Validate username
function validateUsername(username) {
    if (!username || username.length < 2) {
        return 'Username must be at least 2 characters long';
    }
    if (username.length > 20) {
        return 'Username must be less than 20 characters';
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
        return 'Username can only contain letters, numbers, underscores, and hyphens';
    }
    return null;
}

// Enhanced form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        const error = validateInput(input);
        if (error) {
            isValid = false;
            showInputError(input, error);
        } else {
            clearInputError(input);
        }
    });
    
    return isValid;
}

function validateInput(input) {
    if (input.hasAttribute('required') && !input.value.trim()) {
        return 'This field is required';
    }
    
    if (input.id === 'hostUsername' || input.id === 'joinUsername') {
        return validateUsername(input.value.trim());
    }
    
    return null;
}

function showInputError(input, message) {
    clearInputError(input);
    input.style.borderColor = '#dc3545';
    
    const errorElement = document.createElement('div');
    errorElement.className = 'input-error';
    errorElement.style.color = '#dc3545';
    errorElement.style.fontSize = '0.8rem';
    errorElement.style.marginTop = '5px';
    errorElement.textContent = message;
    
    input.parentElement.appendChild(errorElement);
}

function clearInputError(input) {
    input.style.borderColor = '';
    const errorElement = input.parentElement.querySelector('.input-error');
    if (errorElement) {
        errorElement.remove();
    }
}

// Initialize tooltips and help text
function initializeHelp() {
    const helpElements = document.querySelectorAll('[data-help]');
    helpElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this, this.dataset.help);
        });
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 0.8rem;
        z-index: 1000;
        pointer-events: none;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Initialize help system
document.addEventListener('DOMContentLoaded', function() {
    initializeHelp();
});

// Quick join function
function quickJoin() {
    const username = document.getElementById('joinUsername').value.trim();
    
    if (!username) {
        showMessage('Please enter a username first', 'error');
        return;
    }
    
    socket.emit('quick_join', {
        username: username
    });
}

// Show available sessions
function showAvailableSessions() {
    fetch('/api/sessions')
        .then(response => response.json())
        .then(data => {
            if (data.sessions.length === 0) {
                showMessage('No active sessions found. Ask the host to create a session first.', 'info');
                return;
            }
            
            let message = `📋 Available Sessions (${data.sessions.length}):\n\n`;
            data.sessions.forEach(session => {
                message += `🏠 Session: ${session.id}\n`;
                message += `   Host: ${session.host}\n`;
                message += `   Users: ${session.user_count}\n`;
                if (session.created_at) {
                    message += `   Created: ${new Date(session.created_at).toLocaleString()}\n`;
                }
                message += `\n`;
            });
            
            message += `💡 Tip: Use "Quick Join" to automatically join the first available session!`;
            
            alert(message);
        })
        .catch(error => {
            console.error('Failed to get sessions:', error);
            showMessage('Failed to get session list. Please check if the server is running.', 'error');
        });
}

// Check server status and debug information
function checkServerStatus() {
    fetch('/api/debug/sessions')
        .then(response => response.json())
        .then(data => {
            let message = `🖥️ Server Status:\n`;
            message += `Server IP: ${data.server_ip}\n`;
            message += `Active Sessions: ${data.total_sessions}\n`;
            message += `Connected Users: ${data.total_users}\n\n`;
            
            if (data.total_sessions > 0) {
                message += `📋 Available Sessions:\n`;
                Object.keys(data.active_sessions).forEach(sessionId => {
                    const session = data.active_sessions[sessionId];
                    message += `• ${sessionId} (Host: ${session.host}, Users: ${session.user_count})\n`;
                });
            } else {
                message += `⚠️ No active sessions found. Host needs to create a session first.`;
            }
            
            alert(message);
        })
        .catch(error => {
            console.error('Failed to get server status:', error);
            showMessage('Failed to get server status. Please check if the server is running.', 'error');
        });
}
