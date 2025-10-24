#!/usr/bin/env python3
"""
Test if method exists by reading the source directly
"""

def test_method_in_source():
    """Test if method exists in source"""
    with open('client.py', 'r') as f:
        content = f.read()
    
    # Count occurrences of test_connection
    count = content.count('def test_connection')
    print(f"Found {count} definitions of 'def test_connection'")
    
    # Find the line numbers
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'def test_connection' in line:
            print(f"Line {i+1}: {line.strip()}")
            # Check indentation
            indent = len(line) - len(line.lstrip())
            print(f"  Indentation: {indent} spaces")
            
            # Check if it's inside a class (previous lines should have class definition)
            for j in range(max(0, i-50), i):
                if lines[j].strip().startswith('class ') and not lines[j].strip().startswith('class '):
                    print(f"  Found class at line {j+1}: {lines[j].strip()}")
                    break
    
    # Try to import and check
    try:
        import importlib
        import client
        importlib.reload(client)
        
        cls = client.LANCommunicationClient
        print(f"Class methods: {[m for m in dir(cls) if not m.startswith('_')]}")
        
        if hasattr(cls, 'test_connection'):
            print("✅ Method found in class")
        else:
            print("❌ Method NOT found in class")
            
    except Exception as e:
        print(f"Error importing: {e}")

if __name__ == "__main__":
    test_method_in_source()