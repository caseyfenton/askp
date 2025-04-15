#!/usr/bin/env python3
"""
Entry point script for ASKP CLI.
"""
import sys
import os

# Add the project root to the Python path to ensure imports work correctly
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(project_root))

# DO NOT import anything from askp modules here to avoid circular imports
# Instead, delay all imports until they're needed

if __name__ == "__main__":
    sys.argv[0] = "askp"  # Make help text show "askp" instead of the script name
    
    # Import main function at runtime after sys.path is set up
    # This prevents the "module found in sys.modules" warning
    from askp.cli import main as askp_main
    askp_main()
