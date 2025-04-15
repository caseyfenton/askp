#!/usr/bin/env python3
"""Script to implement all changes to cli.py following LFCP."""
import os
import shutil
import sys
import re

def ensure_backup():
    """Ensure we have a backup of the original file."""
    if not os.path.exists('cli.py.bak-complete'):
        shutil.copy2('cli.py', 'cli.py.bak-complete')
        print("Created backup: cli.py.bak-complete")
    else:
        print("Using existing backup: cli.py.bak-complete")

def create_modified_file():
    """Create a fully modified version of cli.py with all enhancements."""
    # Create new file for changes
    shutil.copy2('cli.py', 'cli.py.enhanced')
    print("Created working copy: cli.py.enhanced")
    
    # Read the file
    with open('cli.py.enhanced', 'r') as f:
        content = f.read()
    
    # 1. Update imports
    content = content.replace(
        'from typing import Optional, List, Dict, Any',
        'from typing import Optional, List, Dict, Any, Tuple'
    )
    
    # 2. Add file_utils import
    content = content.replace(
        'import click',
        'import click\nfrom .file_utils import get_file_stats, generate_cat_commands'
    )
    
    # 3. Update version
    content = content.replace('VERSION = "2.4.1"', 'VERSION = "2.4.2"')
    
    # 4. Update output_multi_results return type and documentation
    content = content.replace(
        'def output_multi_results(results: List[dict], opts: dict) -> None:',
        'def output_multi_results(results: List[dict], opts: dict) -> str:'
    )
    
    # 5. Add return value documentation
    content = content.replace(
        '    Args:\n        results: List of result dictionaries.\n        opts: Options dictionary.',
        '    Args:\n        results: List of result dictionaries.\n        opts: Options dictionary.\n        \n    Returns:\n        Path to the output file.'
    )
    
    # 6. Change early return
    content = content.replace(
        '    if not results:\n        return',
        '    if not results:\n        return ""'
    )
    
    # 7. Add expanded queries info
    ts_pattern = r'    ts = datetime\.now\(\)\.strftime\("%Y%m%d_%H%M%S"\)\n    fmt = opts\.get\("format", "markdown"\)\n    ext = "md" if fmt == "markdown" else \("json" if fmt == "json" else "txt"\)'
    expanded_info = """    # Get expanded queries info if available
    expanded_info = ""
    if opts.get("expand", 0) > 0 and opts.get("original_queries") and opts.get("expanded_queries"):
        orig_count = len(opts.get("original_queries", []))
        expanded_count = len(opts.get("expanded_queries", [])) - orig_count
        if expanded_count > 0:
            expanded_info = f"_expanded_{expanded_count}"
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fmt = opts.get("format", "markdown")
    ext = "md" if fmt == "markdown" else ("json" if fmt == "json" else "txt")"""
    
    content = re.sub(ts_pattern, expanded_info, content)
    
    # 8. Update filenames
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
    
    # 9. Add expanded queries section to markdown output
    md_pattern = r'            out = "# Multiple Query Results\\n\\n" if len\(results\) > 1 else "# Single Query Result\\n\\n"'
    md_expanded = """            out = "# Multiple Query Results\\n\\n" if len(results) > 1 else "# Single Query Result\\n\\n"
            
            # If expanded queries were used, show them
            if opts.get("expand", 0) > 0 and opts.get("original_queries") and opts.get("expanded_queries"):
                orig_queries = opts.get("original_queries", [])
                all_queries = opts.get("expanded_queries", [])
                
                out += "## Query Expansion\\n"
                out += f"* **Original Queries ({len(orig_queries)})**: "
                out += ", ".join(f'\\"{{q}}\\"' for q in orig_queries) + "\\n"
                
                if len(all_queries) > len(orig_queries):
                    expanded = all_queries[len(orig_queries):]
                    out += f"* **Expanded Queries ({len(expanded)})**: "
                    out += ", ".join(f'\\"{{q}}\\"' for q in expanded) + "\\n\\n\""""
    
    content = content.replace(md_pattern, md_expanded)
    
    # 10. Add expanded queries section to text output
    txt_pattern = r'            out = "=== Multi-Query Results ===\\n\\n" if len\(results\) > 1 else "=== Single Query Result ===\\n\\n"'
    txt_expanded = """            out = "=== Multi-Query Results ===\\n" if len(results) > 1 else "=== Single Query Result ===\\n"
            
            # If expanded queries were used, show them
            if opts.get("expand", 0) > 0 and opts.get("original_queries") and opts.get("expanded_queries"):
                orig_queries = opts.get("original_queries", [])
                all_queries = opts.get("expanded_queries", [])
                
                out += "=== Query Expansion ===\\n"
                out += f"Original Queries ({len(orig_queries)}): "
                out += ", ".join(f'\\"{{q}}\\"' for q in orig_queries) + "\\n"
                
                if len(all_queries) > len(orig_queries):
                    expanded = all_queries[len(orig_queries):]
                    out += f"Expanded Queries ({len(expanded)}): "
                    out += ", ".join(f'\\"{{q}}\\"' for q in expanded) + "\\n\\n\""""
    
    content = content.replace(txt_pattern, txt_expanded)
    
    # 11. Compress vertical whitespace for markdown
    content = content.replace(
        'out = f"# Deep Research: {qdisp}\\n\\n## Research Overview\\n\\n{qdisp}\\n\\n## Research Findings\\n\\n"',
        'out = f"# Deep Research: {qdisp}\\n\\n## Research Overview\\n{qdisp}\\n\\n## Research Findings\\n"'
    )
    content = content.replace(
        'out += f"### {i+1}. {r.get(\'query\', \'Section \'+str(i+1))}\\n\\n" + format_markdown(r) + "\\n\\n" + "-" * 50 + "\\n\\n"',
        'out += f"### {i+1}. {r.get(\'query\', \'Section \'+str(i+1))}\\n" + format_markdown(r) + "\\n" + "-" * 50 + "\\n"'
    )
    content = content.replace(
        'out += f"## Query {i+1}: {qdisp}\\n\\n" + format_markdown(r) + "\\n\\n" + "-" * 50 + "\\n\\n"',
        'out += f"## Query {i+1}: {qdisp}\\n" + format_markdown(r) + "\\n" + "-" * 50 + "\\n"'
    )
    
    # 12. Compress vertical whitespace for text
    content = content.replace(
        'out = f"=== Deep Research: {qdisp} ===\\n\\n=== Research Overview ===\\n\\n{qdisp}\\n\\n=== Research Findings ===\\n\\n"',
        'out = f"=== Deep Research: {qdisp} ===\\n=== Research Overview ===\\n{qdisp}\\n\\n=== Research Findings ===\\n"'
    )
    content = content.replace(
        'out += f"=== {i+1}. {r.get(\'query\', \'Section \' + str(i+1))} ===\\n\\n" + format_text(r) + "\\n\\n" + "=" * 50 + "\\n\\n"',
        'out += f"=== {i+1}. {r.get(\'query\', \'Section \' + str(i+1))} ===\\n" + format_text(r) + "\\n" + "=" * 50 + "\\n"'
    )
    content = content.replace(
        'out += f"=== Query {i+1}: {qdisp} ===\\n\\n" + format_text(r) + "\\n\\n" + "=" * 50 + "\\n\\n"',
        'out += f"=== Query {i+1}: {qdisp} ===\\n" + format_text(r) + "\\n" + "=" * 50 + "\\n"'
    )
    
    # 13. Add line length limiting
    line_length_limit = """
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
    
    content = content.replace(
        '    if opts.get("output") == \'-\':',
        f'{line_length_limit}\n    if opts.get("output") == \'-\':'
    )
    
    # 14. Add file stats and viewing commands
    file_stats = """
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
    
    content = content.replace(
        '    if not opts.get("quiet", False) and (len(results) == 1 or opts.get("verbose", False)):',
        f'{file_stats}\n    if not opts.get("quiet", False) and (len(results) == 1 or opts.get("verbose", False)):'
    )
    
    # 15. Add console display of file stats
    console_stats = """
        # Display file statistics on console
        rprint(f"[blue]File saved: {out_fp}[/blue]")
        rprint(f"[blue]Size: {file_size:,} bytes | Lines: {line_count:,}[/blue]")
        rprint(f"[blue]Viewing command{'s' if len(cat_commands) > 1 else ''}:[/blue]")
        for cmd in cat_commands:
            rprint(f"[green]{cmd}[/green]")
    """
    
    content = content.replace(
        '    return out_fp',
        f'{console_stats}\n    return out_fp'
    )
    
    # 16. Update the cli function to track original queries
    content = content.replace(
        '    if expand:\n        opts["expand"] = expand',
        '    if expand:\n        opts["expand"] = expand\n        # Save original queries for reference\n        opts["original_queries"] = queries.copy()'
    )
    
    # 17. Update the expand handling
    expand_handling = 'expanded_queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)\n        # Store expanded queries for reference\n        opts["expanded_queries"] = expanded_queries\n        res = handle_multi_query(expanded_queries, opts)\n        if not res:\n            rprint("[red]Error: Failed to process queries[/red]")\n            sys.exit(1)\n        output_multi_results(res, opts)'
    
    content = content.replace(
        'queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)',
        expand_handling
    )
    
    # Write the modified content
    with open('cli.py.enhanced', 'w') as f:
        f.write(content)
    
    print("All enhancements applied to cli.py.enhanced")

def generate_diff():
    """Generate diff for review."""
    os.system('diff -u cli.py cli.py.enhanced > cli.py.enhanced.diff')
    print("Generated comprehensive diff: cli.py.enhanced.diff")

def main():
    """Main function."""
    print("Following Large File Change Safety Protocol (LFCP)")
    ensure_backup()
    create_modified_file()
    generate_diff()
    print("\nAll enhancements complete. Review the diff before applying changes.")
    print("To apply the changes:\n  cp cli.py.enhanced cli.py\n")
    print("To revert if needed:\n  cp cli.py.bak-complete cli.py\n")

if __name__ == "__main__":
    main()
