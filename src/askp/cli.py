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
@click.option("--model", "-m", type=str, default="sonar-pro", help="Model to use (sonar, sonar-pro)")
@click.option("--sonar", "-S", is_flag=True, help="Use Sonar model")
@click.option("--sonar-pro", "-SP", is_flag=True, help="Use Sonar Pro model (default)")
@click.option("--temperature", "-t", type=float, default=0.7, help="Temperature")
@click.option("--token_max", type=int, help="Maximum tokens to generate")
@click.option("--reasoning", "-r", is_flag=True, help="Use reasoning mode if available")
@click.option("--pro-reasoning", "-pr", is_flag=True, help="Use pro reasoning mode")
@click.option("--single", "-s", is_flag=True, help="Force single query mode")
@click.option("--max-parallel", type=int, default=5, help="Maximum number of parallel queries")
@click.option("--file", "-i", type=click.Path(exists=True), help="Read queries from file, one per line")
@click.option("--no-combine", "-nc", is_flag=True, help="Don't combine results (default is to combine)")
@click.option("--combine", "-c", "-C", is_flag=True, help="Combine multi-query results (maintained for compatibility)")
@click.option("--human", "-H", is_flag=True, help="Output in human-readable format")
@click.option("--expand", "-e", type=int, help="Expand queries to specified total number by generating related queries")
@click.option("--deep", "-d", is_flag=True, help="Perform deep research by generating a comprehensive research plan")
@click.option("--cleanup-component-files", is_flag=True, help="Move component files to trash after deep research is complete")
@click.option("--quick", "-Q", is_flag=True, help="Combine all queries into a single request with short answers")
@click.option("--code-check", "-cc", type=click.Path(exists=True), help="File to check for code quality/issues")
@click.option("--debug", is_flag=True, help="Capture raw API responses for debugging")
def cli(query_text, verbose, quiet, format, output, num_results, model, sonar, sonar_pro, temperature, token_max, reasoning, pro_reasoning, single, max_parallel, file, no_combine, combine, human, expand, deep, cleanup_component_files, quick, code_check, debug):
    """ASKP CLI - Search Perplexity AI from the command line"""
    model = "sonar" if sonar else "sonar-pro" if sonar_pro else model
    model = normalize_model_name(model)
    
    # Normalize format aliases
    if format == "md":
        format = "markdown"
    elif format == "txt":
        format = "text"
        
    if reasoning and pro_reasoning:
        rprint("[red]Error: Cannot use both --reasoning and --pro-reasoning together[/red]")
        sys.exit(1)
    ctx = click.get_current_context()
    token_max_set = "token_max" in ctx.params
    reasoning_set = "reasoning" in ctx.params or "pro_reasoning" in ctx.params
    queries = []
    if code_check:
        queries = handle_code_check(code_check, list(query_text), single, quiet)
    elif file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                queries.extend([l.strip() for l in f if l.strip()])
        except Exception as e:
            rprint(f"[red]Error reading query file: {e}[/red]")
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
         "model": model, "temperature": temperature, "max_tokens": token_max, "reasoning": reasoning, "pro_reasoning": pro_reasoning,
         "combine": not no_combine or combine, "max_parallel": max_parallel, "token_max_set_explicitly": token_max_set,
         "reasoning_set_explicitly": reasoning_set, "output_dir": get_output_dir(), "multi": not single,
         "cleanup_component_files": cleanup_component_files, "human_readable": human, "quick": quick, "debug": debug}
    if expand:
        opts["expand"] = expand
    if deep:
        if not quiet:
            rprint("[blue]Deep research mode enabled. Generating research plan...[/blue]")
        if not reasoning_set:
            opts["model"] = "sonar-pro"
        if not quiet:
            rprint(f"[blue]Using model: {opts['model']} | Temperature: {opts['temperature']}[/blue]")
        comp_dir = os.path.join(opts["output_dir"], "components")
        os.makedirs(comp_dir, exist_ok=True)
        final_out_dir = opts["output_dir"]
        opts["components_dir"] = comp_dir
        opts["deep"] = True
        opts["cleanup_component_files"] = cleanup_component_files
        opts["query"] = queries[0]
        from .executor import handle_multi_query  # Ensure proper import of deep research handling
        res = handle_multi_query(queries, opts)
        opts["output_dir"] = final_out_dir
        if not res:
            rprint("[red]Error: Failed to process queries[/red]")
            sys.exit(1)
        from .executor import output_multi_results
        output_multi_results(res, opts)
    elif quick and len(queries) > 1:
        combined_query = " ".join([f"Q{i+1}: {q}" for i, q in enumerate(queries)])
        if not quiet:
            rprint(f"[blue]Quick mode: Combining {len(queries)} queries into one request[/blue]")
        from .executor import execute_query, output_result
        r = execute_query(combined_query, 0, opts)
        if not r:
            rprint("[red]Error: Failed to get response from Perplexity API[/red]")
            sys.exit(1)
        output_result(r, opts)
    elif expand and expand > len(queries):
        rprint(f"[blue]Expanding {len(queries)} queries to {expand} total queries...[/blue]")
        from .expand import generate_expanded_queries
        queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)
    elif not single or file or len(queries) > 1:
        from .executor import handle_multi_query, output_multi_results
        res = handle_multi_query(queries, opts)
        if not res:
            rprint("[red]Error: Failed to process queries[/red]")
            sys.exit(1)
        output_multi_results(res, opts)
    else:
        from .executor import execute_query, output_result
        r = execute_query(queries[0], 0, opts)
        if not r:
            rprint("[red]Error: Failed to get response from Perplexity API[/red]")
            sys.exit(1)
        output_result(r, opts)

def main() -> None:
    """Main entry point for the ASKP CLI."""
    cli()

if __name__ == "__main__":
    main()