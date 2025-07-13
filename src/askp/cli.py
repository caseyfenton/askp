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
import openai
OpenAI = openai.OpenAI
# from .codecheck import handle_code_check  # Module doesn't exist, commenting out
from .formatters import format_json, format_markdown, format_text
from .file_utils import format_path, get_file_stats, generate_cat_commands
from .utils import (load_api_key, format_size, sanitize_filename, get_model_info, 
                   normalize_model_name, estimate_cost, get_output_dir,
                   generate_combined_filename, generate_unique_id)
console = Console()
VERSION = "2.4.4"

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

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

@click.command(context_settings=CONTEXT_SETTINGS)
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
@click.option("--model", "-m", type=str, default="sonar-reasoning", help="Model to use (see --model-help for full details)")
@click.option("--basic", "-b", is_flag=True, help="Use basic Sonar model (fastest, cheapest, good for simple factual queries)")
@click.option("--reasoning-pro", "-r", is_flag=True, help="⚠️ EXPENSIVE: Use enhanced reasoning model (10-20x cost, better for complex analysis)")
@click.option("--code", "-X", is_flag=True, help="Use code-optimized model (best for programming questions, technical analysis)")
@click.option("--sonar", "-S", is_flag=True, help="Use basic Sonar model (same as -b)")
@click.option("--sonar-pro", "-SP", is_flag=True, help="⚠️ VERY EXPENSIVE: Use Sonar Pro model (20x cost, only for critical research)")
@click.option("--search-depth", "-d", type=click.Choice(["low", "medium", "high"]), default="medium",
              help="Search depth: low (minimal info, fastest), medium (balanced), high (comprehensive, slower)")
