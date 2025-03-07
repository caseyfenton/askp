#!/usr/bin/env python3
"""
Project File Consolidation Utility

Functions:
1. Concatenate files and copy to clipboard (for sending to refactoring services)
2. Restore files from clipboard content (after receiving refactored code)

Includes automatic git commit safety before restoration.
"""

import os
import re
import sys
import git
import glob
import fnmatch
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set
from datetime import datetime

# Core configuration
PROJECT_ROOT = Path(os.getcwd())  # Use current directory as project root
EXPECTED_MARKERS = {
    "FILE_PATTERN": r'# === FILE: (.+) ===',
    "PYTHON_SECTION": "# ===== PYTHON SOURCE FILES =====",
    "DOC_SECTION": "# ===== DOCUMENTATION AND CONFIGURATION FILES =====",
    "END_MARKER": "# === END OF PROJECT FILES ==="
}

# Files to prioritize/include when concatenating (defaults)
# Edit these for your specific project
PRIORITY_PY_FILES = [
    "src/askp/cli.py",          # Main CLI implementation
    "tests/test_api_errors.py", # API error tests
    "tests/test_output_formatting.py", # Output formatting tests
    "tests/test_multi_query.py" # Multi-query tests
]

IMPORTANT_DOC_FILES = [
    "README.md",               # Project README
    "requirements.txt",        # Dependencies
    "pyproject.toml"           # Project configuration
]

# Files to exclude (glob patterns)
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".DS_Store",
    "*.pyc",
    ".git",
    "*.egg-info",
    "consolidated_project.txt",
    "*.txt.bak",
    "*.new",
    "deprecated",         # Skip deprecated directory completely
    "screenshots",        # Skip screenshots directory
    "backups",            # Skip backups directory
    "*backup*",           # Skip any backup directories or files
    "*old*",              # Skip old directories or files
    "*.bak",              # Skip backup files
    "*.old",              # Skip old files
    "*.tmp",              # Skip temporary files
    "*copy*",             # Skip files with 'copy' in the name
    "tmp",                # Skip tmp directory
    "*.log",              # Skip log files
    "*.db",               # Skip database files
]

def read_from_clipboard() -> str:
    """Read content from clipboard.
    
    Returns:
        str: Content from clipboard or empty string if failed
    """
    try:
        # For macOS
        import subprocess
        p = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
        content, _ = p.communicate()
        return content.decode('utf-8')
    except Exception as e:
        print(f"Error reading from clipboard: {e}")
        return ""

def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard."""
    try:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        return True
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False

def should_exclude(name: str) -> bool:
    """Check if a file or directory name should be excluded based on patterns."""
    for pattern in EXCLUDE_PATTERNS:
        if '/' in pattern or '\\' in pattern or '**' in pattern:
            # For path patterns, use Path.match which handles ** glob pattern
            try:
                if Path(name).match(pattern):
                    return True
            except:
                # Fall back to fnmatch for invalid path patterns
                if fnmatch.fnmatch(name, pattern):
                    return True
        else:
            # For simple filename patterns, use fnmatch
            if fnmatch.fnmatch(name, pattern):
                return True
    return False

def get_py_files() -> List[str]:
    """Get Python files from the project directory."""
    all_files = []
    
    # First add priority files in order
    for file in PRIORITY_PY_FILES:
        file_path = PROJECT_ROOT / file
        if file_path.exists():
            all_files.append(str(file_path))
        else:
            print(f"Warning: Priority file not found: {file}")
    
    # Then add all other Python files
    for root, _, files in os.walk(PROJECT_ROOT):
        # Skip excluded directories
        if any(fnmatch.fnmatch(root, str(PROJECT_ROOT / pattern)) or 
               fnmatch.fnmatch(os.path.basename(root), pattern) 
               for pattern in EXCLUDE_PATTERNS):
            continue
            
        for file in files:
            # Skip excluded files
            if any(fnmatch.fnmatch(file, pattern) for pattern in EXCLUDE_PATTERNS):
                continue
                
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Skip if already added as a priority file
                if file_path in all_files:
                    continue
                    
                all_files.append(file_path)
    
    return all_files

def get_doc_files() -> List[str]:
    """Get documentation and configuration files."""
    all_files = []
    
    for file in IMPORTANT_DOC_FILES:
        filepath = PROJECT_ROOT / file
        if filepath.is_file():
            all_files.append(str(filepath))
    
    # Add README.md from cases directory if it exists
    cases_readme = PROJECT_ROOT / "cases" / "README.md"
    if cases_readme.is_file():
        all_files.append(str(cases_readme))
    
    # Add global_rules.md
    global_rules = Path(__file__).parent / "../global_rules.md"
    if global_rules.is_file():
        all_files.append(str(global_rules))
    
    return all_files

def create_unified_file(py_files: List[str], doc_files: List[str]) -> str:
    """Create a unified file format containing all project files."""
    result = []
    
    # Add header with refactoring instructions
    result.append("# ===== PROJECT FILE CONSOLIDATION - UNIFIED FILE FORMAT =====")
    result.append(f"# Generated by: {os.path.basename(__file__)}")
    result.append(f"# Contains {len(py_files)} Python files and {len(doc_files)} documentation files")
    result.append("\n# === REFACTORING INSTRUCTIONS ===")
    result.append("""# 
