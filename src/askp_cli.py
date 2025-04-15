#!/usr/bin/env python3
"""
Entry point script for ASKP CLI.
"""
import sys
import os

# Add the project root to the Python path to ensure imports work correctly
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(project_root))

from askp.cli import main

if __name__ == "__main__":
    main()
