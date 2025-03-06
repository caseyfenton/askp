#!/usr/bin/env python3
"""Backfill cost tracking data for ASKD CLI from existing Perplexity results."""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any

from askp.cost_tracking import COST_LOG_DIR, COST_LOG_FILE, ensure_log_dir
from askp.models import MODEL_REGISTRY
from askp.utils import detect_model

# Common project root indicators (lowercase)
PROJECT_ROOTS = frozenset(["projects", "cascadeprojects", "workspace", "repos", "code"])
# Common non-project directories (lowercase)
NON_PROJECT_DIRS = frozenset(["src", "results", "temp", "logs", "data", "tests", "perplexity", "ask", "askd", "old"])

def get_project_from_path(path: str) -> Optional[str]:
    """Extract project name from file path."""
    path = os.path.abspath(path)
    parts = path.split(os.sep)
    
    # Check for working_directory marker files
    dir_path = os.path.dirname(path)
    while dir_path and dir_path != '/':
        wd_marker = os.path.join(dir_path, '.working_directory')
        if os.path.exists(wd_marker):
            try:
                with open(wd_marker) as f: return f.read().strip()
            except: pass
        dir_path = os.path.dirname(dir_path)
    
    # Check for project root indicators
    for i, part in enumerate(parts):
        if part.lower() in PROJECT_ROOTS and i + 1 < len(parts):
            next_part = parts[i + 1].lower()
            if next_part not in NON_PROJECT_DIRS: return parts[i + 1]
    
    # Check for src/project_name pattern
    try:
        src_idx = parts.index('src')
        if src_idx > 0: return parts[src_idx - 1]
    except ValueError: pass
    
    # Check for results directory pattern
    for i, part in enumerate(parts):
        if "results" in part.lower() and i > 0:
            prev_part = parts[i - 1].lower()
            if prev_part not in NON_PROJECT_DIRS: return parts[i - 1]
    
    return None

def estimate_token_count(content: str) -> int:
    """Estimate token count from content."""
    # Count code-like characters that often become separate tokens
    code_chars = len(re.findall(r'[{}()\[\]<>+=\-*/\\|;:~`@#$%^&]', content))
    total_chars = len(content)
    
    # Determine chars per token ratio based on code density
    code_ratio = code_chars / total_chars if total_chars > 0 else 0
    char_per_token = 3.5 if code_ratio > 0.05 else 4.0
    
    # Calculate token count
    token_count = int(total_chars / char_per_token) + code_chars
    return max(1, token_count)

def is_perplexity_result(filepath: str, content: str) -> bool:
    """Check if a file is a valid perplexity result."""
    filename = os.path.basename(filepath)
    
    # Skip citation files - we'll process them with their main files
    if filename.endswith('_citations.md'): return False
        
    # Check filename patterns
    patterns = [
        r"perplexity_\d{8}_\d{6}_.+\.(txt|md)$",
        r"perplexity_[a-zA-Z0-9_]+\.(txt|md)$",
        r"[a-zA-Z_]+_\d{8}_\d{6}_[a-zA-Z_]+\.(txt|md)$",
        r"[a-zA-Z_]+_\d{8}_\d{6}\.(txt|md)$"
    ]
    
    if not any(re.match(p, filename) for p in patterns): return False
    if len(content) < 50: return False
        
    # Check for citations file
    has_citations = os.path.exists(filepath.replace('.md', '_citations.md'))
    if has_citations: return True
    
    # Check content markers
    markers = ["Here are", "Based on", "According to", "Let me", "I'll", "To answer", 
              "I found", "The answer", "References:", "Sources:", "http://", "https://"]
    return any(marker in content for marker in markers)

def get_timestamp_from_file(filepath: str) -> str:
    """Extract timestamp from filename or use file creation time."""
    filename = os.path.basename(filepath)
    
    # Try to extract timestamp from filename
    timestamp_match = re.search(r'_(\d{8}_\d{6})(?:_|\.|$)', filename)
    if timestamp_match:
        try:
            dt = datetime.strptime(timestamp_match.group(1), '%Y%m%d_%H%M%S')
            return dt.isoformat()
        except ValueError: pass
    
    # Fallback to file creation time
    return datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()