# Please refactor the following project code to improve performance and maintainability. 
# I need your output as ONE continuous block of plain text with no extra code fences, markdown, or formatting inside.
#
# Output everything in this exact format:
# ```
# ===== FILE: [filename] =====
# [entire file content]
# ===== END OF [filename] =====
#
# ===== FILE: [next filename] =====
# [entire file content]
# ===== END OF [next filename] =====
#
# ===== FILE: RESPONSE_NOTES.md =====
# [your notes, suggestions, challenges, and any other communication about the refactoring]
# ===== END OF RESPONSE_NOTES.md =====
# ```
#
# Critical requirements:
# 1. NO additional code fences, markdown headings, or syntax highlighting inside your response
# 2. NO explanations or comments between files - ONLY the file markers and content
# 3. KEEP the exact "===== FILE:" and "===== END OF" format for each file
# 4. Ensure file content is COMPLETE with no truncation
# 5. Include a RESPONSE_NOTES.md file at the end with your suggestions and observations
# 6. End with a single end-code-fence and nothing after
#
# REFACTORING GOALS:
# 
# 1. PERFORMANCE IMPROVEMENT:
#    - Optimize code for faster execution
#    - Reduce memory usage
#    - Minimize tool calls and combine operations where possible
# 
# 2. CODE QUALITY:
#    - Improve code readability and maintainability
#    - Simplify complex logic
#    - Remove redundant code
#    - Follow Vertical Compression Protocol (VCP): minimize vertical space while preserving readability
#    - Group related imports, combine related operations, use single-line functions where appropriate
# 
# 3. ERROR HANDLING:
#    - Implement robust error handling for API interactions
#    - Add graceful fallbacks for failure scenarios
#    - Ensure proper validation of inputs and outputs
#    - Add appropriate retry mechanisms for transient failures
#
# 4. TESTING:
#    - Ensure code remains testable
#    - Consider test coverage when refactoring
#    - Maintain clear function boundaries for effective unit testing
# 
# 5. TECHNICAL CONSTRAINTS:
#    - MUST work with the current project structure
#    - Must maintain existing functionality
#    - Minimize configuration requirements
#    - Preserve docstrings, types, and critical comments
# 
# DO NOT:
# DO NOT: Make dramatic, large-scale architectural changes
# DO NOT: Remove existing functionality
# DO NOT: Change the core API interface
# DO NOT: Exceed 6000 characters per file when possible
#
# The refactored code should be more efficient, readable, and maintainable
# while preserving all current functionality.
#
# NOTE: The global_rules.md file at the end is included for reference ONLY. 
# It contains coding style guidelines and standards. DO NOT refactor this file.
# 
""")
    
    # Documentation files section
    result.append(f"\n{EXPECTED_MARKERS['DOC_SECTION']}\n")
    for file_path in doc_files:
        path = Path(file_path)
        rel_path = path.relative_to(PROJECT_ROOT)
        result.append(f"# === FILE: {rel_path} ===")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                result.append(content)
                if not content.endswith('\n'):
                    result.append("")
        except Exception as e:
            result.append(f"# ERROR: Could not read file {rel_path}: {str(e)}")
        
        result.append("")
    
    # Python files section
    result.append(f"{EXPECTED_MARKERS['PYTHON_SECTION']}\n")
    for file_path in py_files:
        path = Path(file_path)
        rel_path = path.relative_to(PROJECT_ROOT)
        result.append(f"# === FILE: {rel_path} ===")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                result.append(content)
                if not content.endswith('\n'):
                    result.append("")
        except Exception as e:
            result.append(f"# ERROR: Could not read file {rel_path}: {str(e)}")
        
        result.append("")
    
    # Add footer
    result.append(EXPECTED_MARKERS['END_MARKER'])
    
    return "\n".join(result)

def estimate_tokens(file_size: int) -> int:
    """Estimate the number of tokens based on file size.
    
    Args:
        file_size: Size of the file in bytes
        
    Returns:
        Estimated number of tokens (roughly 4 chars per token)
    """
    return int(file_size / 4)  # Approximate token count based on bytes

def format_size(size_bytes: int) -> str:
    """Format file size in a human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.23 KB", "4.56 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def format_file_info(file_path: str, project_root: str) -> str:
    """Format detailed information about a file.
    
    Args:
        file_path: Path to the file
        project_root: Project root directory
        
    Returns:
        Formatted string with file information
    """
    rel_path = os.path.relpath(file_path, project_root)
    size_bytes = os.path.getsize(file_path)
    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    token_estimate = estimate_tokens(size_bytes)
    
    return f"{rel_path} ({format_size(size_bytes)}, ~{token_estimate:,} tokens, modified: {mod_time.strftime('%Y-%m-%d %H:%M')})"

