#!/usr/bin/env python3
"""
Comprehensive client media access troubleshooting guide
"""

def show_client_media_troubleshooting():
    print("🎥 Client Media Access Troubleshooting")
    print("=" * 60)
    
    print("📋 CURRENT SITUATION:")
    print("✅ Host can access camera/microphone")
    print("❌ Client cannot access camera/microphone")
    print("✅ Host → Client media streaming works")
    print("❌ Client → Host media streaming fails")
    print()
    
    print("🔍 MOST LIKELY CAUSES:")
    print()
    
    print("1️⃣ BROWSER PERMISSIONS (90% of cases)")
    print("   - Client browser blocked camera/microphone access")
    print("   - User clicked 'Block' or 'Deny' when prompted")
    print("   - Browser settings have site blocked")
    print()
    
    print("2️⃣ HTTPS SECURITY POLICY (Common)")
    print("   - Modern browsers require HTTPS for camera/microphone")
    print("   - Client accessing via HTTP on different machine")
    print("   - Host works because it's on the same machine as server")
    print()
    
    print("3️⃣ HARDWARE/DRIVER ISSUES")
    print("   - Client machine has no camera/microphone")
    print("   - Camera/microphone already in use by another app")
    print("   - Driver issues or hardware problems")
    print()
    
    print("🛠️ STEP-BY-STEP DEBUGGING:")
    print()
    
    print("STEP 1: Check Browser Console")
    print("1. On client machine, open browser (Chrome/Firefox)")
    print("2. Go to http://172.17.213.107:5000")
    print("3. Press F12 to open Developer Tools")
    print("4. Go to Console tab")
    print("5. Join the session and look for error messages")
    print("6. Look for messages starting with '🎥 [DEBUG]'")
    print()
    
    print("STEP 2: Check Browser Permissions")
    print("1. Look at the browser address bar")
    print("2. Look for camera/microphone icons (🎥 🎤)")
    print("3. Click on any blocked icons")
    print("4. Change from 'Block' to 'Allow'")
    print("5. Refresh the page")
    print()
    
    print("STEP 3: Manual Permission Check")
    print("Chrome:")
    print("- Go to chrome://settings/content/camera")
    print("- Check if 172.17.213.107:5000 is in 'Block' list")
    print("- Move it to 'Allow' list if blocked")
    print("- Do the same for microphone: chrome://settings/content/microphone")
    print()
    
    print("Firefox:")
    print("- Go to about:preferences#privacy")
    print("- Scroll to 'Permissions' section")
    print("- Click 'Settings' next to Camera/Microphone")
    print("- Find 172.17.213.107 and set to 'Allow'")
    print()
    
    print("STEP 4: Test Hardware")
    print("1. On client machine, open camera app")
    print("2. Verify camera works in other applications")
    print("3. Test microphone in system settings")
    print("4. Close all other apps using camera/microphone")
    print()
    
    print("STEP 5: HTTPS Test")
    print("If client is on different machine:")
    print("1. Try accessing via localhost (if possible)")
    print("2. Set up HTTPS on server")
    print("3. Use SSH tunnel to localhost")
    print()
    
    print("🚨 COMMON ERROR MESSAGES:")
    print()
    
    print("Console Error: 'NotAllowedError'")
    print("→ SOLUTION: Grant permissions in browser")
    print("→ ACTION: Check address bar for permission icons")
    print()
    
    print("Console Error: 'NotFoundError'")
    print("→ SOLUTION: Check hardware connection")
    print("→ ACTION: Verify camera/microphone are connected")
    print()
    
    print("Console Error: 'SecurityError'")
    print("→ SOLUTION: Use HTTPS or localhost")
    print("→ ACTION: Access via https:// or localhost")
    print()
    
    print("Console Error: 'NotReadableError'")
    print("→ SOLUTION: Close other apps using camera/microphone")
    print("→ ACTION: Check Task Manager for apps using camera")
    print()
    
    print("🔧 IMMEDIATE FIXES TO TRY:")
    print()
    
    print("FIX 1: Force Permission Request")
    print("1. On client, go to http://172.17.213.107:5000")
    print("2. In browser console, type: navigator.mediaDevices.getUserMedia({video:true,audio:true})")
    print("3. Press Enter - this should trigger permission popup")
    print("4. Click 'Allow' when prompted")
    print("5. Refresh the page")
    print()
    
    print("FIX 2: Clear Browser Data")
    print("1. Clear cookies and site data for 172.17.213.107")
    print("2. Restart browser")
    print("3. Visit site again - should prompt for permissions")
    print()
    
    print("FIX 3: Try Different Browser")
    print("1. Try Chrome if using Firefox")
    print("2. Try Firefox if using Chrome")
    print("3. Try Edge or Safari")
    print()
    
    print("FIX 4: Localhost Access (Same Machine)")
    print("If client is on same machine as server:")
    print("1. Use http://localhost:5000 instead")
    print("2. This bypasses HTTPS requirements")
    print()
    
    print("FIX 5: HTTPS Setup (Different Machines)")
    print("For production use:")
    print("1. Generate SSL certificate")
    print("2. Configure server for HTTPS")
    print("3. Access via https://172.17.213.107:5000")

def show_debug_commands():
    print("\n" + "=" * 60)
    print("🔍 DEBUG COMMANDS")
    print("=" * 60)
    
    print("Run these in client browser console (F12):")
    print()
    
    print("1. Check if getUserMedia is supported:")
    print("   navigator.mediaDevices && navigator.mediaDevices.getUserMedia")
    print()
    
    print("2. Check current permissions:")
    print("   navigator.permissions.query({name: 'camera'})")
    print("   navigator.permissions.query({name: 'microphone'})")
    print()
    
    print("3. List available devices:")
    print("   navigator.mediaDevices.enumerateDevices()")
    print()
    
    print("4. Test basic media access:")
    print("   navigator.mediaDevices.getUserMedia({video:true,audio:true})")
    print("   .then(stream => console.log('SUCCESS:', stream))")
    print("   .catch(err => console.error('ERROR:', err))")
    print()
    
    print("5. Check if HTTPS is required:")
    print("   location.protocol")
    print("   (should show 'https:' for secure connection)")

def show_quick_test():
    print("\n" + "=" * 60)
    print("⚡ QUICK TEST")
    print("=" * 60)
    
    print("Test on same computer first:")
    print("1. Open http://172.17.213.107:5000 in two browser tabs")
    print("2. Host session in tab 1")
    print("3. Join session in tab 2")
    print("4. Both tabs should be able to access camera/microphone")
    print("5. If this works, the issue is network/HTTPS related")
    print("6. If this fails, the issue is browser/permissions related")

if __name__ == "__main__":
    show_client_media_troubleshooting()
    show_debug_commands()
    show_quick_test()