def process_file_with_citations(filepath: str) -> str:
    """Process a file and its citations if they exist."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for citations file
        citations_path = filepath.replace('.md', '_citations.md')
        if os.path.exists(citations_path):
            try:
                with open(citations_path, 'r', encoding='utf-8') as f:
                    content += "\n\nCitations:\n" + f.read()
            except Exception as e:
                print(f"Warning: Could not read citations file {citations_path}: {str(e)}")
                
        return content
    except Exception as e:
        print(f"Error processing file {filepath}: {str(e)}")
        return ""

def find_and_process_results(base_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Find and process all perplexity results in specified directory."""
    base_dir = base_dir or os.path.expanduser("~/CascadeProjects")
    print(f"Searching for results in {base_dir}...")
    
    all_entries = []
    total_files_processed = 0
    total_cost = 0.0
    processed_files = set()  # Track processed files to avoid duplicates
    current_folder = None
    unknown_project_files = []  # Track files where project couldn't be determined
    skip_dirs = frozenset(['node_modules', '.git', '__pycache__', 'venv', '.env'])
    
    def format_cost(cost: float) -> str:
        """Format cost with appropriate decimal places."""
        return f"${cost:.4f}" if cost < 0.01 else f"${cost:.2f}"
    
    for root, _, files in os.walk(base_dir):
        # Skip directories we know won't have results
        if any(skip in root for skip in skip_dirs): continue
        
        result_files = []
        
        # First pass: identify potential result files
        for file in files:
            if file.endswith(('.txt', '.md', '.json', '.jsonl')):
                filepath = os.path.join(root, file)
                if filepath in processed_files or file.endswith('_citations.md'): continue
                    
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if is_perplexity_result(filepath, content):
                        result_files.append((filepath, content))
                except UnicodeDecodeError: continue
                except Exception as e:
                    if any(term in filepath.lower() for term in ['perplexity', 'result', 'query']):
                        print(f"Error reading file {os.path.basename(filepath)}: {str(e)}")
        
        if result_files:
            # Print double newline before new folder results
            if current_folder != root:
                if current_folder is not None: print("\n")
                current_folder = root
                print(f"Found {len(result_files)} result files in {os.path.relpath(root, base_dir)}")
            
            entries = []
            dir_cost = 0.0
            files_processed = 0
            
            for filepath, content in result_files:
                try:
                    # Process the result file
                    model = detect_model(content, filepath)
                    if not model: continue
                        
                    token_count = estimate_token_count(content)
                    cost = (token_count / 1_000_000) * MODEL_REGISTRY[model]["cost_per_million"]
                    
                    project = get_project_from_path(filepath)
                    if project is None:
                        unknown_project_files.append((filepath, cost))
                        project = "unknown"  # Fallback for cost tracking
                    
                    entry = {
                        "timestamp": get_timestamp_from_file(filepath),
                        "file": filepath,
                        "model": MODEL_REGISTRY[model]["id"],
                        "token_count": token_count,
                        "cost": cost,
                        "project": project,
                        "working_directory": os.path.dirname(filepath),
                        "source": "perplexity"
                    }
                    
                    entries.append(entry)
                    all_entries.append(entry)
                    processed_files.add(filepath)
                    dir_cost += cost
                    
                    files_processed += 1
                    if len(result_files) > 20 and files_processed % 20 == 0:
                        print(f"Progress: {files_processed}/{len(result_files)} files ({format_cost(dir_cost)} cost so far)")
                except Exception as e:
                    print(f"Error processing {os.path.basename(filepath)}: {str(e)}")
                    continue
            
            if entries:
                print(f"\nFinished processing {os.path.relpath(root, base_dir)}:")
                print(f"- Files processed: {files_processed}")
                print(f"- Cost entries found: {files_processed}")
                print(f"- Total cost: {format_cost(dir_cost)}")
                
                total_files_processed += files_processed
                total_cost += dir_cost
    
    if total_files_processed == 0:
        print("\nNo Perplexity result files found.")
        return []
    
    print(f"\nOverall Summary:")
    print(f"- Total files processed: {total_files_processed}")
    print(f"- Total cost entries: {len(all_entries)}")
    print(f"- Total cost: ${total_cost:.2f}")
    
    if unknown_project_files:
        print("\nWarning: Could not determine project for some files:")
        for filepath, cost in unknown_project_files[:5]:
            print(f"  - {os.path.relpath(filepath, base_dir)} (cost: {format_cost(cost)})")
        if len(unknown_project_files) > 5:
            print(f"  ... and {len(unknown_project_files) - 5} more files")
        print("\nTo fix this, you can:")
        print("1. Create a .working_directory file in the project root with the project name")
        print("2. Move results to a more standard project directory structure")
    
    return all_entries

def write_cost_data(entries: List[Dict], mode: str = 'a') -> None:
    """Write cost data entries to the log file."""
    if not entries:
        print("No entries to write")
        return
        
    try:
        ensure_log_dir()
        
        print("\nSorting entries by timestamp...")
        entries.sort(key=lambda x: x["timestamp"])
        
        # Check for duplicates
        existing_entries = set()
        if os.path.exists(COST_LOG_FILE):
            with open(COST_LOG_FILE, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        key = f"{entry['timestamp']}:{entry.get('file', '')}"
                        existing_entries.add(key)
                    except json.JSONDecodeError: continue
        
        print("Writing new entries...")
        new_count = 0
        total_cost = 0.0
        with open(COST_LOG_FILE, mode) as f:
            for entry in entries:
                key = f"{entry['timestamp']}:{entry.get('file', '')}"
                if key not in existing_entries:
                    f.write(json.dumps(entry) + "\n")
                    new_count += 1
                    total_cost += entry["cost"]
        
        print(f"\nResults:")
        print(f"- Added {new_count} new entries")
        print(f"- Skipped {len(entries) - new_count} duplicate entries")
        print(f"- Total cost of new entries: ${total_cost:.2f}")
        
    except Exception as e:
        print(f"Error writing to cost log: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill cost tracking data from Perplexity results")
    parser.add_argument("--directory", "-d", type=str, help="Directory to search (default: ~/CascadeProjects)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing cost log")
    parser.add_argument("--quick", dest="quick_extract", action="store_true", help="Use quick extraction")
    
    args = parser.parse_args()
    directory = os.path.expanduser(args.directory) if args.directory else os.path.expanduser("~/CascadeProjects")
    
    try:
        entries = find_and_process_results(directory)
        if entries:
            write_cost_data(entries, mode='a' if not args.overwrite else 'w')
    except Exception as e:
        print(f"Error during backfill: {str(e)}")
        import traceback
        print(traceback.format_exc())
        exit(1)
