#!/usr/bin/env python3
"""
ASKR - Ask Results

A utility for viewing and formatting Perplexity results for LLMs.
Shows recent results and formats them optimally for LLM consumption.
"""
import os
import sys
import glob
import time
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel


def get_output_dir() -> str:
    """Get the directory where ASKP results are stored."""
    home = os.path.expanduser("~")
    return os.path.join(home, "perplexity_results")


def find_recent_results(minutes: int = 10, count: int = 10, 
                        output_dir: Optional[str] = None) -> List[Dict]:
    """
    Find recent ASKP results.
    
    Args:
        minutes: Find results from the last N minutes
        count: Maximum number of results to return
        output_dir: Directory to search (defaults to standard ASKP results dir)
        
    Returns:
        List of result file info (path, creation time, size)
    """
    if not output_dir:
        output_dir = get_output_dir()
    
    if not os.path.exists(output_dir):
        return []
    
    # Get all markdown and json files in the directory
    files = []
    for ext in ["*.md", "*.json", "*.txt"]:
        files.extend(glob.glob(os.path.join(output_dir, ext)))
    
    # Filter by creation time
    cutoff_time = time.time() - (minutes * 60)
    recent_files = []
    
    for file_path in files:
        stat = os.stat(file_path)
        creation_time = stat.st_ctime
        
        if creation_time >= cutoff_time:
            recent_files.append({
                "path": file_path,
                "ctime": creation_time,
                "ctime_str": datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S"),
                "size": stat.st_size,
                "size_str": format_size(stat.st_size),
                "name": os.path.basename(file_path)
            })
    
    # Sort by creation time (newest first) and limit to count
    recent_files.sort(key=lambda x: x["ctime"], reverse=True)
    return recent_files[:count]


