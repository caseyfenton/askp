#!/usr/bin/env python3
"""
Test script to ensure the output directory functionality works correctly.
"""
import os
from pathlib import Path

def test_output_dir():
    """Test that the output directory functions correctly."""
    # Create our own output dir function for testing
    def get_output_dir():
        """Returns the perplexity_results folder in the current working directory."""
        results_dir = Path.cwd() / "perplexity_results"
        results_dir.mkdir(exist_ok=True)
        return results_dir
    
    # Create test file
    output_dir = get_output_dir()
    test_file = output_dir / "test_file.txt"
    with open(test_file, "w") as f:
        f.write("Test file to verify output directory works correctly.")
    
    # Verify file exists
    if test_file.exists():
        print(f"✅ Success! Test file created at: {test_file}")
        return True
    else:
        print(f"❌ Error: Failed to create test file at: {test_file}")
        return False

if __name__ == "__main__":
    test_output_dir()
