#!/usr/bin/env python3
"""
Main entry point for running ASKP as a module.
This allows running with `python -m askp` during development.
"""

if __name__ == "__main__":
    from .cli import main
    main()