def validate_content(content: str, strict: bool = True) -> Tuple[bool, str, Dict[str, str]]:
    """
    Validate that clipboard content is in the expected unified format.
    Returns (is_valid, error_message, files_dict).
    
    If strict=True, validate that key files are present.
    If strict=False, just check format but don't require specific files.
    """
    # Hallucination checks
    if not content.strip():
        return False, "Clipboard is empty", {}
    
    if EXPECTED_MARKERS['PYTHON_SECTION'] not in content:
        return False, "Missing Python files section marker", {}
    
    if EXPECTED_MARKERS['DOC_SECTION'] not in content:
        return False, "Missing documentation files section marker", {}
    
    if EXPECTED_MARKERS['END_MARKER'] not in content:
        return False, "Missing end marker", {}
    
    # Extract files and check for basic validity
    file_pattern = re.compile(EXPECTED_MARKERS['FILE_PATTERN'])
    files_dict = {}
    current_file = None
    current_content = []
    
    for line in content.splitlines():
        match = file_pattern.match(line)
        if match:
            # Save previous file if we were processing one
            if current_file and current_content:
                files_dict[current_file] = "\n".join(current_content)
                current_content = []
            
            # Start new file
            current_file = match.group(1)
        elif current_file and not line.startswith("# ==="):
            current_content.append(line)
    
    # Save the last file
    if current_file and current_content:
        files_dict[current_file] = "\n".join(current_content)
    
    # Verify we have at least some files
    if not files_dict:
        return False, "No files found in the content", {}
    
    # If strict validation is enabled, check expected Python files
    if strict:
        expected_files = ["src/askp/cli.py", "tests/test_api_errors.py"]
        missing_files = [f for f in expected_files if not any(f in k for k in files_dict.keys())]
        
        if missing_files:
            return False, f"Missing critical files: {', '.join(missing_files)}", {}
    
    return True, "", files_dict

def git_commit_current_state() -> bool:
    """Make a git commit of the current state."""
    try:
        repo = git.Repo(PROJECT_ROOT)
        
        # Check if there are any changes to commit
        if not repo.is_dirty(untracked_files=True):
            print("No changes detected in the git repository.")
            return True
        
        # Add all changes
        repo.git.add('.')
        
        # Commit with message
        commit_message = f"Backup before restoring refactored code ({subprocess.check_output(['date']).decode().strip()})"
        repo.git.commit('-m', commit_message)
        
        print(f"Created git commit: {commit_message}")
        return True
    except Exception as e:
        print(f"Warning: Failed to create git commit: {e}")
        user_input = input("Continue without git commit? (y/n): ")
        return user_input.lower() == 'y'

def restore_files(files_dict: Dict[str, str], dry_run: bool = False) -> List[str]:
    """
    Restore files from the dictionary of {relative_path: content}.
    If dry_run is True, just print what would be done without actually writing.
    """
    restored_files = []
    
    for rel_path, content in files_dict.items():
        target_path = PROJECT_ROOT / rel_path
        
        if dry_run:
            print(f"Would write {len(content)} bytes to {target_path}")
            restored_files.append(str(rel_path))
            continue
        
        # Create parent directories if needed
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Write the file
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Restored: {rel_path}")
        restored_files.append(str(rel_path))
    
    return restored_files

