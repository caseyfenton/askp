#!/usr/bin/env python3
"""
Query execution module for ASKP.
Contains execute_query, handle_multi_query, output_result, and output_multi_results.
"""
import os
import sys
import json
import time
import uuid
import threading
import re
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any, Tuple, Union
from rich import print as rprint

from .api import search_perplexity
from .formatters import format_json, format_markdown, format_text
from .utils import (format_size, sanitize_filename, load_api_key, get_model_info, 
                   normalize_model_name, estimate_cost, get_output_dir,
                   generate_combined_filename, generate_unique_id)
from .file_utils import format_path, generate_cat_commands
from .bgrun_integration import notify_query_completed, notify_multi_query_completed, update_askp_status_widget

def save_result_file(query: str, result: dict, index: int, output_dir: str, opts: Optional[Dict[str, Any]] = None) -> str:
    """
    Save query result to a file and return the filepath.
    
    Args:
        query: The query text
        result: Query result dictionary
        index: Query index
        output_dir: Directory to save results in
        opts: Options dictionary containing format preference
    
    Returns:
        Path to the saved file
    """
    import os
    import json
    from datetime import datetime
    from .formatters import format_markdown, format_json, format_text
    
    opts = opts or {}
    format_type = opts.get("format", "markdown").lower()
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_part = sanitize_filename(query[:50])
    
    # Determine file extension and content based on format type
    if format_type == "json":
        file_ext = ".json"
        content = result  # Will be JSON-serialized later
    elif format_type == "text":
        file_ext = ".txt"
        content = format_text(result)
    else:  # Default to markdown
        file_ext = ".md"
        content = format_markdown(result)
    
    # Create filename and full path
    filename = f"query_{index+1}_{timestamp}_{query_part}{file_ext}"
    filepath = os.path.join(output_dir, filename)
    
    # Save the file in the appropriate format
    if format_type == "json":
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    
    return filepath