def format_size(size_bytes):
    """Format byte size with appropriate unit."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def strip_metadata(content: str) -> str:
    """
    Strip metadata and formatting to make content more LLM-friendly.
    
    Removes:
    - Token counts, costs, and other statistics
    - File information sections
    - Viewing commands
    - Reduces excessive formatting
    
    Args:
        content: Original file content
        
    Returns:
        Stripped content optimized for LLM consumption
    """
    # Skip processing if content is too short
    if len(content) < 100:
        return content
        
    lines = content.split('\n')
    result_lines = []
    skip_section = False
    
    for line in lines:
        # Skip metadata sections
        if any(marker in line.lower() for marker in ["=== file information ===", "=== viewing commands ===", 
                                                    "## summary", "tokens |", "results saved to:"]):
            skip_section = True
            continue
            
        if skip_section and line.strip() and not line.startswith('#'):
            if any(marker in line.lower() for marker in ["tokens", "summary", "total"]):
                continue
            skip_section = False
            
        # Skip horizontal separators
        if line.strip() and line.strip()[0] * len(line.strip()) == line.strip():
            continue
            
        result_lines.append(line)
    
    return '\n'.join(result_lines)


def create_llm_payload(files: List[Dict], max_lines: int = 200) -> str:
    """
    Create a combined payload of file contents optimized for LLM consumption.
    
    Args:
        files: List of file info dictionaries
        max_lines: Maximum number of lines to include
        
    Returns:
        Combined content string
    """
    combined_content = []
    total_lines = 0
    
    for file_info in files:
        try:
            with open(file_info["path"], 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Strip metadata to make it more LLM-friendly
            cleaned_content = strip_metadata(content)
            
            # Add file header
            combined_content.append(f"--- {file_info['name']} ---\n")
            
            # Add content
            lines = cleaned_content.split('\n')
            if total_lines + len(lines) > max_lines:
                # Only add as many lines as we can fit
                available_lines = max_lines - total_lines
                if available_lines > 10:  # Only add if we can include at least 10 lines
                    combined_content.append('\n'.join(lines[:available_lines]))
                    combined_content.append("\n[Content truncated due to length]")
                    total_lines = max_lines
                    break
            else:
                combined_content.append(cleaned_content)
                total_lines += len(lines)
                
        except Exception as e:
            combined_content.append(f"Error reading {file_info['name']}: {str(e)}")
    
    return '\n\n'.join(combined_content)


def create_widget_content(files: List[Dict]) -> str:
    """
    Create content for the ASKP results widget.
    
    Args:
        files: List of recent result files
        
    Returns:
        Formatted widget content
    """
    if not files:
        return "No recent ASKP results"
        
    lines = ["### Recent ASKP Results"]
    
    for i, file in enumerate(files[:5]):  # Show up to 5 results in widget
        created = datetime.fromtimestamp(file["ctime"]).strftime("%H:%M:%S")
        lines.append(f"{i+1}. {file['name']} ({created}) {file['size_str']}")
        
    if len(files) > 5:
        lines.append(f"+ {len(files) - 5} more results")
        
    return "\n".join(lines)


def update_bgrun_widget(files: List[Dict]) -> bool:
    """
    Update the BGRun widget with recent ASKP results.
    
    Args:
        files: List of recent result files
        
    Returns:
        True if widget was updated successfully, False otherwise
    """
    try:
        widget_content = create_widget_content(files)
        
        # Try to find bgrun in PATH
        bgrun_path = os.popen("which bgrun").read().strip()
        
        # If not found, check in common locations
        if not bgrun_path:
            potential_paths = [
                os.path.expanduser("~/bin/bgrun"),
                "/usr/local/bin/bgrun",
                os.path.expanduser("~/CascadeProjects/bgrun/bgrun")
            ]
            
            for path in potential_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    bgrun_path = path
                    break
        
        if bgrun_path:
            os.system(f"{bgrun_path} --widget askp-results --interval 3m \"echo '{widget_content}'\"")
            return True
    except Exception:
        pass
        
    return False


def display_results_table(files: List[Dict]):
    """Display a table of recent ASKP results."""
    console = Console()
    
    if not files:
        console.print("[yellow]No recent ASKP results found[/yellow]")
        return
    
    table = Table(title="Recent ASKP Results")
    table.add_column("#", style="dim")
    table.add_column("File", style="blue")
    table.add_column("Created", style="green")
    table.add_column("Size", style="cyan", justify="right")
    
    for i, file in enumerate(files):
        table.add_row(
            str(i+1),
            file["name"],
            file["ctime_str"],
            file["size_str"]
        )
    
    console.print(table)
    
    # Show command examples
    console.print("\nCommands:")
    console.print(f"  [green]askr show 1[/green]         # Show content of result #1")
    console.print(f"  [green]askr show 1-3[/green]       # Show content of results #1 through #3")
    console.print(f"  [green]askr llm 1-3[/green]        # Show LLM-optimized content of results #1-#3")


def show_file_content(file_path: str, llm_mode: bool = False):
    """Display the content of a result file."""
    console = Console()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if llm_mode:
            content = strip_metadata(content)
            
        # Auto-detect format
        if file_path.endswith('.md'):
            console.print(Markdown(content))
        else:
            console.print(content)
            
    except Exception as e:
        console.print(f"[red]Error reading file: {str(e)}[/red]")


def main():
    """Main entry point for ASKR."""
    parser = argparse.ArgumentParser(description="ASKR - View Perplexity Results")
    
    # Main commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List recent results")
    list_parser.add_argument("-m", "--minutes", type=int, default=10,
                            help="Show results from last N minutes (default: 10)")
    list_parser.add_argument("-c", "--count", type=int, default=10,
                            help="Maximum number of results to show (default: 10)")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show content of specific results")
    show_parser.add_argument("index", help="Index or range (e.g., 1 or 1-3)")
    
    # LLM command
    llm_parser = subparsers.add_parser("llm", help="Get LLM-optimized content")
    llm_parser.add_argument("index", help="Index or range (e.g., 1 or 1-3)")
    llm_parser.add_argument("-l", "--lines", type=int, default=200,
                          help="Maximum lines to include (default: 200)")
    
    # Widget command
    widget_parser = subparsers.add_parser("widget", help="Update BGRun widget with recent results")
    
    args = parser.parse_args()
    
    # Default to list if no command specified
    if not args.command:
        args.command = "list"
        args.minutes = 10
        args.count = 10
    
    # Find recent results
    recent_files = find_recent_results(
        minutes=args.minutes if hasattr(args, 'minutes') else 10,
        count=args.count if hasattr(args, 'count') else 10
    )
    
    # Handle commands
    if args.command == "list":
        display_results_table(recent_files)
        
    elif args.command == "show" and recent_files:
        try:
            # Parse index or range
            if "-" in args.index:
                start, end = map(int, args.index.split("-"))
                indexes = range(start-1, end)
            else:
                indexes = [int(args.index) - 1]
                
            for idx in indexes:
                if 0 <= idx < len(recent_files):
                    file_path = recent_files[idx]["path"]
                    print(f"\n=== {recent_files[idx]['name']} ===\n")
                    show_file_content(file_path)
                    print()
                else:
                    print(f"Index {idx+1} out of range")
        except ValueError:
            print("Invalid index format. Use a number (e.g., 1) or range (e.g., 1-3)")
            
    elif args.command == "llm" and recent_files:
        try:
            # Parse index or range
            if "-" in args.index:
                start, end = map(int, args.index.split("-"))
                indexes = range(start-1, min(end, len(recent_files)))
            else:
                indexes = [int(args.index) - 1]
                
            # Filter files to selected indexes
            selected_files = [recent_files[idx] for idx in indexes if 0 <= idx < len(recent_files)]
            
            if selected_files:
                # Create LLM payload
                llm_content = create_llm_payload(
                    selected_files, 
                    max_lines=args.lines if hasattr(args, 'lines') else 200
                )
                print(llm_content)
            else:
                print("No valid files selected")
                
        except ValueError:
            print("Invalid index format. Use a number (e.g., 1) or range (e.g., 1-3)")
            
    elif args.command == "widget":
        success = update_bgrun_widget(recent_files)
        if success:
            print("ASKP results widget updated successfully")
        else:
            print("Failed to update ASKP results widget")
    
    else:
        if not recent_files:
            print("No recent ASKP results found")


if __name__ == "__main__":
    main()