def concatenate_command(custom_files: List[str] = None, doc_files_list: List[str] = None) -> None:
    """Command to concatenate files and copy to clipboard.
    
    Args:
        custom_files: Optional list of specific code files to include (overrides defaults)
        doc_files_list: Optional list of documentation/context files to include (overrides defaults)
    """
    if custom_files or doc_files_list:
        # Use custom file lists instead of scanning directories
        py_files = []
        doc_files = []
        
        if custom_files:
            for file_path in custom_files:
                # Handle both relative and absolute paths
                if os.path.isabs(file_path):
                    absolute_path = file_path
                else:
                    absolute_path = os.path.join(PROJECT_ROOT, file_path)
                    
                if not os.path.exists(absolute_path):
                    print(f"Warning: File not found: {file_path}")
                    continue
                    
                if file_path.endswith('.py'):
                    py_files.append(absolute_path)
                else:
                    # Non-Python files in code-files should still be treated as code files
                    py_files.append(absolute_path)
        
        if doc_files_list:
            for file_path in doc_files_list:
                # Handle both relative and absolute paths
                if os.path.isabs(file_path):
                    absolute_path = file_path
                else:
                    absolute_path = os.path.join(PROJECT_ROOT, file_path)
                    
                if not os.path.exists(absolute_path):
                    print(f"Warning: Documentation file not found: {file_path}")
                    continue
                
                doc_files.append(absolute_path)
                # Remove from py_files if it was added there
                if absolute_path in py_files:
                    py_files.remove(absolute_path)
    else:
        # Use default file discovery process
        py_files = get_py_files()
        doc_files = get_doc_files()
    
    print("\nIncluded Python files:")
    total_py_size = 0
    total_py_tokens = 0
    for f in py_files:
        size_bytes = os.path.getsize(f)
        total_py_size += size_bytes
        total_py_tokens += estimate_tokens(size_bytes)
        print(f"  - {format_file_info(f, PROJECT_ROOT)}")
    
    print("\nIncluded documentation files:")
    total_doc_size = 0
    total_doc_tokens = 0
    for f in doc_files:
        size_bytes = os.path.getsize(f)
        total_doc_size += size_bytes
        total_doc_tokens += estimate_tokens(size_bytes)
        print(f"  - {format_file_info(f, PROJECT_ROOT)}")
    
    if not py_files:
        print("No Python files found.")
        return
    
    total_size = total_py_size + total_doc_size
    total_tokens = total_py_tokens + total_doc_tokens
    
    print(f"\nSummary:")
    print(f"  - Code files: {len(py_files)} files, {format_size(total_py_size)}, ~{total_py_tokens:,} tokens")
    print(f"  - Documentation files: {len(doc_files)} files, {format_size(total_doc_size)}, ~{total_doc_tokens:,} tokens")
    print(f"  - Total: {len(py_files) + len(doc_files)} files, {format_size(total_size)}, ~{total_tokens:,} tokens")
    
    # Estimate API costs based on typical LLM pricing
    cost_per_1k_tokens = 0.002  # $0.002 per 1K tokens, typical for many LLMs
    estimated_cost = (total_tokens / 1000) * cost_per_1k_tokens
    print(f"  - Estimated LLM processing cost: ${estimated_cost:.4f} (based on ${cost_per_1k_tokens:.4f}/1K tokens)")
    
    # Create unified file
    unified_content = create_unified_file(py_files, doc_files)
    
    # Save a temporary copy
    tmp_file = PROJECT_ROOT / "consolidated_project.txt"
    with open(tmp_file, 'w', encoding='utf-8') as f:
        f.write(unified_content)
    
    # Copy to clipboard
    if copy_to_clipboard(unified_content):
        print(f"Content copied to clipboard!")
    else:
        print(f"Failed to copy to clipboard. You can find the content in consolidated_project.txt")
    
    print(f"Total size: {len(unified_content)} bytes ({format_size(len(unified_content))})")

