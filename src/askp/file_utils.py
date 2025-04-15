#!/usr/bin/env python3
"""
File utilities for ASKP.
Contains functions for path formatting, file stats, and generating cat commands.
"""
import os
from pathlib import Path
from typing import Tuple, List, Dict
from rich import print as rprint

def format_path(filepath: str) -> str:
    """Format a file path to use tilde notation.
Example: /Users/username/CascadeProjects/askp/file.txt -> ~/askp/file.txt"""
    home = str(Path.home())
    if filepath.startswith(home):
        rel = filepath[len(home):]
        if '/CascadeProjects/' in filepath:
            parts = rel.split('/CascadeProjects/', 1)
            if len(parts) > 1:
                proj = parts[1].split('/', 1)
                return f"~/{proj[0]}/{proj[1]}" if len(proj) > 1 else f"~/{proj[0]}"
        return "~" + rel
    return filepath

def get_file_stats(filepath: str) -> Tuple[int, int]:
    """Get file statistics (size in bytes and line count)."""
    if not os.path.exists(filepath):
        return (0, 0)
    try:
        size = os.path.getsize(filepath)
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = sum(1 for _ in f)
        return (size, lines)
    except Exception as e:
        rprint(f"[yellow]Warning: Could not get stats for {filepath}: {e}[/yellow]")
        return (0, 0)

def generate_cat_commands(results: List[dict], output_dir: str = None) -> Dict[str, List[str]]:
    """
    Generate cat commands for viewing result files.
    
    Args:
        results: List of query result dictionaries
        output_dir: Output directory where results are saved
        
    Returns:
        Dictionary of command groups, each containing a list of cat commands
    """
    if not results:
        return {}
    
    cmd_groups = {"View": [], "JSON": [], "All": []}
    
    # Check if results have saved_path metadata
    for i, res in enumerate(results):
        if not res:
            continue
            
        saved_path = res.get("metadata", {}).get("saved_path", "")
        if saved_path and os.path.exists(saved_path):
            rel_path = format_path(saved_path)
            cmd_groups["View"].append(f"cat {rel_path}")
            
            # Check for JSON version
            json_path = saved_path.replace(".md", ".json")
            if os.path.exists(json_path):
                rel_json_path = format_path(json_path)
                cmd_groups["JSON"].append(f"cat {rel_json_path}")
    
    # Add a command for the combined file if it exists
    if output_dir:
        combined_files = [f for f in os.listdir(output_dir) if f.startswith("combined_results_") and f.endswith(".md")]
        for cf in combined_files:
            combined_path = os.path.join(output_dir, cf)
            rel_combined = format_path(combined_path)
            cmd_groups["All"].append(f"cat {rel_combined}")
    
    return cmd_groups