# Microphone and Speaker Separation

## Overview

Replaced single audio buttons with separate microphone and speaker controls in both client and server for better audio management.

## Changes Made

### 🎤 **Client Changes**

#### **UI Updates**

- **Removed**: Single "Audio" button
- **Added**: Separate "Mic" and "Speaker" buttons
- **Layout**: Side-by-side placement with reduced padding (5px instead of 10px)

#### **New State Variables**

```python
self.microphone_enabled = False
self.speaker_enabled = True  # Speaker on by default
self.audio_enabled = False  # Kept for compatibility
```

#### **New Methods**

```python
def toggle_microphone(self):
    """Toggle microphone on/off"""

def toggle_speaker(self):
    """Toggle speaker on/off"""

def start_microphone(self):
    """Start microphone capture and streaming"""

def start_speaker(self):
    """Start speaker for playing received audio"""

def stop_microphone(self):
    """Stop microphone capture and streaming"""

def stop_speaker(self):
    """Stop speaker output"""
```

#### **Legacy Compatibility**

- `toggle_audio()` now calls `toggle_microphone()`
- `start_audio()` starts both mic and speaker
- `stop_audio()` stops both mic and speaker

### 🔊 **Server Changes**

#### **UI Updates**

- **Removed**: Single "Host Audio" button
- **Added**: Separate "Host Mic" and "Host Speaker" buttons
- **Layout**: Side-by-side placement with reduced padding

#### **New State Variables**

```python
self.host_microphone_enabled = False
self.host_speaker_enabled = True  # Speaker on by default
self.host_audio_enabled = False  # Kept for compatibility
```

#### **New Methods**

```python
def toggle_host_microphone(self):
    """Toggle Host microphone on/off"""

def toggle_host_speaker(self):
    """Toggle Host speaker on/off"""

def start_host_microphone(self):
    """Start Host microphone"""

def start_host_speaker(self):
    """Start Host speaker"""

def stop_host_microphone(self):
    """Stop Host microphone"""

def stop_host_speaker(self):
    """Stop Host speaker"""
```

## User Experience Improvements

### 🎯 **Independent Control**

- **Microphone**: Users can mute/unmute without affecting speaker
- **Speaker**: Users can disable audio output without stopping microphone
- **Flexibility**: Listen-only mode (speaker on, mic off) or broadcast-only mode (mic on, speaker off)

### 🎨 **Visual Feedback**

- **Microphone Button**:
  - Off: `🎤 Mic` (gray background)
  - On: `🎤 Mic On` (green background)
- **Speaker Button**:
  - Off: `🔊 Speaker` (gray background)
  - On: `🔊 Speaker On` (green background)

### ⚙️ **Default Behavior**

- **Speaker**: Enabled by default (users can hear others immediately)
- **Microphone**: Disabled by default (privacy-first approach)
- **Join Settings**: "Join with microphone on" checkbox still works

## Technical Implementation

### 🔧 **Audio Stream Management**

```python
# Separate stream handling
if microphone_enabled:
    # Create input stream for microphone
    self.audio_stream = self.audio.open(input=True, ...)

if speaker_enabled:
    # Create output stream for speaker
    self.audio_output_stream = self.audio.open(output=True, ...)
```

### 🛡️ **Error Handling**

- Individual error handling for mic and speaker streams
- Graceful degradation if one component fails
- Proper cleanup when stopping individual components

### 🔄 **Compatibility Layer**

- Legacy methods maintained for existing code
- Gradual migration path for future updates
- Backward compatibility with force commands

## Force Commands Updated

### 📢 **Server Force Commands**

- `force_mute` now targets microphone specifically
- `force_mute_all` affects all client microphones
- Speaker control remains with users

### 📱 **Client Response**

- Force mute stops microphone only
- Speaker remains active for listening
- Users get clear feedback about what was changed

## Benefits

### 👥 **For Users**

- **Better Control**: Independent mic/speaker management
- **Privacy**: Can listen without broadcasting
- **Flexibility**: Various participation modes
- **Clarity**: Clear visual indication of audio state

### 🔧 **For Administrators**

- **Granular Control**: Can mute participants while they still hear
- **Meeting Management**: Better control over audio flow
- **Troubleshooting**: Easier to diagnose audio issues

### 💻 **For Developers**

- **Modular Design**: Separate concerns for input/output
- **Maintainability**: Cleaner code organization
- **Extensibility**: Easier to add audio features

## Usage Scenarios

### 🎧 **Listen-Only Mode**

- Speaker: ON
- Microphone: OFF
- Use case: Large meetings, presentations, training

### 📢 **Broadcast Mode**

- Speaker: OFF (to avoid feedback)
- Microphone: ON
- Use case: Presenter with external audio setup

### 💬 **Full Participation**

- Speaker: ON
- Microphone: ON
- Use case: Regular meeting participation

### 🔇 **Silent Mode**

- Speaker: OFF
- Microphone: OFF
- Use case: Temporary disconnect from audio

## Migration Notes

### ✅ **Backward Compatibility**

- All existing audio-related code continues to work
- Legacy methods redirect to appropriate new methods
- No breaking changes for existing functionality

### 🔄 **Gradual Migration**

- Can update UI components independently
- Force commands work with new system
- Auto-start logic updated for microphone control

The separation provides users with much better control over their audio experience while maintaining full compatibility with existing features.
