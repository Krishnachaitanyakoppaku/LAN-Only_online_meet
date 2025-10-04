#!/usr/bin/env python3
"""
Entry point for the Host Server (Command Line)
Starts the server in host mode with meeting control capabilities
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.host_server import main

if __name__ == "__main__":
    main()