@click.option("--temperature", "-t", type=float, default=0.7, help="Temperature (0.1-1.0): lower for focused/deterministic, higher for creative responses")
@click.option("--token_max", type=int, help="Maximum tokens to generate (controls response length)")
@click.option("--model-help", is_flag=True, help="Show detailed model information, capabilities, and cost comparison")
@click.option("--pro-reasoning", "-pr", is_flag=True, help="[DEPRECATED] Use --reasoning-pro (-r) instead")
@click.option("--reasoning", "-R", is_flag=True, help="[DEPRECATED] Use --reasoning-pro (-r) instead")
@click.option("--single", "-s", is_flag=True, help="Force single query mode even with multiple queries (prevents parallel processing)")
@click.option("--max-parallel", type=int, default=5, help="Maximum number of parallel queries (higher values = faster but more API load)")
@click.option("--file", "-i", type=click.Path(exists=True), help="Read queries from file, one per line")
@click.option("--no-combine", "-nc", is_flag=True, help="Save each query result to a separate file (overrides default combining)")
@click.option("--combine", "-C", is_flag=True, help="Combine multi-query results into one file (this is the default)")
@click.option("--view", is_flag=True, help="Display query results directly in terminal (in addition to saving)")
@click.option("--view-lines", type=int, default=None, help="Set maximum number of lines to display in terminal")
@click.option("--expand", "-e", type=int, help="Generate additional related queries to reach this total (e.g. -e 5 turns 1 query into 5)")
@click.option("--deep", "-D", is_flag=True, help="Use Perplexity's built-in deep research mode (faster, more efficient)")
@click.option("--deep-custom", is_flag=True, help="Use custom multi-query deep research (more transparent, good for specialized research)")
@click.option("--cleanup-component-files", is_flag=True, help="Remove intermediate files after deep research completes")
@click.option("--comprehensive", "--comp", "-c", is_flag=True, help="Process each query separately with comprehensive results (slower but more detailed)")
@click.option("--quick", "-Q", is_flag=True, help="[DEPRECATED] Quick mode is now the default (combining multiple questions into a single API call)")
@click.option("--code-check", "-cc", type=click.Path(exists=True), help="Check code file for bugs, improvements, and security issues")
@click.option("--debug", is_flag=True, help="Save raw API responses for debugging and analysis")
@click.option("--account-status", "--credits", is_flag=True, help="Check account status and remaining API credits")
@click.option("--account-details", is_flag=True, help="Show detailed account information including rate limits")
def cli(query_text, verbose, quiet, format, output, num_results, model, basic, reasoning_pro, code, sonar, sonar_pro, 
        search_depth, temperature, token_max, model_help, pro_reasoning, reasoning, single, max_parallel, file, 
        no_combine, combine, view, view_lines, expand, deep, deep_custom, cleanup_component_files, comprehensive, quick, code_check, debug,
        account_status, account_details):
    """ASKP - Advanced knowledge search using Perplexity AI

    Run natural language searches directly from your terminal. Use multiple queries,
    deep research modes, and specialized models for different types of questions.
    
    Simple Example: askp "What is quantum computing?"
    
    Multi-query Example: askp "Python packaging" "Virtual environments" "Poetry vs pip"  # Combined by default
    
    Comprehensive Mode: askp -c "Python packaging" "Virtual environments" "Poetry vs pip"  # Process separately
    
    Deep Research: askp -D "History and impact of renewable energy"
    
    For detailed model information and costs, use: askp --model-help
    """
    # Show model help if requested
    ctx = click.get_current_context()
    if model_help:
        display_model_help()
        ctx.exit()
        
    # Check account status if requested (should happen before query processing)
    if account_status or account_details:
        handle_account_status_check(verbose=account_details)
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
    
    # ⚠️ COST WARNING FOR EXPENSIVE MODELS ⚠️
    expensive_models = ["sonar-reasoning-pro", "sonar-pro", "reasoning-pro", "pro"]
    if any(expensive in model.lower() for expensive in expensive_models):
        if not quiet:
            rprint("\n" + "="*80)
            rprint("[bold red]⚠️  EXPENSIVE MODEL WARNING - USE WITH CAUTION ⚠️[/bold red]")
            rprint("="*80)
            rprint(f"[bold yellow]You are using model: {model}[/bold yellow]")
            rprint("[bold red]THIS MODEL IS 10-20X MORE EXPENSIVE THAN STANDARD MODELS[/bold red]")
            rprint("[yellow]- Only use for complex reasoning tasks that require advanced capabilities[/yellow]")
            rprint("[yellow]- Consider using 'sonar-reasoning' or 'sonar' for most queries[/yellow]")
            rprint("[yellow]- Each query may cost significantly more API credits[/yellow]")
            rprint("="*80 + "\n")
    
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
         "cleanup_component_files": cleanup_component_files, "view": view, "view_lines": view_lines, "quick": quick, "comprehensive": comprehensive, "debug": debug,
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
    
    # Process queries based on mode
    if expand and expand > len(queries):
        print(f"Expanding {len(queries)} queries to {expand} total queries...")
        from .expand import generate_expanded_queries
        queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)
    # Process comprehensive mode (old default behavior)
    elif comprehensive and len(queries) > 1:
        if not quiet:
            print("\n⏳ Processing queries in comprehensive mode...")
            if debug:
                print(f"   Model: {model} | Temperature: {temperature}")
            print("   Each query processed separately for detailed results")
            print("   Please wait...\n")
        
        from .executor import handle_multi_query, output_multi_results
        res = handle_multi_query(queries, opts)
        if not res:
            print("Error: Failed to process queries")
            sys.exit(1)
        output_multi_results(res, opts)
    # Process multiple queries with default (quick) mode
    elif len(queries) > 1:
        combined_query = " ".join([f"Q{i+1}: {q}" for i, q in enumerate(queries)])
        if not quiet:
            print(f"\n⏳ Processing {len(queries)} queries in combined mode (default)...")
            if debug:
                print(f"   Model: {model} | Temperature: {temperature}")
            print("   Please wait...\n")
        from .executor import execute_query, output_result
        r = execute_query(combined_query, 0, opts)
        if not r:
            print("Error: Failed to get response from Perplexity API")
            sys.exit(1)
        output_result(r, opts)
    else:
        # Display processing message
        if not quiet:
            print("\n⏳ Processing query with Perplexity API...")
            if debug:
                print(f"   Model: {model} | Temperature: {temperature}")
            print("   Please wait...\n")
        
        from .executor import execute_query, output_result
        r = execute_query(queries[0], 0, opts)
        if not r:
            print("Error: Failed to get response from Perplexity API")
            sys.exit(1)
        output_result(r, opts)

    # Check account status
    if account_status or account_details:
        handle_account_status_check(verbose=verbose)

def handle_account_status_check(verbose=False):
    """Handle the account status check command."""
    from .api import display_account_status
    display_account_status(verbose=verbose)

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