#!/usr/bin/env python3
"""
Safe Client Launcher - Prevents crashes and provides recovery
"""

import sys
import os
import signal
import traceback
import time

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    """Main function with crash protection"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting LAN Communication Client (Safe Mode)")
    print("=" * 50)
    
    # Set environment variables for stability
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS'] = '0'
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"\n📱 Starting client (Attempt {retry_count + 1}/{max_retries})")
            
            # Import and start client
            from client import LANCommunicationClient
            
            # Create client instance
            client = LANCommunicationClient()
            
            print("✅ Client initialized successfully")
            print("🖥️  GUI starting...")
            
            # Start the GUI main loop
            client.run()
            
            print("👋 Client shut down normally")
            break
            
        except KeyboardInterrupt:
            print("\n⏹️  Client stopped by user")
            break
            
        except Exception as e:
            retry_count += 1
            print(f"\n❌ Client crashed: {str(e)}")
            print(f"📋 Error details:")
            traceback.print_exc()
            
            if retry_count < max_retries:
                print(f"\n🔄 Restarting in 3 seconds... ({retry_count}/{max_retries})")
                time.sleep(3)
            else:
                print(f"\n💥 Maximum retries ({max_retries}) reached. Exiting.")
                print("\n🔧 Troubleshooting tips:")
                print("   1. Check if camera/microphone is being used by another app")
                print("   2. Ensure server is running and accessible")
                print("   3. Check network connectivity")
                print("   4. Restart your computer if issues persist")
                sys.exit(1)
    
    print("\n🏁 Safe client launcher finished")

if __name__ == "__main__":
    main()