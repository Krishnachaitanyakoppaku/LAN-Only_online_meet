#!/usr/bin/env python3
"""
Main entry point for running the LAN Video Calling Server
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.main_server import main

if __name__ == "__main__":
    main()
