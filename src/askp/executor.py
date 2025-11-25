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

from .formatters import format_json, format_markdown, format_text
from .utils import (format_size, sanitize_filename, load_api_key, get_model_info,
                   normalize_model_name, estimate_cost, get_output_dir,
                   generate_combined_filename, generate_unique_id)
from .file_utils import format_path, generate_cat_commands
from .api import search_perplexity as sp

def index_with_sema(result_path: Path) -> None:
    """Index newly created result with SEMA for future cache hits."""
    try:
        import subprocess
        subprocess.run(
            ['sema', '--index'],
            cwd=result_path.parent,
            capture_output=True,
            timeout=10,
            check=False  # Don't fail if sema not available
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # SEMA not available, skip indexing (don't break askp)
        pass

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
    from .agent_response import AgentResponseCache, format_agent_index

    opts = opts or {}
    format_type = opts.get("format", "markdown").lower()
    agent_mode = opts.get("agent_mode", False)

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_part = sanitize_filename(query[:50])

    # Determine file extension and content based on format type and agent mode
    if agent_mode and "structured_content" in result:
        # Cache the full response for later retrieval
        cache = AgentResponseCache()
        query_id = result.get("metadata", {}).get("uuid")
        if query_id:
            cache.store(query_id, result)

        # For agent mode, save lightweight index by default
        index_data = cache.get_index(query_id)

        if format_type == "json":
            file_ext = ".json"
            content = index_data
        else:
            file_ext = ".md"
            content = format_agent_index(index_data)
            content += f"\n\n---\n**Query ID:** `{query_id}`\n\nUse this ID to retrieve modules:\n"
            content += f"```bash\naskp --agent-module <ID> --query-id {query_id}\n```\n"
    else:
        # Regular mode processing
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

    # Index with SEMA for future cache hits
    index_with_sema(Path(filepath))

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

        # Index with SEMA after each write (for incremental updates)
        index_with_sema(Path(combined_filepath))

    return combined_filepath

def execute_query(q: str, i: int, opts: dict, lock: Optional[threading.Lock] = None) -> Optional[dict]:
    """Execute a single query and save its result."""
    res = sp(q, opts)
    if not res:
        return None
    od = get_output_dir()
    rf = save_result_file(q, res, i, od, opts)
    abs_path = str(rf)  # Use absolute path for agents
    res.setdefault("metadata", {})["saved_path"] = rf
    if opts.get("suppress_model_display", False):
        t = q[:40] + "..." if len(q) > 40 else q
        bytes_count = len(res["results"][0].get("content", "")) if res.get("results") else len(res.get("content", ""))

        # Check if we have a successful response with cost information
        if "error" in res:
            # Display error message without cost information
            print(f'{i+1}: "{t}"  Error')
        else:
            # Display normal success message with cost
            print(f'{i+1}: "{t}"  {format_size(bytes_count)} | {res.get("tokens", 0)}T | ${res["metadata"].get("cost", 0):.4f}')
    else:
        print(f"Saved: {abs_path}")
    
    # Only create the combined file if no_combine is not set and combine is set
    if not opts.get("no_combine", False) and opts.get("combine") and lock and i == opts.get("total_queries", 0) - 1:
        cf = append_to_combined(q, res, i, od, lock, opts)
        if not opts.get("quiet", False):
            print(f"Combined results saved to {format_path(cf)}")
    return res

def handle_multi_query(queries: List[str], opts: dict) -> List[Optional[dict]]:
    """Process multiple queries in parallel."""
    # Process deep research first - this should be done before any regular processing
    if len(queries) == 1:
        if opts.get("custom_deep_research", False):
            # Use our custom deep research implementation (multiple parallel queries)
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
        elif opts.get("deep", False) and not opts.get("custom_deep_research", False):
            # Use Perplexity's built-in deep research model (single query)
            # No special processing needed, just execute as a normal query but with sonar-deep-research model
            model = opts.get("model", "sonar-deep-research")
            if not opts.get("quiet", False):
                print(f"Using Perplexity's deep research model: {model}")
            
            # The sonar-deep-research model handles everything in one query
            # Just note that we're in deep research mode for output formatting
            opts["deep_single_query"] = True
    
    # Only mention "parallel" for multiple queries
    if len(queries) > 1:
        if not opts.get("quiet", False):
            print(f"\nProcessing {len(queries)} queries in parallel...")
    else:
        # Only show basic processing message if not a sub-query of deep research
        # Processing message is now handled by the CLI module
        pass
        
    from .utils import get_model_info
    model = opts.get("model", "sonar-reasoning")
    model_info = get_model_info(model)
    
    # Only show model info if not processing sub-queries for deep research
    if not opts.get("processing_subqueries", False):
        if not opts.get("quiet", False):
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
                        total_cost += r.get("metadata", {}).get("cost", 0)  # Safely access cost with default
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
    
    # Process the combined output only if no-combine is not set
    if not opts.get("no_combine", False):
        # Process the results with output_multi_results, which will create the combined file
        output_multi_results(results, opts)
    else:
        # Just show the individual file info without creating a combined file
        if not opts.get("quiet", False):
            print("\nDONE!")
            print(f"Queries processed: {len(results)}/{len(queries)}")
        
        # Show list of individual files
        suggest_cat_commands(results, od)
        
        # Also include the stats summary
        if not opts.get("quiet", False):
            print(f"\n{len(results)} queries | {total_tokens:,}T | ${total_cost:.4f} | {elapsed:.1f}s ({qps:.1f}q/s)")
    
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

def output_result(res: Optional[Dict[str, Any]], opts: Dict[str, Any]) -> None:
    """Format result and output to terminal or file."""
    if not res:
        print("Error: No result to output")
        return
    
    fmt = opts.get("format", "markdown")
    if fmt in ["markdown", "md"]:
        out = format_markdown(res)
    elif fmt == "json":
        out = format_json(res)
    else:
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
        # Only echo output if not being displayed by other means
        if not opts.get("human", False) and not opts.get("view", False):
            import click
            click.echo(out)
    
    # Show where results are saved
    if not opts.get("quiet", False) and fmt != "json":
        saved_path = saved_path or res.get("metadata", {}).get("saved_path")
        if saved_path:
            rel_path = format_path(saved_path)
            print(f"\n📁 Full results saved to: {rel_path}")
    
    # Show tips occasionally
    if saved_path and not opts.get("quiet", False):
        from .tips import get_formatted_tip
        if not opts.get("quiet", False) and not opts.get("multi", False):
            tip = get_formatted_tip()
            if tip:
                print(tip)

def output_multi_results(results: List[dict], opts: dict) -> None:
    """Combine and output results from multiple queries to a file."""
    if not results:
        print("No results to output!")
        return
    
    import json
    import os
    from datetime import datetime
    
    opts = opts or {}
    fmt = opts.get("format", "markdown").lower()
    if fmt in ["md", "markdown"]:
        fmt = "markdown"
    elif fmt in ["txt", "text"]:
        fmt = "text"
    
    # Initialize token and cost counters right away so they're available in all code paths
    tot_toks = sum(r.get("tokens", 0) for r in results if r)
    tot_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
    model = opts.get("model", "sonar-pro")
    
    # Determine if this is a deep research result
    is_deep = opts.get("deep", False) or opts.get("custom_deep_research", False) or opts.get("deep_single_query", False)
    is_custom_deep = opts.get("custom_deep_research", False)
    is_builtin_deep = opts.get("deep_single_query", False)
    
    if is_deep:
        # For deep research, use a more descriptive filename
        query = opts.get("query", "Deep_Research")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_query = sanitize_filename(query[:30])
        out_file = f"{sanitized_query}_{timestamp}.{fmt}"
        
        # Get the right output dir
        if is_custom_deep and "final_output_dir" in opts:
            # Use the final output dir for custom deep research
            out_dir = opts["final_output_dir"]
        else:
            # Use the regular output dir
            out_dir = opts.get("output_dir", get_output_dir())
        
        # Create output directory if it doesn't exist
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, out_file)
    else:
        # For regular multi-query, use the standard approach
        out_dir = opts.get("output_dir", get_output_dir())
        os.makedirs(out_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate an appropriate filename
        if len(results) == 1:
            query = results[0].get("query", "Unknown")
            query_part = sanitize_filename(query[:50])
            out_file = f"{query_part}_{timestamp}.{fmt}"
        else:
            # For multiple queries, use a combined filename
            out_file = generate_combined_filename(
                [r.get("query", f"Query_{i+1}") for i, r in enumerate(results) if r],
                opts
            )
        
        out_file = os.path.join(out_dir, out_file)
    
    # Generate the output content based on format and type
    if fmt == "json":
        if is_deep:
            # Create a structured JSON for deep research
            if is_custom_deep:
                # For custom deep research with multiple queries
                intro = results[0] if results else {}
                concl = results[-1] if len(results) > 1 else {}
                combined = {
                    "type": "custom_deep_research",
                    "query": opts.get("query", "Unknown"),
                    "timestamp": datetime.now().isoformat(),
                    "overview": intro.get("content", "") if intro else "",
                    "conclusion": concl.get("content", "") if concl else "",
                    "sections": [{"title": r["query"], "content": r["content"]}
                                for r in results[1:-1] if r and r.get("query") and r.get("content")]
                }
            else:
                # For built-in deep research (single query)
                combined = {
                    "type": "deep_research",
                    "query": opts.get("query", results[0].get("query", "Unknown")),
                    "timestamp": datetime.now().isoformat(),
                    "content": results[0].get("content", "") if results else ""
                }
            out = json.dumps(combined, indent=2)
        else:
            # Regular multi-query JSON
            combined = {
                "type": "multi_query",
                "timestamp": datetime.now().isoformat(),
                "num_queries": len(results),
                "results": results
            }
            out = json.dumps(combined, indent=2)
    else:
        # Markdown/text output
        if is_deep:
            if is_custom_deep:
                # Custom deep research with intro, sections, and conclusion
                intro = results[0] if results else {}
                concl = results[-1] if len(results) > 1 else {}
                
                out = f"# Deep Research Results: {opts.get('query', 'Research Topic')}\n\n"
                out += f"*Generated using custom deep research with multiple parallel queries*\n\n"
                out += f"**Model:** {model} | **Total Tokens:** {tot_toks:,} | **Total Cost:** ${tot_cost:.4f}\n\n"
                
                # Add overview
                if intro and intro.get("content"):
                    out += "## Overview\n\n" + intro["content"] + "\n\n"
                
                # Add the main content sections
                for r in results[1:-1]:
                    if r and r.get("query") and r.get("content"):
                        out += f"## {r['query']}\n\n" + r["content"] + "\n\n"
                
                # Add conclusion
                if concl and concl.get("content"):
                    out += "## Conclusion\n\n" + concl["content"] + "\n\n"
            else:
                # Built-in deep research (single query)
                out = f"# Deep Research Results: {opts.get('query', results[0].get('query', 'Research Topic') if results else 'Research Topic')}\n\n"
                out += f"*Generated using Perplexity's built-in deep research model*\n\n"
                out += f"**Model:** {model} | **Total Tokens:** {tot_toks:,} | **Total Cost:** ${tot_cost:.4f}\n\n"
                
                # Just include the content directly
                if results and results[0] and results[0].get("content"):
                    out += results[0]["content"]
        else:
            # Regular multi-query output
            qps = results[0].get("metadata", {}).get("queries_per_second", 0) if results else 0
            et = results[0].get("metadata", {}).get("elapsed_time", 0) if results else 0
            
            out = f"# Combined Query Results\n\nSummary:\n\n"
            out += f"Totals | Model: {model} | {len(results)} queries | {tot_toks:,} tokens | ${tot_cost:.4f} | {et:.1f}s ({qps:.2f} q/s)\n\n"
            out += f"Results saved to: {format_path(out_dir)}\n\n"
            
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

    # Index with SEMA for future cache hits
    index_with_sema(Path(out_file))

    rel_path = format_path(out_file)
    
    # Handle viewing content directly vs showing paths based on --view flag
    if not opts.get("quiet", False):
        # Auto-view content if it's a single result OR if --view flag is explicitly used
        should_view = opts.get("view") or (len(results) == 1 and fmt == "markdown")
        
        if should_view and fmt == "markdown":
            # Display content directly
            print("\n📊 Query Results:")
            
            if is_deep and not is_custom_deep:
                # For built-in deep research, just show the main content
                if results and results[0]:
                    content = results[0].get("content", "")
                    view_lines = opts.get("view_lines")
                    max_lines = view_lines if view_lines is not None else 200
                    
                    content_lines = content.split('\n')
                    if len(content_lines) > max_lines:
                        # Show limited content with message about remaining lines
                        for line in content_lines[:max_lines]:
                            print(line)
                        remaining = len(content_lines) - max_lines
                        print(f"\n... {remaining} more lines not shown.")
                    else:
                        print(content)
            else:
                # For regular multi-query or custom deep research
                for i, r in enumerate(results):
                    if r and "query" in r and "content" in r:
                        # Get max lines to display
                        view_lines = opts.get("view_lines")
                        max_lines = view_lines if view_lines is not None else 200
                        
                        print(f"\n📝 Query {i+1}: {r['query']}")
                        
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
            
            # Always show where the file is saved
            print(f"\nFull results saved to: {rel_path}")
        else:
            # Only show the combined results message for multiple queries, not single queries
            if len(results) > 1 or is_deep:
                # Only mention the combined file if no_combine is not set
                if not opts.get("no_combine", False):
                    print(f"Results saved to: {rel_path}")
                
                # Only show command suggestions if we're not already viewing the content with --view
                if fmt == "markdown" and not is_deep:
                    suggest_cat_commands(results, out_dir)
            else:
                # For single results that aren't being viewed, show where the file is saved
                print(f"Results saved to: {rel_path}")
    
    # Also include the stats summary
    if not opts.get("quiet", False):
        print(f"\n{len(results)} queries | {tot_toks:,}T | ${tot_cost:.4f}")
    
    return results