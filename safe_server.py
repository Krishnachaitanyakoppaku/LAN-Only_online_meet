#!/usr/bin/env python3
"""
Safe Server Launcher - Prevents crashes and provides recovery
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
    
    print("🚀 Starting LAN Communication Server (Safe Mode)")
    print("=" * 50)
    
    # Set environment variables for stability
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS'] = '0'
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"\n📡 Starting server (Attempt {retry_count + 1}/{max_retries})")
            
            # Import and start server
            from server import LANCommunicationServer
            
            # Create server instance
            server = LANCommunicationServer()
            
            print("✅ Server initialized successfully")
            print("🖥️  GUI starting...")
            
            # Start the GUI main loop
            server.root.mainloop()
            
            print("👋 Server shut down normally")
            break
            
        except KeyboardInterrupt:
            print("\n⏹️  Server stopped by user")
            break
            
        except Exception as e:
            retry_count += 1
            print(f"\n❌ Server crashed: {str(e)}")
            print(f"📋 Error details:")
            traceback.print_exc()
            
            if retry_count < max_retries:
                print(f"\n🔄 Restarting in 3 seconds... ({retry_count}/{max_retries})")
                time.sleep(3)
            else:
                print(f"\n💥 Maximum retries ({max_retries}) reached. Exiting.")
                print("\n🔧 Troubleshooting tips:")
                print("   1. Check if camera is being used by another app")
                print("   2. Try running: python test_video.py")
                print("   3. Restart your computer if issues persist")
                print("   4. Check system requirements in README.md")
                sys.exit(1)
    
    print("\n🏁 Safe server launcher finished")

if __name__ == "__main__":
    main()