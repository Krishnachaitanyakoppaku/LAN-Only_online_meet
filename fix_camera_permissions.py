#!/usr/bin/env python3
"""
Camera Permission Fix Script for LAN Video Calling Application
This script helps fix camera permission issues on Linux systems
"""

import os
import sys
import subprocess
import glob
import getpass

def check_camera_devices():
    """Check available camera devices"""
    print("Checking camera devices...")
    video_devices = glob.glob('/dev/video*')
    
    if not video_devices:
        print("❌ No video devices found at /dev/video*")
        return False
    
    print(f"✅ Found video devices: {video_devices}")
    
    # Check permissions
    accessible_devices = []
    for device in video_devices:
        if os.access(device, os.R_OK | os.W_OK):
            print(f"✅ Device {device} is accessible")
            accessible_devices.append(device)
        else:
            print(f"❌ Device {device} is not accessible (permission denied)")
    
    return len(accessible_devices) > 0

def check_user_groups():
    """Check if user is in video group"""
    print("\nChecking user groups...")
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout.strip().split()
        
        if 'video' in groups:
            print("✅ User is in 'video' group")
            return True
        else:
            print("❌ User is NOT in 'video' group")
            return False
    except Exception as e:
        print(f"❌ Error checking groups: {e}")
        return False

def add_user_to_video_group():
    """Add user to video group"""
    print("\nAdding user to video group...")
    try:
        username = getpass.getuser()
        print(f"Adding user '{username}' to 'video' group...")
        
        # Add user to video group
        result = subprocess.run(['sudo', 'usermod', '-a', '-G', 'video', username], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Successfully added user to video group")
            print("⚠️  You need to log out and log back in for changes to take effect")
            return True
        else:
            print(f"❌ Failed to add user to video group: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error adding user to video group: {e}")
        return False

def check_camera_usage():
    """Check if camera is being used by other processes"""
    print("\nChecking camera usage...")
    try:
        # Check for processes using video devices
        result = subprocess.run(['lsof', '/dev/video*'], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            print("⚠️  Camera is being used by other processes:")
            print(result.stdout)
            return False
        else:
            print("✅ Camera is not being used by other processes")
            return True
    except Exception as e:
        print(f"⚠️  Could not check camera usage: {e}")
        return True

def test_camera_with_opencv():
    """Test camera with OpenCV"""
    print("\nTesting camera with OpenCV...")
    try:
        import cv2
        
        # Try to open camera
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Camera opened successfully with OpenCV")
            ret, frame = cap.read()
            if ret:
                print("✅ Camera can capture frames")
                cap.release()
                return True
            else:
                print("❌ Camera opened but cannot capture frames")
                cap.release()
                return False
        else:
            print("❌ Could not open camera with OpenCV")
            return False
    except ImportError:
        print("❌ OpenCV not installed")
        return False
    except Exception as e:
        print(f"❌ Error testing camera: {e}")
        return False

def main():
    """Main function"""
    print("LAN Video Calling - Camera Permission Fix")
    print("=" * 50)
    
    # Check if running on Linux
    if os.name != 'posix':
        print("❌ This script is designed for Linux systems")
        sys.exit(1)
    
    # Check if running as root
    if os.geteuid() == 0:
        print("⚠️  Running as root. This is not recommended for security reasons.")
        print("   Please run as a regular user and use sudo when needed.")
        sys.exit(1)
    
    # Step 1: Check camera devices
    devices_ok = check_camera_devices()
    
    # Step 2: Check user groups
    groups_ok = check_user_groups()
    
    # Step 3: Check camera usage
    usage_ok = check_camera_usage()
    
    # Step 4: Test camera with OpenCV
    opencv_ok = test_camera_with_opencv()
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC RESULTS:")
    print(f"Camera devices found: {'✅' if devices_ok else '❌'}")
    print(f"User in video group: {'✅' if groups_ok else '❌'}")
    print(f"Camera not in use: {'✅' if usage_ok else '❌'}")
    print(f"OpenCV camera test: {'✅' if opencv_ok else '❌'}")
    
    if not groups_ok:
        print("\n🔧 FIXING PERMISSIONS:")
        if add_user_to_video_group():
            print("\n✅ Permission fix applied!")
            print("⚠️  IMPORTANT: You must log out and log back in for changes to take effect.")
            print("   After logging back in, run this script again to verify the fix.")
        else:
            print("\n❌ Could not fix permissions automatically.")
            print("   Please run manually: sudo usermod -a -G video $USER")
    
    if opencv_ok:
        print("\n🎉 Camera is working! You can now use the video calling application.")
    else:
        print("\n❌ Camera is still not working. Please try the following:")
        print("1. Log out and log back in (if you just added yourself to video group)")
        print("2. Check if another application is using the camera")
        print("3. Try running the application with sudo (temporary solution)")
        print("4. Check camera with: cheese or guvcview")
        print("5. Verify camera is working with: ls -la /dev/video*")

if __name__ == "__main__":
    main()

