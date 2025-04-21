#!/usr/bin/env python3
"""
Main CLI entry point for ASKP.
Preserves Click command structure and provides a drop-in replacement.
"""
import os
import re
import sys
import json
import time
import click
import pathlib
from typing import Dict, List, Optional, Tuple, Union, Any

from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from .executor import execute_query, handle_multi_query, output_result, output_multi_results
from .api import search_perplexity
from .codecheck import handle_code_check
from .formatters import format_json, format_markdown, format_text
from .file_utils import format_path, get_file_stats, generate_cat_commands
from .utils import (format_size, sanitize_filename, load_api_key, get_model_info, 
                   normalize_model_name, estimate_cost, get_output_dir,
                   generate_combined_filename, generate_unique_id)
from .bgrun_integration import notify_query_completed, notify_multi_query_completed, update_askp_status_widget
console = Console()
VERSION = "2.4.1"

def setup_deep_research(quiet: bool, model: str, temperature: float, reasoning_set: bool, output_dir: str, custom: bool = False) -> Tuple[bool, dict]:
    """Set up deep research mode."""
    opts = {
        "temperature": temperature or 0.7,
        "output_dir": output_dir
    }
    
    if custom:
        # Use our custom implementation (multiple parallel queries)
        if not quiet:
            print("Custom deep research mode enabled (multiple parallel queries).")
        opts["deep"] = True
        opts["custom_deep_research"] = True
        
        # Ensure model is set to a reasoning model if not specified
        if not reasoning_set:
            opts["model"] = "sonar-reasoning-pro"
        else:
            opts["model"] = model
    else:
        # Use Perplexity's built-in deep research model
        if not quiet:
            print("Deep research mode enabled (using Perplexity's built-in model).")
        opts["model"] = "sonar-deep-research"
        # We still need to process the result but we don't need the multi-query processing
        opts["deep"] = False
        opts["custom_deep_research"] = False
    
    # Create component directory for custom deep research
    if custom:
        comp_dir = os.path.join(opts["output_dir"], "components")
        os.makedirs(comp_dir, exist_ok=True)
        
        # Remember the original output dir for final results
        final_out_dir = opts["output_dir"]
        opts["final_output_dir"] = final_out_dir
        
        # Set component dir for intermediate results
        opts["output_dir"] = comp_dir
    
    return True, opts

