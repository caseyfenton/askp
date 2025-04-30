#!/usr/bin/env python3
"""Script to enhance cli.py with file statistics and expanded query tracking."""
import os
import shutil
import re
import sys

def main():
    """Safely enhance cli.py with new features."""
    # Check if we have file_utils.py (which contains required functions)
    if not os.path.exists('file_utils.py'):
        print("Error: file_utils.py not found, cannot proceed")
        sys.exit(1)
    
    # Create clean copy for enhancement
    shutil.copy2('cli.py', 'cli.py.new')
    print("Created working copy at cli.py.new")
    
    # Read the original file
    with open('cli.py', 'r') as f:
        content = f.read()
    
    # Essential changes:
    # 1. Update imports
    content = content.replace(
        'from typing import Optional, List, Dict, Any',
        'from typing import Optional, List, Dict, Any, Tuple'
    )
    
    # 2. Add file_utils import
    content = re.sub(
        r'(import click.*?\n)',
        r'\1from .file_utils import get_file_stats, generate_cat_commands\n',
        content, flags=re.DOTALL
    )
    
    # 3. Update version
    content = content.replace('VERSION = "2.4.1"', 'VERSION = "2.4.2"')
    
    # 4. Update output_multi_results return type
    content = content.replace(
        'def output_multi_results(results: List[dict], opts: dict) -> None:',
        'def output_multi_results(results: List[dict], opts: dict) -> str:'
    )
    
    # 5. Add return value documentation
    content = re.sub(
        r'("""Combine and output results from multiple queries to a file.*?Args:.*?opts: Options dictionary\.)(.*?)"""',
        r'\1\2\n\n    Returns:\n        Path to the output file or empty string if no results."""',
        content, flags=re.DOTALL
    )
    
    # 6. Change early return
    content = content.replace(
        '    if not results:\n        return',
        '    if not results:\n        return ""'
    )
    
    # 7. Add file stats and viewing commands
    file_stats_code = '''
    # Get file stats and viewing commands
    file_size, line_count = get_file_stats(out_fp)
    cat_commands = generate_cat_commands(out_fp, line_count)
    
    # Add file information and viewing commands to the output file
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
'''
    
    # Add file stats before the "if not opts.get('quiet')" section
    content = re.sub(
        r'(    # Write the output to a file.*?out_fp = os.path.join\(opts\.get\("dir", "\."*?\), fname\).*?with open\(out_fp, "w", encoding="utf-8"\) as f:.*?f\.write\(out\).*?)(\n\s+if not opts\.get\("quiet", False\))',
        r'\1' + file_stats_code + r'\2',
        content, flags=re.DOTALL
    )
    
    # 8. Add console display of file stats
    console_stats = '''
        # Display file statistics on console
        rprint(f"[blue]File saved: {out_fp}[/blue]")
        rprint(f"[blue]Size: {file_size:,} bytes | Lines: {line_count:,}[/blue]")
        rprint(f"[blue]Viewing command{'s' if len(cat_commands) > 1 else ''}:[/blue]")
        for cmd in cat_commands:
            rprint(f"[green]{cmd}[/green]")
'''
    
    # Add console stats before return
    content = re.sub(
        r'(    return out_fp)',
        console_stats + r'\1',
        content
    )
    
    # 9. Update the cli function to track original queries
    content = re.sub(
        r'(    if expand:.*?opts\["expand"\] = expand)',
        r'\1\n        # Save original queries for reference\n        opts["original_queries"] = queries.copy()',
        content
    )
    
    # 10. Modify query expansion handling
    new_expand_handling = '''        expanded_queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)
        # Store expanded queries for reference
        opts["expanded_queries"] = expanded_queries
        res = handle_multi_query(expanded_queries, opts)
        if not res:
            rprint("[red]Error: Failed to process queries[/red]")
            sys.exit(1)
        output_multi_results(res, opts)'''
    
    content = content.replace(
        '        queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)',
        new_expand_handling
    )
    
    # 11. Add expanded queries info to filenames
    expanded_info_code = '''    # Get expanded queries info if available
    expanded_info = ""
    if opts.get("expand", 0) > 0 and opts.get("original_queries") and opts.get("expanded_queries"):
        orig_count = len(opts.get("original_queries", []))
        expanded_count = len(opts.get("expanded_queries", [])) - orig_count
        if expanded_count > 0:
            expanded_info = f"_expanded_{expanded_count}"
    '''
    
    # Add expansion info
    content = re.sub(
        r'(    ts = datetime\.now\(\)\.strftime\("%Y%m%d_%H%M%S"\))',
        expanded_info_code + r'\1',
        content
    )
    
    # 12. Update filenames
    content = content.replace(
        'fname = f"deep_research_{s_query}_{ts}.{ext}"',
        'fname = f"deep_research_{s_query}{expanded_info}_{ts}.{ext}"'
    )
    content = content.replace(
        'fname = f"query_result_{s_query}_{ts}.{ext}"',
        'fname = f"query_result_{s_query}{expanded_info}_{ts}.{ext}"'
    )
    content = content.replace(
        'fname = f"multi_query_results_{ts}.{ext}"',
        'fname = f"multi_query_results{expanded_info}_{ts}.{ext}"'
    )
    
    # Write the enhanced content
    with open('cli.py.new', 'w') as f:
        f.write(content)
    
    # Generate diff for review
    os.system('diff -u cli.py cli.py.new > cli.py.diff')
    print("Generated diff for review: cli.py.diff")
    
    print("\nEnhancements complete. Review cli.py.diff before applying changes.")
    print("To apply the changes: mv cli.py.new cli.py")
    print("To revert if needed: cp cli.py.backup cli.py")

if __name__ == "__main__":
    main()
