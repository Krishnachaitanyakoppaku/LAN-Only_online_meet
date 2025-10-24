#!/usr/bin/env python3
"""
Debug client initialization step by step
"""

def debug_client():
    """Debug client initialization"""
    try:
        print("Step 1: Importing client module...")
        from client import LANCommunicationClient
        print("✅ Import successful")
        
        print("Step 2: Checking if test_connection method exists in class...")
        if hasattr(LANCommunicationClient, 'test_connection'):
            print("✅ test_connection method found in class")
        else:
            print("❌ test_connection method NOT found in class")
            
        print("Step 3: Checking method resolution order...")
        methods = [method for method in dir(LANCommunicationClient) if not method.startswith('_')]
        print(f"Available methods: {len(methods)}")
        
        if 'test_connection' in methods:
            print("✅ test_connection in methods list")
        else:
            print("❌ test_connection NOT in methods list")
            
        print("Step 4: Trying to create instance without GUI...")
        # We'll monkey patch to skip GUI setup
        original_setup_gui = LANCommunicationClient.setup_gui
        LANCommunicationClient.setup_gui = lambda self: None
        
        client = LANCommunicationClient()
        print("✅ Instance created without GUI")
        
        if hasattr(client, 'test_connection'):
            print("✅ test_connection method accessible on instance")
        else:
            print("❌ test_connection method NOT accessible on instance")
            
        # Restore original method
        LANCommunicationClient.setup_gui = original_setup_gui
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_client()