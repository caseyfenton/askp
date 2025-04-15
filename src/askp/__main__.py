#!/usr/bin/env python3
"""
Main entry point for ASKP when run as a module.
"""
import sys

if __name__ == "__main__":
    # Import inside the if block to avoid circular imports
    # This approach prevents the "module found in sys.modules" warning
    from askp.cli import main
    sys.argv[0] = "askp"  # Make help text show "askp" instead of the script name
    main()