def restore_command(dry_run: bool = False, force: bool = False) -> None:
    """Command to restore files from clipboard."""
    try:
        # Get clipboard content
        print("Reading content from clipboard...")
        clipboard_content = read_from_clipboard()
        
        if not clipboard_content:
            print("Clipboard is empty!")
            return
        
        # Parse content for file sections
        sections = parse_file_sections(clipboard_content, force)
        
        if not sections:
            print("Error: Failed to parse file sections from clipboard content")
            return
        
        # For each file, restore content
        for file_path, content in sections.items():
            print(f"{'Would restore' if dry_run else 'Restoring'} file: {file_path} ({len(content)} bytes)")
            
            if not dry_run:
                # Create parent directories if needed
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                
                # Write content to file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
        
        print(f"\n{len(sections)} files {'would be' if dry_run else 'have been'} restored")
        
        if dry_run:
            print("This was a dry run. No changes were made.")
            print(f"To actually restore files, run: python {os.path.basename(__file__)} restore")
    
    except Exception as e:
        print(f"Error during restore: {e}")
        import traceback
        traceback.print_exc()

def parse_file_sections(content: str, force: bool = False) -> Dict[str, str]:
    """Parse the content into file sections.
    
    Args:
        content: Content to parse
        force: Whether to skip validation checks
        
    Returns:
        Dictionary of file path to content
    """
    sections = {}
    
    # Look for file sections with multiple possible formats
    patterns = [
        r"===== FILE: (.*?) =====\n(.*?)\n===== END OF \1 =====",  # ChatGPT format
        r"# === FILE: (.*?) ===\n(.*?)\n# === END FILE: \1 ===",   # Original format
        r"# FILE: (.*?)\n(.*?)\n# END FILE"                        # Simple format
    ]
    
    # Try all patterns
    for pattern in patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            print(f"Found {len(matches)} file sections using format: {pattern[:20]}...")
            for file_path, file_content in matches:
                # Skip response notes if it's not a real file (unless forced)
                if file_path == "RESPONSE_NOTES.md" and not force:
                    continue
                    
                # Handle the case where file_path might have extra "====="
                file_path = file_path.strip("= ")
                sections[file_path] = file_content
            
            # If we found sections with this pattern, no need to try others
            break
    
    # Show which files we found
    if sections:
        print(f"\nFound {len(sections)} files:")
        for file_path, content in sections.items():
            print(f"  - {file_path}: {len(content)} bytes")

    # Validate important sections if not forced
    if not force and not sections:
        print("Error: Invalid clipboard content: No file sections found")
        print("Use --force to skip strict validation checks.")
        return {}

    return sections

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Project File Consolidation Utility", 
                                     epilog=f"""
Examples:
  # Use default files:
  python {os.path.basename(__file__)} concatenate
  
  # Use custom code files:
  python {os.path.basename(__file__)} concatenate --code-files src/askp/cli.py tests/test_api_errors.py
  
  # Use custom documentation files:
  python {os.path.basename(__file__)} concatenate --doc-files README.md global_rules.md
  
  # Use both custom code and documentation files:
  python {os.path.basename(__file__)} concatenate --code-files src/askp/cli.py --doc-files README.md
  
  # Restore files from clipboard (dry run):
  python {os.path.basename(__file__)} restore --dry-run
  
  # Restore files from clipboard (actual changes):
  python {os.path.basename(__file__)} restore
""", 
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Concatenate command
    concat_parser = subparsers.add_parser("concatenate", aliases=["cat", "concat"], 
                                         help="Concatenate project files and copy to clipboard")
    concat_parser.add_argument("--custom-files", nargs="+", metavar="FILE",
                             help="Optional list of specific files to include (overrides defaults) - DEPRECATED, use --code-files instead")
    concat_parser.add_argument("--code-files", nargs="+", metavar="FILE",
                             help="Optional list of code files to refactor (overrides defaults)")
    concat_parser.add_argument("--doc-files", nargs="+", metavar="FILE",
                             help="Optional list of documentation/context files to include (not for refactoring)")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", 
                                         help="Restore files from clipboard content")
    restore_parser.add_argument("--dry-run", action="store_true", 
                              help="Print what would be done without making changes")
    restore_parser.add_argument("--force", action="store_true",
                              help="Skip strict validation of required files")
    
    args = parser.parse_args()
    
    if args.command in ["concatenate", "cat", "concat"]:
        custom_files = getattr(args, 'custom_files', None) or getattr(args, 'code_files', None)
        doc_files_list = getattr(args, 'doc_files', None)
        concatenate_command(custom_files, doc_files_list)
    elif args.command == "restore":
        restore_command(dry_run=args.dry_run, force=getattr(args, 'force', False))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
