#!/usr/bin/env python3
"""
BGRun integration for ASKP.

Simple integration that notifies BGRun when ASKP queries complete,
allowing results to appear directly in the .windsurfrules file.
"""
import os
import subprocess
from pathlib import Path


def notify_bgrun(name, command):
    """
    Notify BGRun with a command.
    
    This is a simplified approach that uses the system's bgrun command
    without complex path detection.
    
    Args:
        name: Task name
        command: Command to run
        
    Returns:
        bool: True if the notification was sent, False otherwise
    """
    try:
        subprocess.run(["bgrun", "--name", name, command], 
                      check=False, capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        # Fallback to direct command if bgrun not in PATH
        try:
            home = os.path.expanduser("~")
            bgrun_path = os.path.join(home, "bin", "bgrun")
            if os.path.exists(bgrun_path) and os.access(bgrun_path, os.X_OK):
                subprocess.run([bgrun_path, "--name", name, command], 
                              check=False, capture_output=True)
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
    return False


def update_askp_results_widget():
    """
    Update the ASKP results widget to show recent query results.
    
    Returns:
        bool: True if the widget was updated successfully, False otherwise
    """
    # Get the path to the widget script
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    widget_script = os.path.join(script_dir, "widgets", "askp_results_widget.sh")
    
    # Make sure the script exists and is executable
    if not os.path.exists(widget_script):
        return False
    
    if not os.access(widget_script, os.X_OK):
        os.chmod(widget_script, 0o755)  # Make executable if it isn't already
    
    # Run the widget script to update the widget
    try:
        subprocess.run([widget_script], check=False, capture_output=True)
        
        # Register the widget if it's not already registered
        try:
            subprocess.run(["bgrun", "--widget", "askp-results", "--interval", "5m", widget_script], 
                          check=False, capture_output=True)
        except:
            # If bgrun isn't in PATH, try to find it
            home = os.path.expanduser("~")
            bgrun_path = os.path.join(home, "bin", "bgrun")
            if os.path.exists(bgrun_path) and os.access(bgrun_path, os.X_OK):
                subprocess.run([bgrun_path, "--widget", "askp-results", "--interval", "5m", widget_script], 
                               check=False, capture_output=True)
        return True
    except:
        return False


def notify_query_completed(query, result_file, model="", tokens=0, cost=0.0):
    """
    Notify BGRun that an ASKP query has completed.
    
    Args:
        query (str): The query string
        result_file (str): Path to the result file
        model (str): Model used for the query
        tokens (int): Number of tokens used
        cost (float): Cost of the query
    
    Returns:
        bool: True if notification was successful, False otherwise
    """
    # Truncate query if too long
    query_display = query[:50] + "..." if len(query) > 50 else query
    
    # Get absolute path for result file
    abs_path = os.path.abspath(result_file)
    
    # Create message with file URL and metadata
    message = (
        f"ASKP query completed: \"{query_display}\" | "
        f"Model: {model} | Tokens: {tokens} | Cost: ${cost:.4f} | "
        f"Results: file://{abs_path}"
    )
    
    # Update the widget after notifying
    update_askp_results_widget()
    
    return notify_bgrun("askp-complete", f"echo '{message}'")


def notify_multi_query_completed(num_queries, combined_file, total_tokens=0, total_cost=0.0):
    """
    Notify BGRun that multiple ASKP queries have completed.
    
    Args:
        num_queries (int): Number of queries processed
        combined_file (str): Path to the combined results file
        total_tokens (int): Total tokens used across all queries
        total_cost (float): Total cost across all queries
    
    Returns:
        bool: True if notification was successful, False otherwise
    """
    # Get absolute path for result file
    abs_path = os.path.abspath(combined_file)
    
    # Create message with file URL and metadata
    message = (
        f"ASKP completed {num_queries} queries | "
        f"Tokens: {total_tokens} | Cost: ${total_cost:.4f} | "
        f"Results: file://{abs_path}"
    )
    
    # Update the widget after notifying
    update_askp_results_widget()
    
    return notify_bgrun("askp-multi-complete", f"echo '{message}'")


def create_widget(name, content, interval=None):
    """
    Create or update a BGRun widget.
    
    Args:
        name (str): Widget name
        content (str): Widget content
        interval (str, optional): Update interval (e.g., "5m", "30s")
    
    Returns:
        bool: True if widget creation was successful, False otherwise
    """
    command = ["bgrun", "--widget", name]
    if interval:
        command.extend(["--interval", interval])
    command.append(f"echo '{content}'")
    
    try:
        subprocess.run(command, check=False, capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        # Fallback to direct command
        try:
            home = os.path.expanduser("~")
            bgrun_path = os.path.join(home, "bin", "bgrun")
            if os.path.exists(bgrun_path) and os.access(bgrun_path, os.X_OK):
                command[0] = bgrun_path
                subprocess.run(command, check=False, capture_output=True)
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
    return False


def update_askp_status_widget(num_queries_today=0, total_cost_today=0.0, average_time=0.0):
    """
    Update the ASKP status widget in .windsurfrules
    
    Args:
        num_queries_today (int): Number of queries run today
        total_cost_today (float): Total cost of queries today
        average_time (float): Average query time in seconds
    
    Returns:
        bool: True if widget update was successful, False otherwise
    """
    content = (
        "### ASKP Status\n"
        f"Queries today: {num_queries_today}\n"
        f"Total cost: ${total_cost_today:.4f}\n"
        f"Avg time: {average_time:.1f}s"
    )
    
    return create_widget("askp-status", content, interval="1h")
