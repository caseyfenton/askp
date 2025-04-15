#!/usr/bin/env python3
"""Script to safely modify cli.py following LFCP."""
import os
import shutil
import sys

def ensure_backup():
    """Ensure we have a backup of the original file."""
    if not os.path.exists('cli.py.bak'):
        shutil.copy2('cli.py', 'cli.py.bak')
        print("Created backup: cli.py.bak")
    else:
        print("Using existing backup: cli.py.bak")

def create_modified_file():
    """Create modified version of cli.py."""
    # Create new file for changes
    shutil.copy2('cli.py', 'cli.py.new')
    print("Created working copy: cli.py.new")
    
    # Read the file
    with open('cli.py.new', 'r') as f:
        lines = f.readlines()
    
    # Modify the file
    modified = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Update imports
        if 'from typing import Optional, List, Dict, Any' in line:
            modified.append('from typing import Optional, List, Dict, Any, Tuple\n')
        
        # Add file_utils import
        elif 'import click' in line:
            modified.append(line)
            modified.append('from .file_utils import get_file_stats, generate_cat_commands\n')
        
        # Update version
        elif 'VERSION = "2.4.1"' in line:
            modified.append('VERSION = "2.4.2"\n')
        
        # Update output_multi_results return type
        elif 'def output_multi_results(results: List[dict], opts: dict) -> None:' in line:
            modified.append('def output_multi_results(results: List[dict], opts: dict) -> str:\n')
        
        # Update early return
        elif '        return' == line.rstrip():
            modified.append('        return ""\n')
        
        # Otherwise keep the line as is
        else:
            modified.append(line)
        
        i += 1
    
    # Write the modified file
    with open('cli.py.new', 'w') as f:
        f.writelines(modified)
    
    print("Initial changes applied to cli.py.new")

def generate_diff():
    """Generate diff between original and modified files."""
    os.system('diff -u cli.py cli.py.new > cli.py.diff')
    print("Generated diff: cli.py.diff")

def main():
    """Main function."""
    print("Following Large File Change Safety Protocol (LFCP)")
    ensure_backup()
    create_modified_file()
    generate_diff()
    print("\nInitial changes complete. Review diff before applying.")
    print("Next steps: Complete implementation of file stats and query tracking.")

if __name__ == "__main__":
    main()
