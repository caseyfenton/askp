#!/usr/bin/env python3
"""File utilities for ASKP CLI."""
import os
from typing import Tuple, List
from rich import print as rprint

def get_file_stats(filepath: str) -> Tuple[int, int]:
    """Get file statistics (size in bytes and line count).
    
    Args:
        filepath: Path to the file
        
    Returns:
        Tuple of (size_bytes, line_count)
    """
    try:
        size_bytes = os.path.getsize(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        return size_bytes, line_count
    except Exception as e:
        rprint(f"[yellow]Warning: Could not get file stats for {filepath}: {e}[/yellow]")
        return 0, 0

def generate_cat_commands(filepath: str, line_count: int, max_lines_per_cmd: int = 200) -> List[str]:
    """Generate efficient cat commands to view a file in chunks if needed.
    
    Args:
        filepath: Path to the file
        line_count: Total number of lines in the file
        max_lines_per_cmd: Maximum lines to show per command
        
    Returns:
        List of cat commands to view the file
    """
    if line_count <= max_lines_per_cmd:
        return [f"cat {filepath}"]
    
    commands = []
    start_line = 1
    while start_line <= line_count:
        end_line = min(start_line + max_lines_per_cmd - 1, line_count)
        commands.append(f"cat {filepath} | sed -n '{start_line},{end_line}p'")
        start_line += max_lines_per_cmd
    
    return commands