@click.command()
@click.version_option(version=VERSION, prog_name="askp")
@click.argument("query_text", nargs=-1, required=False)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output")
@click.option(
    "--format", 
    "-f", 
    type=click.Choice(["markdown", "md", "json", "text", "txt"]), 
    default="markdown", 
    help="Output format: markdown/md, json, or text/txt"
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--num-results", "-n", type=int, default=1, help="Number of results per query")
@click.option("--model", "-m", type=str, default="sonar-reasoning", help="Model to use (sonar, sonar-reasoning, sonar-reasoning-pro)")
@click.option("--basic", "-b", is_flag=True, help="Use basic Sonar model (fastest, cheapest)")
@click.option("--reasoning-pro", "-r", is_flag=True, help="Use enhanced reasoning model (sonar-reasoning-pro)")
@click.option("--code", "-c", is_flag=True, help="Use code-optimized model (llama-3.1-sonar-small-128k-online)")
@click.option("--sonar", "-S", is_flag=True, help="Use Sonar model (same as -b)")
@click.option("--sonar-pro", "-SP", is_flag=True, help="Use Sonar Pro model (EXPENSIVE)")
@click.option("--search-depth", "-d", type=click.Choice(["low", "medium", "high"]), default="medium",
              help="Search depth: low (minimal), medium (standard), high (extensive)")
@click.option("--temperature", "-t", type=float, default=0.7, help="Temperature")
@click.option("--token_max", type=int, help="Maximum tokens to generate")
@click.option("--model-help", is_flag=True, help="Show detailed model information and costs")
@click.option("--pro-reasoning", "-pr", is_flag=True, help="Use pro reasoning mode (deprecated, use -r instead)")
@click.option("--reasoning", "-R", is_flag=True, help="Legacy reasoning flag (deprecated, use -r instead)")
@click.option("--single", "-s", is_flag=True, help="Force single query mode")
@click.option("--max-parallel", type=int, default=5, help="Maximum number of parallel queries")
@click.option("--file", "-i", type=click.Path(exists=True), help="Read queries from file, one per line")
@click.option("--no-combine", "-nc", is_flag=True, help="Don't combine results into a single file (override default combining)")
@click.option("--combine", "-c", "-C", is_flag=True, help="Combine multi-query results (default, maintained for compatibility)")
@click.option("--view", is_flag=True, help="View query results directly in terminal (using default line limit)")
@click.option("--view-lines", type=int, default=None, help="View query results with specified max lines")
@click.option("--expand", "-e", type=int, help="Expand queries to specified total number by generating related queries")
@click.option("--deep", "-D", is_flag=True, help="Perform deep research by generating a comprehensive research plan")
@click.option("--deep-custom", is_flag=True, help="Use custom deep research implementation (multiple parallel queries)")
@click.option("--cleanup-component-files", is_flag=True, help="Move component files to trash after deep research is complete")
@click.option("--quick", "-Q", is_flag=True, help="Combine all queries into a single request with short answers")
@click.option("--code-check", "-cc", type=click.Path(exists=True), help="File to check for code quality/issues")
@click.option("--debug", is_flag=True, help="Capture raw API responses for debugging")
def cli(query_text, verbose, quiet, format, output, num_results, model, basic, reasoning_pro, code, sonar, sonar_pro, 
        search_depth, temperature, token_max, model_help, pro_reasoning, reasoning, single, max_parallel, file, 
        no_combine, combine, view, view_lines, expand, deep, deep_custom, cleanup_component_files, quick, code_check, debug):
    """ASKP CLI - Search Perplexity AI from the command line"""
    # Show model help if requested
    ctx = click.get_current_context()
    if model_help:
        display_model_help()
        ctx.exit()
        
    # Select model based on flags (priority order)
    if basic or sonar:
        model = "sonar"
    elif reasoning_pro or pro_reasoning:
        model = "sonar-reasoning-pro"
    elif code:
        model = "llama-3.1-sonar-small-128k-online"
    elif sonar_pro:
        model = "sonar-pro"
    elif reasoning:
        # Handle legacy reasoning flag - try to maintain compatibility
        if model == "sonar":
            model = "sonar-reasoning"
        elif model == "sonar-pro":
            model = "sonar-reasoning-pro"
        
    # Normalize the model name
    model = normalize_model_name(model)
    token_max_set = token_max is not None
    reasoning_set = reasoning or reasoning_pro or pro_reasoning
    queries = []
    if code_check:
        queries = handle_code_check(code_check, list(query_text), single, quiet)
    elif file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                queries.extend([l.strip() for l in f if l.strip()])
        except Exception as e:
            rprint(f"Error reading query file: {e}")
            sys.exit(1)
    if query_text and not queries:
        # Don't join the queries into one unless single mode is explicitly requested
        if single:
            queries.append(" ".join(query_text))
        else:
            # Process each argument as a separate query
            for arg in query_text:
                if not arg.startswith("-"):  # Skip anything that looks like an option flag
                    queries.append(arg)
    elif not queries and not sys.stdin.isatty():
        queries.extend([l.strip() for l in sys.stdin.read().splitlines() if l.strip()])
    if not queries:
        click.echo(ctx.get_help())
        ctx.exit()
    opts: Dict[str, Any] = {"verbose": verbose, "quiet": quiet, "format": format, "output": output, "num_results": num_results,
         "model": model, "temperature": temperature, "max_tokens": token_max, "reasoning": reasoning_set, 
         "search_depth": search_depth, "combine": not no_combine, "max_parallel": max_parallel, 
         "token_max_set_explicitly": token_max_set, "reasoning_set_explicitly": reasoning_set, 
         "output_dir": get_output_dir(), "multi": not single,
         "cleanup_component_files": cleanup_component_files, "view": view, "view_lines": view_lines, "quick": quick, "debug": debug,
         "no_combine": no_combine}
    if expand:
        opts["expand"] = expand
    if deep and deep_custom:
        # Both flags are set - prioritize custom
        is_deep, deep_opts = setup_deep_research(quiet, model, temperature, reasoning_set, opts["output_dir"], custom=True)
        opts.update(deep_opts)
    elif deep_custom:
        # Use custom deep research
        is_deep, deep_opts = setup_deep_research(quiet, model, temperature, reasoning_set, opts["output_dir"], custom=True)
        opts.update(deep_opts)
    elif deep:
        # Use Perplexity's built-in deep research
        is_deep, deep_opts = setup_deep_research(quiet, model, temperature, reasoning_set, opts["output_dir"], custom=False)
        opts.update(deep_opts)
    
    # Process quick mode - combine all queries into one
    if quick and len(queries) > 1:
        combined_query = " ".join([f"Q{i+1}: {q}" for i, q in enumerate(queries)])
        if not quiet:
            print(f"Quick mode: Combining {len(queries)} queries into one request")
        from .executor import execute_query, output_result
        r = execute_query(combined_query, 0, opts)
        if not r:
            print("Error: Failed to get response from Perplexity API")
            sys.exit(1)
        output_result(r, opts)
    elif expand and expand > len(queries):
        print(f"Expanding {len(queries)} queries to {expand} total queries...")
        from .expand import generate_expanded_queries
        queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)
    elif not single or file or len(queries) > 1:
        from .executor import handle_multi_query, output_multi_results
        res = handle_multi_query(queries, opts)
        if not res:
            print("Error: Failed to process queries")
            sys.exit(1)
        output_multi_results(res, opts)
    else:
        from .executor import execute_query, output_result
        r = execute_query(queries[0], 0, opts)
        if not r:
            print("Error: Failed to get response from Perplexity API")
            sys.exit(1)
        output_result(r, opts)

def display_model_help():
    """Display model help information."""
    help_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "model_help.md")
    if os.path.exists(help_file):
        with open(help_file, "r") as f:
            content = f.read()
        console.print(Markdown(content))
    else:
        console.print("Model help file not found. Visit https://github.com/caseyfenton/askp for documentation.")

def main() -> None:
    """Main entry point for the ASKP CLI."""
    cli()

if __name__ == "__main__":
    main()