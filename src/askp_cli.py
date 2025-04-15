#!/usr/bin/env python3
"""
Entry point script for ASKP CLI.
"""
import sys
import os

# Add the project root to the Python path to ensure imports work correctly
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(project_root))

# Import the main function directly instead of importing it through askp.__init__
# This prevents the duplicate module warning
from askp.cli import main as askp_main

if __name__ == "__main__":
    sys.argv[0] = "askp"  # Make help text show "askp" instead of the script name
    askp_main()
