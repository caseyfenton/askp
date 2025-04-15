#!/usr/bin/env python3
"""Script to safely modify cli.py following the Large File Change Safety Protocol (LFCP)."""
import os
import shutil
import re
import sys

def ensure_backup(filename):
    """Ensure a backup of the file exists."""
    backup = filename + '.bak'
    if not os.path.exists(backup):
        shutil.copy2(filename, backup)
        print(f"Created backup: {backup}")
    else:
        print(f"Using existing backup: {backup}")

def create_new_file(filename):
    """Create a new file for modifications."""
    new_file = filename + '.new'
    shutil.copy2(filename, new_file)
    print(f"Created new file for modifications: {new_file}")
    return new_file

def modify_file(filename):
    """Make necessary modifications to the file."""
    with open(filename, 'r') as f:
        content = f.read()
    
    # 1. Update imports
    content = re.sub(
        r'from typing import Optional, List, Dict, Any',
        'from typing import Optional, List, Dict, Any, Tuple',
        content
    )
    
    # 2. Add file_utils import
    content = re.sub(
        r'import click',
        'import click\nfrom .file_utils import get_file_stats, generate_cat_commands',
        content
    )
    
    # 3. Update version
    content = re.sub(r'VERSION = "2.4.1"', 'VERSION = "2.4.2"', content)
    
    # 4. Update output_multi_results return type
    content = re.sub(
        r'def output_multi_results\(results: List\[dict\], opts: dict\) -> None:',
        'def output_multi_results(results: List[dict], opts: dict) -> str:',
        content
    )
    
    # 5. Add documentation to function
    content = re.sub(
        r'    """Combine and output results from multiple queries to a file.\n\n    Args:\n        results: List of result dictionaries.\n        opts: Options dictionary.\n    """',
        '    """Combine and output results from multiple queries to a file.\n\n    Args:\n        results: List of result dictionaries.\n        opts: Options dictionary.\n        \n    Returns:\n        Path to the output file.\n    """',
        content
    )
    
    # 6. Change early return
    content = re.sub(
        r'    if not results:\n        return',
        '    if not results:\n        return ""',
        content
    )
    
    # 7. Add expanded query info for filenames
    content = re.sub(
        r'    ts = datetime.now\(\).strftime\("%Y%m%d_%H%M%S"\)\n    fmt = opts.get\("format", "markdown"\)\n    ext = "md" if fmt == "markdown" else \("json" if fmt == "json" else "txt"\)',
        '    # Get expanded queries info if available\n    expanded_info = ""\n    if opts.get("expand", 0) > 0 and opts.get("original_queries") and opts.get("expanded_queries"):\n        orig_count = len(opts.get("original_queries", []))\n        expanded_count = len(opts.get("expanded_queries", [])) - orig_count\n        if expanded_count > 0:\n            expanded_info = f"_expanded_{expanded_count}"\n    \n    ts = datetime.now().strftime("%Y%m%d_%H%M%S")\n    fmt = opts.get("format", "markdown")\n    ext = "md" if fmt == "markdown" else ("json" if fmt == "json" else "txt")',
        content
    )
    
    # 8. Update filenames
    content = re.sub(
        r'fname = f"deep_research_{s_query}_{ts}.{ext}"',
        'fname = f"deep_research_{s_query}{expanded_info}_{ts}.{ext}"',
        content
    )
    content = re.sub(
        r'fname = f"query_result_{s_query}_{ts}.{ext}"',
        'fname = f"query_result_{s_query}{expanded_info}_{ts}.{ext}"',
        content
    )
    content = re.sub(
        r'fname = f"multi_query_results_{ts}.{ext}"',
        'fname = f"multi_query_results{expanded_info}_{ts}.{ext}"',
        content
    )
    
    # 9. Add file stats and viewing commands
    stats_and_commands = """
    # Get file stats
    file_size, line_count = get_file_stats(out_fp)
    cat_commands = generate_cat_commands(out_fp, line_count)
    
    # Add file statistics and viewing commands
    file_stats = f"\\n=== File Information ===\\n"
    file_stats += f"Location: {out_fp}\\n"
    file_stats += f"Size: {file_size:,} bytes | Lines: {line_count:,}\\n"
    file_stats += f"\\n=== Viewing Commands ===\\n"
    for i, cmd in enumerate(cat_commands):
        if len(cat_commands) > 1:
            file_stats += f"Part {i+1}/{len(cat_commands)}: {cmd}\\n"
        else:
            file_stats += f"View all: {cmd}\\n"
    
    # Append to file
    with open(out_fp, "a", encoding="utf-8") as f:
        f.write(file_stats)
    
    # Update output with file stats
    out += file_stats
    """
    
    # Add file stats before return
    content = re.sub(
        r'    if not opts.get\("quiet", False\) and \(len\(results\) == 1 or opts.get\("verbose", False\)\):\n',
        f'{stats_and_commands}\n    if not opts.get("quiet", False) and (len(results) == 1 or opts.get("verbose", False)):\n',
        content
    )
    
    # 10. Add console output of file stats
    console_stats = """
        # Display file statistics on console
        rprint(f"[blue]File saved: {out_fp}[/blue]")
        rprint(f"[blue]Size: {file_size:,} bytes | Lines: {line_count:,}[/blue]")
        rprint(f"[blue]Viewing command{'s' if len(cat_commands) > 1 else ''}:[/blue]")
        for cmd in cat_commands:
            rprint(f"[green]{cmd}[/green]")
    """
    
    content = re.sub(
        r'    return out_fp',
        f'{console_stats}\n    return out_fp',
        content
    )
    
    # 11. Update the cli function to save original queries
    content = re.sub(
        r'    if expand:\n        opts\["expand"\] = expand',
        '    if expand:\n        opts["expand"] = expand\n        # Save original queries for reference\n        opts["original_queries"] = queries.copy()',
        content
    )
    
    # 12. Update expanded queries handling
    content = re.sub(
        r'        queries = generate_expanded_queries\(queries, expand, model=model, temperature=temperature\)',
        '        expanded_queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)\n        # Store expanded queries for reference\n        opts["expanded_queries"] = expanded_queries\n        res = handle_multi_query(expanded_queries, opts)\n        if not res:\n            rprint("[red]Error: Failed to process queries[/red]")\n            sys.exit(1)\n        output_multi_results(res, opts)',
        content
    )
    
    # 13. Add display of expanded queries in markdown output
    markdown_section = """            # If expanded queries were used, show them
            if opts.get("expand", 0) > 0 and opts.get("original_queries") and opts.get("expanded_queries"):
                orig_queries = opts.get("original_queries", [])
                all_queries = opts.get("expanded_queries", [])
                
                out += "## Query Expansion\\n"
                out += f"* **Original Queries ({len(orig_queries)})**: "
                out += ", ".join(f'\\"{{q}}\\"' for q in orig_queries) + "\\n"
                
                if len(all_queries) > len(orig_queries):
                    expanded = all_queries[len(orig_queries):]
                    out += f"* **Expanded Queries ({len(expanded)})**: "
                    out += ", ".join(f'\\"{{q}}\\"' for q in expanded) + "\\n\\n"
            """
    
    content = re.sub(
        r'            out = "# Multiple Query Results\\n\\n" if len\(results\) > 1 else "# Single Query Result\\n\\n"',
        f'            out = "# Multiple Query Results\\n\\n" if len(results) > 1 else "# Single Query Result\\n\\n"\n{markdown_section}',
        content
    )
    
    # 14. Add display of expanded queries in text output
    text_section = """            # If expanded queries were used, show them
            if opts.get("expand", 0) > 0 and opts.get("original_queries") and opts.get("expanded_queries"):
                orig_queries = opts.get("original_queries", [])
                all_queries = opts.get("expanded_queries", [])
                
                out += "=== Query Expansion ===\\n"
                out += f"Original Queries ({len(orig_queries)}): "
                out += ", ".join(f'\\"{{q}}\\"' for q in orig_queries) + "\\n"
                
                if len(all_queries) > len(orig_queries):
                    expanded = all_queries[len(orig_queries):]
                    out += f"Expanded Queries ({len(expanded)}): "
                    out += ", ".join(f'\\"{{q}}\\"' for q in expanded) + "\\n\\n"
            """
    
    content = re.sub(
        r'            out = "=== Multi-Query Results ===\\n\\n" if len\(results\) > 1 else "=== Single Query Result ===\\n\\n"',
        f'            out = "=== Multi-Query Results ===\\n\\n" if len(results) > 1 else "=== Single Query Result ===\\n\\n"\n{text_section}',
        content
    )
    
    # 15. Add line length limiting
    line_limiting = """
    # Enforce max line length of 400 characters
    processed_lines = []
    for line in out.split('\\n'):
        while len(line) > 400:
            # Find a space to break at near the 400 character mark
            break_point = line[:400].rfind(' ')
            if break_point == -1:  # No space found, hard break
                break_point = 399
            processed_lines.append(line[:break_point])
            line = line[break_point:].lstrip()
        processed_lines.append(line)
    
    out = '\\n'.join(processed_lines)
    """
    
    content = re.sub(
        r'    if opts.get\("output"\) == \'-\':',
        f'{line_limiting}\n    if opts.get("output") == \'-\':',
        content
    )
    
    # Write the modified content
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"Applied modifications to {filename}")

def generate_diff(original, modified):
    """Generate a diff between the original and modified files."""
    diff_file = original + '.diff'
    os.system(f"diff -u {original} {modified} > {diff_file}")
    print(f"Generated diff: {diff_file}")
    return diff_file

def main():
    """Main function."""
    # The file to modify
    filename = "cli.py"
    
    # Ensure we have a backup
    ensure_backup(filename)
    
    # Create new file for modifications
    new_file = create_new_file(filename)
    
    # Modify the new file
    modify_file(new_file)
    
    # Generate diff
    diff_file = generate_diff(filename, new_file)
    
    print("\n=== Modifications completed following LFCP ===")
    print(f"1. Original file: {filename}")
    print(f"2. Backup file: {filename}.bak")
    print(f"3. Modified file: {new_file}")
    print(f"4. Diff file: {diff_file}")
    print("\nReview the diff file before applying changes.")
    print(f"To apply changes: mv {new_file} {filename}")
    print(f"To revert changes: mv {filename}.bak {filename}")

if __name__ == "__main__":
    main()
