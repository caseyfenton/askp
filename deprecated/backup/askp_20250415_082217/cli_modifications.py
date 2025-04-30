#!/usr/bin/env python3
"""
This file contains the modifications to be made to cli.py
It serves as a reference and will not be executed directly.
"""

# 1. Import the file_utils module at the top of the file
from .file_utils import get_file_stats, generate_cat_commands

# 2. Update the VERSION constant
VERSION = "2.4.2"  # Version bump for new features

# 3. Modifications to output_multi_results function

# 3.1 Add expanded query info to filename
expanded_info = ""
if opts.get("expand", 0) > 0 and opts.get("original_queries") and opts.get("expanded_queries"):
    orig_count = len(opts.get("original_queries", []))
    expanded_count = len(opts.get("expanded_queries", [])) - orig_count
    if expanded_count > 0:
        expanded_info = f"_expanded_{expanded_count}"

# 3.2 Update filenames with expanded info
fname = f"deep_research_{s_query}{expanded_info}_{ts}.{ext}"
fname = f"query_result_{s_query}{expanded_info}_{ts}.{ext}"
fname = f"multi_query_results{expanded_info}_{ts}.{ext}"

# 3.3 Add the expanded queries section to markdown output
# If expanded queries were used, show them
if opts.get("expand", 0) > 0 and opts.get("original_queries") and opts.get("expanded_queries"):
    orig_queries = opts.get("original_queries", [])
    all_queries = opts.get("expanded_queries", [])
    
    out += "## Query Expansion\n"
    out += f"* **Original Queries ({len(orig_queries)})**: "
    out += ", ".join(f'"{q}"' for q in orig_queries) + "\n"
    
    if len(all_queries) > len(orig_queries):
        expanded = all_queries[len(orig_queries):]
        out += f"* **Expanded Queries ({len(expanded)})**: "
        out += ", ".join(f'"{q}"' for q in expanded) + "\n\n"

# 3.4 Add the expanded queries section to text output
# If expanded queries were used, show them
if opts.get("expand", 0) > 0 and opts.get("original_queries") and opts.get("expanded_queries"):
    orig_queries = opts.get("original_queries", [])
    all_queries = opts.get("expanded_queries", [])
    
    out += "=== Query Expansion ===\n"
    out += f"Original Queries ({len(orig_queries)}): "
    out += ", ".join(f'"{q}"' for q in orig_queries) + "\n"
    
    if len(all_queries) > len(orig_queries):
        expanded = all_queries[len(orig_queries):]
        out += f"Expanded Queries ({len(expanded)}): "
        out += ", ".join(f'"{q}"' for q in expanded) + "\n\n"

# 3.5 Add line length limiting code
# Enforce max line length of 400 characters
processed_lines = []
for line in out.split('\n'):
    while len(line) > 400:
        # Find a space to break at near the 400 character mark
        break_point = line[:400].rfind(' ')
        if break_point == -1:  # No space found, hard break
            break_point = 399
        processed_lines.append(line[:break_point])
        line = line[break_point:].lstrip()
    processed_lines.append(line)

out = '\n'.join(processed_lines)

# 3.6 Add file statistics and viewing commands
# Get file stats
file_size, line_count = get_file_stats(out_fp)
cat_commands = generate_cat_commands(out_fp, line_count)

# Add file statistics and viewing commands
file_stats = f"\n=== File Information ===\n"
file_stats += f"Location: {out_fp}\n"
file_stats += f"Size: {file_size:,} bytes | Lines: {line_count:,}\n"
file_stats += f"\n=== Viewing Commands ===\n"
for i, cmd in enumerate(cat_commands):
    if len(cat_commands) > 1:
        file_stats += f"Part {i+1}/{len(cat_commands)}: {cmd}\n"
    else:
        file_stats += f"View all: {cmd}\n"

# Append to file
with open(out_fp, "a", encoding="utf-8") as f:
    f.write(file_stats)

# Update output with file stats
out += file_stats

# 3.7 Add console display of file statistics
# Display file statistics on console
rprint(f"[blue]File saved: {out_fp}[/blue]")
rprint(f"[blue]Size: {file_size:,} bytes | Lines: {line_count:,}[/blue]")
rprint(f"[blue]Viewing command{'s' if len(cat_commands) > 1 else ''}:[/blue]")
for cmd in cat_commands:
    rprint(f"[green]{cmd}[/green]")

# 4. Update the cli function to track original and expanded queries
if expand:
    opts["expand"] = expand
    # Save original queries for reference
    opts["original_queries"] = queries.copy()

# 5. Update the expand handling section
expanded_queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)
# Store expanded queries for reference
opts["expanded_queries"] = expanded_queries
res = handle_multi_query(expanded_queries, opts)
if not res:
    rprint("[red]Error: Failed to process queries[/red]")
    sys.exit(1)
output_multi_results(res, opts)
