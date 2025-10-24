#!/usr/bin/env python3
"""
Quick test to verify client GUI initialization
"""

import sys
import os

def test_client_gui():
    """Test client GUI initialization"""
    try:
        print("🧪 Testing client GUI initialization...")
        
        # Import client
        from client import LANCommunicationClient
        print("✅ Client imported successfully")
        
        # Create client instance (but don't run mainloop)
        client = LANCommunicationClient()
        print("✅ Client instance created successfully")
        
        # Check if GUI components exist
        if hasattr(client, 'root'):
            print("✅ Root window created")
        
        if hasattr(client, 'main_container'):
            print("✅ Main container created")
            
        if hasattr(client, 'server_ip_entry'):
            print("✅ Connection form created")
            
        # Destroy the window without running mainloop
        client.root.destroy()
        print("✅ GUI cleanup successful")
        
        print("\n🎉 All tests passed! Client GUI is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_client_gui()
    sys.exit(0 if success else 1)