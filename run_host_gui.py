#!/usr/bin/env python3
"""
Entry point for the Host GUI
Starts the host control panel with meeting management capabilities
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.host_gui import main

if __name__ == "__main__":
    main()