def append_to_combined(query: str, result: dict, index: int, output_dir: str, 
                      lock: threading.Lock, opts: dict) -> str:
    """
    Append result to a combined file for multi-query results.
    
    Args:
        query: The query string
        result: Query result dictionary
        index: Query index
        output_dir: Directory to save results
        lock: Thread lock for safe concurrent writes
        opts: Options dictionary containing format preference
        
    Returns:
        Path to the combined file
    """
    import os
    import json
    from datetime import datetime
    from .formatters import format_markdown, format_json, format_text
    from .utils import generate_combined_filename
    
    # Determine format type
    format_type = opts.get("format", "markdown").lower()
    
    os.makedirs(output_dir, exist_ok=True)
    with lock:
        num_queries = opts.get("total_queries", 1)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use the utility function which now handles format type
        combined_filename = generate_combined_filename(
            [query] if index == 0 else ["query"], 
            opts
        )
        combined_filepath = os.path.join(output_dir, combined_filename)
        
        # Handle different formats
        if format_type == "json":
            # For JSON, we need to build a composite structure
            data = {}
            if index == 0 or not os.path.exists(combined_filepath):
                # Initialize new JSON structure
                data = {
                    "metadata": {
                        "query_count": num_queries,
                        "timestamp": timestamp
                    },
                    "results": []
                }
            else:
                # Load existing JSON
                try:
                    with open(combined_filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except:
                    # If file exists but is corrupt, start fresh
                    data = {
                        "metadata": {
                            "query_count": num_queries,
                            "timestamp": timestamp
                        },
                        "results": []
                    }
            
            # Add this result
            data["results"].append({
                "query_index": index + 1,
                "query_text": query,
                "result": result
            })
            
            # Write updated JSON
            with open(combined_filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
        elif format_type == "text":
            # Plain text format
            if index == 0 or not os.path.exists(combined_filepath):
                # Create a new file for the first result
                with open(combined_filepath, "w", encoding="utf-8") as f:
                    f.write(f"Combined Results ({num_queries} queries)\n\n")
            
            # Append this result
            with open(combined_filepath, "a", encoding="utf-8") as f:
                f.write(f"\nQuery {index+1}: {query}\n\n")
                f.write(format_text(result))
                f.write("\n---\n")
        
        else:
            # Default to markdown
            if index == 0 or not os.path.exists(combined_filepath):
                # Create a new file for the first result
                with open(combined_filepath, "w", encoding="utf-8") as f:
                    f.write(f"# Combined Results ({num_queries} queries)\n\n")
            
            # Append this result
            with open(combined_filepath, "a", encoding="utf-8") as f:
                f.write(f"\n## Query {index+1}: {query}\n\n")
                content = format_markdown(result).replace("# ", "### ")
                f.write(content)
                f.write("\n---\n")
    
    return combined_filepath

def execute_query(q: str, i: int, opts: dict, lock: Optional[threading.Lock] = None) -> Optional[dict]:
    """Execute a single query and save its result."""
    res = search_perplexity(q, opts)
    if not res:
        return None
    od = get_output_dir()
    rf = save_result_file(q, res, i, od, opts)
    rel_path = format_path(rf)
    res.setdefault("metadata", {})["saved_path"] = rf
    if opts.get("suppress_model_display", False):
        t = q[:40] + "..." if len(q) > 40 else q
        bytes_count = len(res["results"][0].get("content", "")) if res.get("results") else len(res.get("content", ""))
        print(f'{i+1}: "{t}"  {format_size(bytes_count)} | {res.get("tokens", 0)}T | ${res["metadata"]["cost"]:.4f}')
    else:
        print(f"Saved: {rel_path}")
    if opts.get("combine") and lock and i == opts.get("total_queries", 0) - 1:
        cf = append_to_combined(q, res, i, od, lock, opts)
        print(f"Combined results saved to {format_path(cf)}")
    return res

def handle_multi_query(queries: List[str], opts: dict) -> List[Optional[dict]]:
    """Process multiple queries in parallel."""
    # Process deep research first - this should be done before any regular processing
    if opts.get("deep", False) and len(queries) == 1:
        from .deep_research import generate_research_plan, process_research_plan
        
        # Generate the research plan
        research_plan = generate_research_plan(
            queries[0], 
            model=opts.get("model", "sonar-reasoning-pro"),
            temperature=opts.get("temperature", 0.7),
            options=opts
        )
        
        # Store the original query
        opts["query"] = queries[0]
        
        # Process the research plan (this will call back to handle_multi_query with the sub-queries)
        return process_research_plan(research_plan, opts)
    
    # Only mention "parallel" for multiple queries
    if len(queries) > 1:
        print(f"\nProcessing {len(queries)} queries in parallel...")
    else:
        # Only show basic processing message if not a sub-query of deep research
        if not opts.get("processing_subqueries", False):
            print(f"\nProcessing query...")
        
    from .utils import get_model_info
    model = opts.get("model", "sonar-reasoning")
    model_info = get_model_info(model)
    
    # Only show model info if not processing sub-queries for deep research
    if not opts.get("processing_subqueries", False):
        print(f"Model: {model_info['display_name']} | Temp: {opts.get('temperature', 0.7)}")
    
    opts["suppress_model_display"] = True
    results: List[Optional[dict]] = []
    total_tokens, total_cost = 0, 0
    
    # Set start time for all queries
    start_time = time.time()
    
    # Handle single query case - no need for parallel processing
    if len(queries) == 1 and not opts.get("processing_subqueries", False):
        result = execute_query(queries[0], 0, opts)
        if result:
            results = [result]
            total_tokens += result.get("tokens", 0)
            total_cost += result.get("metadata", {}).get("cost", 0.0)
            
            # For --view flag, display content directly in terminal
            view_enabled = opts.get("view")
            view_lines_count = opts.get("view_lines")
            
            if (view_enabled or view_lines_count is not None) and not opts.get("quiet", False) and "content" in result:
                # Default to 200 lines if just --view is used
                max_lines = 200
                if view_lines_count is not None:
                    max_lines = view_lines_count
                
                content_lines = result["content"].split('\n')
                
                print("\nQuery Result:")
                
                if len(content_lines) > max_lines:
                    # Show limited content with message about remaining lines
                    for line in content_lines[:max_lines]:
                        print(line)
                    remaining = len(content_lines) - max_lines
                    print(f"\n... {remaining} more lines not shown.")
                    print(f"To view full results: cat {result.get('metadata', {}).get('saved_path', '')}")
                else:
                    # Show all content
                    print(result["content"])
                
                print("\n")
    else:
        # For multiple queries, use parallel processing
        od = get_output_dir(opts.get("output_dir"))
        os.makedirs(od, exist_ok=True)
        
        from concurrent.futures import ThreadPoolExecutor
        # Number of parallel queries
        max_parallel = opts.get("max_parallel", 5)
        
        # Process queries sequentially for better user experience
        if len(queries) <= 2:
            # For a small number of queries, process them sequentially
            for i, q in enumerate(queries):
                try:
                    r = execute_query(q, i, opts)
                    if r:
                        results.append(r)
                        total_tokens += r.get("tokens", 0)
                        total_cost += r.get("metadata", {}).get("cost", 0.0)  # Safely access cost with default
                except Exception as e:
                    print(f"Error processing query {i+1}: {e}")
        else:
            # For more queries, use ThreadPoolExecutor but with safeguards
            with ThreadPoolExecutor(max_workers=min(max_parallel, len(queries))) as ex:
                futures = {ex.submit(execute_query, q, i, opts): i for i, q in enumerate(queries)}
                for f in futures:
                    try:
                        r = f.result()
                        if r:
                            results.append(r)
                            total_tokens += r.get("tokens", 0)
                            # Safely access cost with a default value if missing
                            total_cost += r.get("metadata", {}).get("cost", 0.0)
                    except Exception as e:
                        print(f"Error in future: {e}")
    
    elapsed = time.time() - start_time
    qps = len(results)/elapsed if elapsed > 0 else 0
    od = get_output_dir()
    
    # Deep research synthesis is handled after subqueries are processed
    if opts.get("processing_subqueries", False):
        from .deep_research import process_deep_research
        return process_deep_research(results, opts)
    
    # Combine results for single or multi queries    
    print("\nDONE!")
    
    # Different output messages for single vs multiple queries
    if len(queries) > 1:
        combined_filename = generate_combined_filename(queries, opts)
        combined_path = os.path.join(od, combined_filename)
        print(f"Output file: {format_path(combined_path)}")
        print(f"Queries processed: {len(results)}/{len(queries)}")
    else:
        if results and results[0] and "metadata" in results[0] and "saved_path" in results[0]["metadata"]:
            print(f"Output file: {format_path(results[0]['metadata']['saved_path'])}")
    
    # Show token usage
    if len(results) > 0:
        # We want to sum all token counts in results
        total_tokens = sum(r.get("tokens", 0) for r in results if r)
        count_text = f"{len(results)} quer{'y' if len(results) == 1 else 'ies'}"
        cost_text = f" | ${total_cost:.4f}" if total_cost > 0 else ""
        print(f"{count_text} | {total_tokens:,}T{cost_text} | {elapsed:.1f}s ({qps:.1f}q/s)")
    
    return results

def suggest_cat_commands(results: List[dict], output_dir: str) -> None:
    """Suggest cat commands to view result files."""
    from .file_utils import generate_cat_commands
    cmd_groups = generate_cat_commands(results, output_dir)
    if not cmd_groups:
        return
    for group_name, commands in cmd_groups.items():
        if commands:
            print(f"\n== {group_name} Commands ==")
            for cmd in commands:
                print(f"  {cmd}")

def output_result(res: dict, opts: dict) -> None:
    """Output a single query result."""
    if not res:
        return
    fmt = opts.get("format", "markdown")
    if fmt in ["markdown", "md"]:
        out = format_markdown(res)
    elif fmt == "json":
        out = format_json(res)
    else:  # text
        out = format_text(res)
    
    # For human-readable output (--human), directly display the content in the terminal
    if opts.get("human", False) and not opts.get("quiet", False) and fmt != "json":
        if "content" in res:
            print("\nQuery Result:")
            print(res["content"])
            print("\n")
    
    # Save to file if output is specified
    saved_path = None
    if opts.get("output", None):
        try:
            with open(opts["output"], "w", encoding="utf-8") as f:
                f.write(out)
            saved_path = opts["output"]
        except PermissionError:
            print(f"Error: Permission denied writing to {opts['output']}")
    else:
        import click
        click.echo(out)
    if not opts.get("quiet", False) and fmt != "json":
        op_dir = format_path(get_output_dir())
        print(f"Results saved to: {op_dir}")
        saved_path = saved_path or res.get("metadata", {}).get("saved_path")
    if saved_path and not opts.get("quiet", False):
        from .bgrun_integration import notify_query_completed
        notify_query_completed(res.get("query", ""), saved_path, res.get("model", ""),
                               res.get("tokens", 0), res.get("metadata", {}).get("cost", 0.0))
    from .tips import get_formatted_tip
    if not opts.get("quiet", False) and not opts.get("multi", False):
        tip = get_formatted_tip()
        if tip:
            print(tip)

def output_multi_results(results: List[dict], opts: dict) -> None:
    """Combine and output results from multiple queries to a file."""
    if not results:
        return
    out_dir = opts.get("output_dir", os.path.join(os.getcwd(), "perplexity_results"))
    os.makedirs(out_dir, exist_ok=True)
    is_deep = opts.get("deep", False)
    overview = opts.get("research_overview", "")
    if isinstance(overview, (tuple, list)):
        overview = " ".join(str(x) for x in overview)
        
    fmt = opts.get("format", "markdown")
    is_single_query = len(results) == 1
    
    # Generate appropriate filename
    if is_single_query and not is_deep:
        base_name = results[0].get("query", "query").strip()
        filename = sanitize_filename(f"{base_name[:50]}_{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        if fmt == "json":
            filename += ".json"
        else:
            filename += ".md"
    else:
        filename = generate_combined_filename([r.get("query", f"query_{i}") for i, r in enumerate(results) if r], opts)
    
    out_file = os.path.join(out_dir, filename)
    out = ""
    
    # Format output based on type and format
    if is_deep:
        intro = results[0] if results else {}
        concl = results[-1] if len(results) > 1 else {}
        if fmt == "markdown":
            out = "# Deep Research Results\n\n"
            if intro.get("content"):
                out += "## Overview\n\n" + intro["content"] + "\n\n"
            if len(results) > 2:
                out += "## Table of Contents\n\n"
                for i, r in enumerate(results[1:-1], 1):
                    if r and r.get("query"):
                        slug = re.sub(r'[^a-z0-9\s-]', '', r["query"].lower()).strip().replace(' ', '-')
                        out += f"{i}. [{r['query']}](#{slug})\n"
                out += "\n\n"
                for r in results[1:-1]:
                    if r and r.get("query") and r.get("content"):
                        out += f"## {r['query']}\n\n{r['content']}\n\n---\n\n"
            if concl.get("content"):
                out += "## Conclusion\n\n" + concl["content"] + "\n\n"
        else:
            combined = {"type": "deep_research",
                        "overview": intro.get("content", "") if intro else "",
                        "conclusion": concl.get("content", "") if concl else "",
                        "sections": [{"title": r["query"], "content": r["content"]}
                                     for r in results[1:-1] if r and r.get("query") and r.get("content")]}
            out = json.dumps(combined, indent=2)
    else:
        if fmt == "json":
            combined = {"type": "multi_query", "timestamp": datetime.now().isoformat(),
                        "num_queries": len(results), "results": results}
            out = json.dumps(combined, indent=2)
        else:
            tot_toks = sum(r.get("tokens", 0) for r in results if r)
            tot_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
            qps = results[0].get("metadata", {}).get("queries_per_second", 0) if results else 0
            et = results[0].get("metadata", {}).get("elapsed_time", 0) if results else 0
            out = f"# Combined Query Results\n\nSummary:\n\nTotals | Model: {opts.get('model','sonar-pro')} | {len(results)} queries | {tot_toks:,} tokens | ${tot_cost:.4f} | {et:.1f}s ({qps:.2f} q/s)\n\nResults saved to: {format_path(out_dir)}\n\n"
            for i, r in enumerate(results):
                if not r:
                    continue
                out += f"## Query {i+1}: {r.get('query', f'Query {i+1}')}\n\n"
                out += (r["content"] if "content" in r else "No content available") + "\n\n"
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(out)
    except PermissionError:
        print(f"Error: Permission denied writing to {out_file}")
        return
    rel_path = format_path(out_file)
    
    # Handle viewing content directly vs showing paths based on --view flag
    if not opts.get("quiet", False):
        if opts.get("view") and fmt == "markdown":
            # Display content directly if --view flag is used
            print("\nQuery Results:")
            
            for i, r in enumerate(results):
                if r and "query" in r and "content" in r:
                    # Get max lines to display
                    view_lines = opts.get("view_lines")
                    max_lines = view_lines if view_lines is not None else 200
                    
                    print(f"\nQuery {i+1}: {r['query']}")
                    
                    # Display content with line limit
                    content_lines = r["content"].split('\n')
                    if len(content_lines) > max_lines:
                        # Show limited content with message about remaining lines
                        for line in content_lines[:max_lines]:
                            print(line)
                        remaining = len(content_lines) - max_lines
                        print(f"\n... {remaining} more lines not shown.")
                    else:
                        print(r["content"])
                        
            print(f"\nFull results saved to: {rel_path}")
        else:
            # Only show the combined results message for multiple queries, not single queries
            if len(results) > 1:
                print(f"Combined results saved to: {rel_path}")
                
                # Only show command suggestions if we're not already viewing the content with --view
                if fmt == "markdown" and not is_deep:
                    suggest_cat_commands(results, out_dir)
            
    # Update notification systems
    if not opts.get("quiet", False):
        tot_toks = sum(r.get("tokens", 0) for r in results if r)
        tot_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
        notify_multi_query_completed(len(results), rel_path, tot_toks, tot_cost)
        update_askp_status_widget(len(results), tot_cost)