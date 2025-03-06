#!/usr/bin/env python3
"""ASKP – Ask Perplexity CLI with Multi-Query Support. Interface to the Perplexity API for search and knowledge discovery."""
import os, sys, json, uuid, threading, click, time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from openai import OpenAI
from .cost_tracking import log_query_cost
import re
console = Console(); VERSION = "2.4.0"
def sanitize_filename(query: str) -> str:
    safe = ''.join(c if c.isalnum() else '_' for c in query); return safe[:50] if safe.strip('_') else "query"
def load_api_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY"); 
    if key: return key
    for p in [Path.home() / ".env", Path.home() / ".perplexity" / ".env", Path.home() / ".askp" / ".env"]:
        if p.exists():
            try:
                for line in p.read_text().splitlines():
                    if line.startswith("PERPLEXITY_API_KEY="): return line.split("=",1)[1].strip().strip('"\'' )
            except Exception as e: rprint(f"[yellow]Warning: Error reading {p}: {e}[/yellow]")
    rprint("[red]Error: Could not find Perplexity API key.[/red]"); sys.exit(1)
def get_model_info(model_name: str, reasoning: bool=False, pro_reasoning: bool=False) -> dict:
    if reasoning: return {"id": "reasoning", "model": "sonar-reasoning", "cost_per_million": 5.00, "reasoning": True}
    if pro_reasoning: return {"id": "pro-reasoning", "model": "sonar-reasoning-pro", "cost_per_million": 8.00, "reasoning": True}
    return {"id": model_name, "model": model_name, "cost_per_million": 1.00, "reasoning": False}
def estimate_cost(tokens_used: int, model_info: dict) -> float:
    return (tokens_used / 1_000_000) * model_info["cost_per_million"]
def search_perplexity(query: str, options: dict) -> dict:
    model = options.get("model", "sonar-pro")
    temperature = options.get("temperature", 0.7)
    max_tokens = options.get("max_tokens", 8192)
    
    # For deep research, use higher token limits if not explicitly set
    if options.get("deep", False) and not options.get("token_max_set_explicitly", False):
        max_tokens = 16384  # Use 16k tokens for deep research
    
    reasoning = options.get("reasoning", False)
    pro_reasoning = options.get("pro_reasoning", False)
    model_info = get_model_info(model, reasoning, pro_reasoning)
    model = model_info["model"]
    try:
        api_key = load_api_key(); client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        messages = [{"role": "user", "content": query}]; input_bytes = len(query.encode("utf-8"))
        response = client.chat.completions.create(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens, stream=False)
        content = response.choices[0].message.content; output_bytes = len(content.encode("utf-8")); total_tokens = response.usage.total_tokens
        if not options.get("suppress_model_display", False):
            disp = model_info["model"] + (" (reasoning)" if reasoning or pro_reasoning else ""); print(f"[{disp} | Temp: {temperature}]")
        try: log_query_cost(str(uuid.uuid4()), model_info, total_tokens, os.path.basename(os.getcwd()))
        except Exception as e: rprint(f"[yellow]Warning: Failed to log query cost: {e}[/yellow]")
        return {"query": query, "results": [{"content": content}], "citations": [], "model": model, "tokens": total_tokens,
                "bytes": input_bytes + output_bytes, "metadata": {"model": model, "tokens": total_tokens, "cost": estimate_cost(total_tokens, model_info),
                "num_results": 1, "verbose": options.get("verbose", False)}, "model_info": model_info, "tokens_used": total_tokens}
    except Exception as e:
        rprint(f"[red]Error in search_perplexity: {e}[/red]"); return None
def get_output_dir() -> str:
    out_dir = Path(os.getcwd()) / "perplexity_results"; out_dir.mkdir(exist_ok=True); return str(out_dir)
def save_result_file(query: str, result: dict, index: int, output_dir: str) -> str:
    """Save result to a file and return the filename."""
    os.makedirs(output_dir, exist_ok=True)
    sanitized = sanitize_filename(query)
    filename = f"{index:03d}_{sanitized[:50]}.json"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return filepath
def append_to_combined(query: str, result: dict, index: int, output_dir: str, lock: threading.Lock) -> str:
    """Append result to combined file and return the filename."""
    os.makedirs(output_dir, exist_ok=True)
    combined_file = os.path.join(output_dir, "combined_results.md")
    with lock:
        with open(combined_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n## Query {index+1}: {query}\n\n")
            f.write(result["results"][0]["content"])
            f.write("\n\n---\n\n")
    return combined_file
def execute_query(query: str, index: int, options: dict, lock: threading.Lock = None) -> dict:
    result = search_perplexity(query, options); 
    if not result: return None
    out_dir = get_output_dir(); 
    result_file = save_result_file(query, result, index, out_dir)
    if options.get("combine") and lock: 
        combined_file = append_to_combined(query, result, index, out_dir, lock)
        rprint(f"[green]Combined results saved to {combined_file}[/green]")
    if options.get("suppress_model_display", False):
        truncated = query[:40] + "..." if len(query) > 40 else query; print(f"Query {index+1}: {truncated} | {result.get('bytes',0):,} bytes | {result.get('tokens',0):,} tokens | ${result['metadata']['cost']:.4f}")
    rprint(f"[green]Result saved to {result_file}[/green]")
    return result
def handle_multi_query(queries: list, options: dict) -> list:
    """Process multiple queries, with support for deep research mode."""
    # Track if token_max was explicitly set by the user
    token_max_set_explicitly = "max_tokens" in options
    
    # Adjust token limit for deep research if not explicitly set
    if options.get("deep", False) and not token_max_set_explicitly:
        options["max_tokens"] = 16384
        options["token_max_set_explicitly"] = False
    else:
        options["token_max_set_explicitly"] = token_max_set_explicitly
    
    # Adjust reasoning settings for deep research
    reasoning_set_explicitly = "reasoning" in options
    pro_reasoning_set_explicitly = "pro_reasoning" in options
    
    # For deep research, enable reasoning by default unless explicitly set
    if options.get("deep", False) and not reasoning_set_explicitly and not pro_reasoning_set_explicitly:
        options["reasoning"] = True
    
    # Save the original query for output file naming
    if options.get("deep", False) and len(queries) > 0:
        if isinstance(queries[0], str):
            options["query"] = queries[0]
    
    print(f"\nProcessing {len(queries)} queries in parallel..."); 
    
    model_info = get_model_info(options.get("model", "sonar-pro"), options.get("reasoning", False), options.get("pro_reasoning", False))
    print(f"Model: {model_info['model']}{' (reasoning)' if model_info.get('reasoning', False) else ''} | Temperature: {options.get('temperature',0.7)}")
    options["suppress_model_display"] = True; results_lock = threading.Lock(); results = []; total_tokens = 0; total_cost = 0
    
    # Track start time for queries per second calculation
    start_time = time.time()
    
    max_workers = options.get("max_parallel", 10)
    with ThreadPoolExecutor(max_workers=min(max_workers, len(queries))) as executor:
        futures = {executor.submit(execute_query, q, i, options, results_lock): i for i, q in enumerate(queries)}
        for future in futures:
            try:
                res = future.result(); 
                if res: results.append(res); total_tokens += res.get("tokens", 0); total_cost += res["metadata"]["cost"]
            except Exception as e: rprint(f"[red]Error in future: {e}[/red]")
    
    # Calculate elapsed time and queries per second
    elapsed_time = time.time() - start_time
    queries_per_second = len(results) / elapsed_time if elapsed_time > 0 else 0
    
    # Synthesize the results if deep research is enabled
    if options.get("deep", False) and len(results) > 1:
        try:
            if options.get("verbose", False): rprint("[blue]Synthesizing research results...[/blue]")
            
            # Import the synthesis functions
            from .deep_research import synthesize_research, apply_synthesis
            
            # Create a dictionary of section titles to content
            section_results = {}
            for i, r in enumerate(results):
                if i == 0:  # Skip the original query
                    continue
                section_title = f"Section {i}: {r['query']}"
                # Handle different result structures
                if 'content' in r:
                    section_results[section_title] = r['content']
                elif 'results' in r and r['results'] and 'content' in r['results'][0]:
                    section_results[section_title] = r['results'][0]['content']
            
            # Get the original query
            original_query = options.get("research_overview", results[0]['query'])
            # Handle case where query is a tuple (from CLI arguments)
            if isinstance(original_query, tuple):
                original_query = " ".join(original_query)
            
            # Synthesize the research
            synthesis = synthesize_research(
                query=original_query,
                results=section_results,
                model=options.get("model", "sonar-pro"),
                temperature=options.get("temperature", 0.7)
            )
            
            # Add the introduction and conclusion to the results
            intro_result = {
                "query": "Introduction",
                "content": synthesis["introduction"],
                "tokens": len(synthesis["introduction"].split()) * 1.3,  # Estimate tokens
                "metadata": {
                    "cost": len(synthesis["introduction"].split()) * 1.3 * 0.000001,
                    "verbose": options.get("verbose", False),
                    "model": options.get("model", "sonar-pro"),
                    "tokens": len(synthesis["introduction"].split()) * 1.3,
                    "num_results": 1
                }
            }
            
            conclusion_result = {
                "query": "Conclusion",
                "content": synthesis["conclusion"],
                "tokens": len(synthesis["conclusion"].split()) * 1.3,  # Estimate tokens
                "metadata": {
                    "cost": len(synthesis["conclusion"].split()) * 1.3 * 0.000001,
                    "verbose": options.get("verbose", False),
                    "model": options.get("model", "sonar-pro"),
                    "tokens": len(synthesis["conclusion"].split()) * 1.3,
                    "num_results": 1
                }
            }
            
            # Insert at beginning and end
            results.insert(0, intro_result)
            results.append(conclusion_result)
            
            # Update total tokens and cost
            total_tokens += intro_result["tokens"] + conclusion_result["tokens"]
            total_cost += intro_result["metadata"]["cost"] + conclusion_result["metadata"]["cost"]
            
        except Exception as e:
            if options.get("verbose", False): rprint(f"[yellow]Warning: Failed to synthesize research: {e}[/yellow]")
    
    print("\nProcessing complete!"); 
    output_dir = get_output_dir()
    print(f"Results saved in directory: {output_dir}"); 
    print(f"Queries processed: {len(results)}/{len(queries)}"); 
    print(f"Total tokens used: {total_tokens:,}"); 
    print(f"Total cost: ${total_cost:.4f}");
    print(f"Performance: {elapsed_time:.1f}s ({queries_per_second:.2f} queries/second)");
    
    # Store metrics in results for use in output_multi_results
    if results:
        results[0]["metadata"]["queries_per_second"] = queries_per_second
        results[0]["metadata"]["elapsed_time"] = elapsed_time
        results[0]["metadata"]["output_dir"] = output_dir
    
    return results
def handle_deep_research(query: str, options: dict) -> list:
    """Handle deep research mode with multiple queries."""
    from .deep_research import create_research_queries, synthesize_research
    
    # Set deep research flag
    options["deep"] = True
    
    # Store the original query for output filename
    options["query"] = query
    
    # Generate research queries
    queries = create_research_queries(query, options.get("model", "sonar-pro"), options.get("temperature", 0.7))
    
    # Process the queries
    results = handle_multi_query(queries, options)
    
    # Synthesize the research results
    if results:
        print("Synthesizing research results...")
        try:
            synthesis = synthesize_research(query, results, options)
            if synthesis:
                print("Successfully generated research synthesis.")
                results.append(synthesis)
            else:
                print("Failed to generate research synthesis.")
        except Exception as e:
            print(f"Warning: Failed to synthesize research: {str(e)}")
            # Create a basic synthesis result
            synthesis = {
                "query": f"Research Synthesis: {query}",
                "content": f"# {query}\n\n## Introduction\n\nResearch on: {query}\n\n## Conclusion\n\nBased on the research conducted, further investigation is recommended.",
                "model": options.get("model", "sonar-pro"),
                "tokens": 0,
                "cost": 0,
                "num_results": 1,
                "verbose": options.get("verbose", True)
            }
            results.append(synthesis)
    
    return results
def format_json(result: dict) -> str: return json.dumps(result, indent=2)
def format_markdown(result: dict) -> str:
    parts = ["# Search Results\n"]
    if result.get("metadata", {}).get("verbose", False):
        parts.extend([f"**Query:** {result.get('query', 'No query')}", 
                     f"**Model:** {result.get('metadata', {}).get('model', 'Unknown model')}", 
                     f"**Tokens Used:** {result.get('metadata', {}).get('tokens', 0)}", 
                     f"**Estimated Cost:** ${result.get('metadata', {}).get('cost', 0):.6f}\n"])
    
    # Handle different result structures
    if "content" in result:
        parts.append(result["content"])
    elif "results" in result and result["results"] and "content" in result["results"][0]:
        parts.append(result["results"][0]["content"])
    else:
        parts.append("No content available")
    
    if result.get("citations") and result.get("metadata", {}).get("verbose", False):
        parts.append("\n**Citations:**"); parts.extend(f"- {c}" for c in result["citations"])
    
    if result.get("metadata", {}).get("verbose", False):
        parts.append("\n## Metadata"); 
        for key, value in result.get("metadata", {}).items():
            parts.append(f"- **{key}:** {f'${value:.6f}' if key=='cost' else value}")
    
    return "\n".join(parts)
def format_text(result: dict) -> str:
    parts = ["=== Search Results ==="]
    if result.get("metadata", {}).get("verbose", False):
        parts.extend([f"Query: {result.get('query', 'No query')}", 
                     f"Model: {result.get('metadata', {}).get('model', 'Unknown model')}", 
                     f"Tokens: {result.get('metadata', {}).get('tokens', 0)}", 
                     f"Cost: ${result.get('metadata', {}).get('cost', 0):.6f}\n"])
    
    # Handle different result structures
    if "content" in result:
        parts.append(result["content"])
    elif "results" in result and result["results"] and "content" in result["results"][0]:
        parts.append(result["results"][0]["content"])
    else:
        parts.append("No content available")
    
    return "\n".join(parts)
def output_result(result: dict, options: dict) -> None:
    """Output a single query result in the specified format."""
    if not result or options.get("quiet", False): return
    
    fmt = options.get("format", "markdown")
    formatted = format_json(result) if fmt == "json" else (format_text(result) if fmt == "text" else format_markdown(result))
    
    # Add model and token information for text and markdown formats
    if fmt in {"markdown", "text"}:
        model_disp = result.get("model", "") + (" (reasoning)" if result.get("model_info", {}).get("reasoning", False) else "")
        formatted += f"\n{model_disp} | {result.get('tokens_used', 0):,} tokens | ${result.get('metadata', {}).get('cost', 0):.4f}"
    
    if options.get("output"):
        p = Path(options["output"])
        if not p.parent.exists():
            rprint(f"[red]Error: Directory {p.parent} does not exist[/red]")
        else:
            try:
                p.write_text(formatted, encoding="utf-8")
                rprint(f"[green]Output saved to {options['output']}[/green]")
            except PermissionError:
                rprint(f"[red]Error: Permission denied writing to {options['output']}[/red]")
    else:
        if fmt == "markdown":
            console.print(Markdown(formatted))
        else:
            click.echo(formatted)
    
    # Always show the output directory for individual results too
    if not options.get("quiet") and fmt != "json":
        rprint(f"[blue]Results directory: {get_output_dir()}[/blue]")
    
    # Show a random tip if in single query mode
    if not options.get("quiet", False) and not options.get("multi", False):
        from .tips import get_formatted_tip
        tip = get_formatted_tip()
        if tip:
            rprint(tip)
def output_multi_results(results: list, options: dict) -> None:
    """Output multiple query results in the specified format."""
    if not results: return
    
    # Create output directory if it doesn't exist
    output_dir = options.get("output_dir", os.path.join(os.getcwd(), "perplexity_results"))
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine if this is deep research mode
    is_deep_research = options.get("deep", False)
    research_overview = options.get("research_overview", "")
    
    # Convert research_overview to string if it's a tuple or list
    if isinstance(research_overview, (tuple, list)):
        research_overview = " ".join(str(item) for item in research_overview)
    
    # Generate appropriate filename based on mode
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if is_deep_research:
        filename_prefix = "deep_research"
        # Get the main query for the filename
        main_query = options.get("query", research_overview) or "research"
        # Make sure main_query is a string
        if isinstance(main_query, (tuple, list)):
            main_query = " ".join(str(item) for item in main_query)
        # Sanitize the query for use in filename
        sanitized_query = re.sub(r'[^\w\s-]', '', main_query).strip().replace(' ', '_')[:30]
        base_filename = f"{filename_prefix}_{sanitized_query}_{timestamp}"
    else:
        base_filename = f"multi_query_results_{timestamp}"
    
    # Add appropriate extension based on format
    format_type = options.get("format", "markdown")
    if format_type == "json":
        output_filepath = os.path.join(output_dir, f"{base_filename}.json")
    elif format_type == "markdown":
        output_filepath = os.path.join(output_dir, f"{base_filename}.markdown")
    else:
        output_filepath = os.path.join(output_dir, f"{base_filename}.txt")
    
    # Prepare output
    if format_type=="json":
        combined = [json.loads(format_json(r)) for r in results if r]
        # Add research overview to JSON output if in deep research mode
        if is_deep_research:
            combined.insert(0, {"research_overview": research_overview})
        out = json.dumps(combined, indent=2)
    elif format_type=="markdown":
        if is_deep_research:
            # Special formatting for deep research
            query_display = research_overview if isinstance(research_overview, str) else " ".join(research_overview)
            out = f"# Deep Research: {query_display}\n\n"
            out += f"## Research Overview\n\n{query_display}\n\n"
            out += "## Research Findings\n\n"
            for i, r in enumerate(results):
                if r: 
                    # Safely get the query value, using a default if not present
                    query_text = r.get('query', f"Research Section {i+1}")
                    out += f"### {i+1}. {query_text}\n\n" + format_markdown(r) + "\n\n"
            
            # Add summary
            total_tokens = sum(r.get("tokens", 0) for r in results if r)
            total_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
            queries_per_second = results[0].get("metadata", {}).get("queries_per_second", 0) if results else 0
            elapsed_time = results[0].get("metadata", {}).get("elapsed_time", 0) if results else 0
            
            out += "\n## Summary\n\n"
            out += f"* Total Queries: {len(results)}\n"
            out += f"* Total Tokens: {total_tokens:,}\n"
            out += f"* Total Cost: ${total_cost:.4f}\n"
            out += f"* Performance: {elapsed_time:.1f}s ({queries_per_second:.2f} queries/second)\n"
            out += f"* Results Directory: {output_dir}\n"
            out += f"* Output File: {output_filepath}\n"
        else:
            # Regular multi-query output
            out = "# Multiple Query Results\n\n"
            for i, r in enumerate(results):
                if r: 
                    # Safely get the query value, using a default if not present
                    query_text = r.get('query', f"Query {i+1}")
                    query_display = query_text[:50] + "..." if len(query_text) > 50 else query_text
                    out += f"## Query {i+1}: {query_display}\n\n" + format_markdown(r) + "\n\n" + "-"*50 + "\n\n"
            
            # Add summary
            total_tokens = sum(r.get("tokens", 0) for r in results if r)
            total_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
            
            out += "\n## Summary\n\n"
            out += f"* Total Queries: {len(results)}\n"
            out += f"* Total Tokens: {total_tokens:,}\n"
            out += f"* Total Cost: ${total_cost:.4f}\n"
            out += f"* Results Directory: {output_dir}\n"
            out += f"* Output File: {output_filepath}\n"
    else:
        # Text format
        if is_deep_research:
            # Special formatting for deep research in text mode
            query_display = research_overview if isinstance(research_overview, str) else " ".join(research_overview)
            out = f"=== Deep Research: {query_display} ===\n\n"
            out += f"=== Research Overview ===\n\n{query_display}\n\n"
            out += "=== Research Findings ===\n\n"
            for i, r in enumerate(results):
                if r: 
                    # Safely get the query value, using a default if not present
                    query_text = r.get('query', f"Research Section {i+1}")
                    out += f"=== {i+1}. {query_text} ===\n\n" + format_text(r) + "\n\n" + "="*50 + "\n\n"
            
            # Add summary
            total_tokens = sum(r.get("tokens", 0) for r in results if r)
            total_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
            queries_per_second = results[0].get("metadata", {}).get("queries_per_second", 0) if results else 0
            elapsed_time = results[0].get("metadata", {}).get("elapsed_time", 0) if results else 0
            
            out += "=== Summary ===\n\n"
            out += f"Total Queries: {len(results)}\n"
            out += f"Total Tokens: {total_tokens:,}\n"
            out += f"Total Cost: ${total_cost:.4f}\n"
            out += f"Performance: {elapsed_time:.1f}s ({queries_per_second:.2f} queries/second)\n"
            out += f"Results Directory: {output_dir}\n"
            out += f"Output File: {output_filepath}\n"
        else:
            # Regular multi-query output in text mode
            out = "=== Multi-Query Results ===\n\n"
            for i, r in enumerate(results):
                if r: 
                    # Safely get the query value, using a default if not present
                    query_text = r.get('query', f"Query {i+1}")
                    query_display = query_text[:50] + "..." if len(query_text) > 50 else query_text
                    out += f"=== Query {i+1}: {query_display} ===\n\n" + format_text(r) + "\n\n" + "="*50 + "\n\n"
            
            # Add summary
            total_tokens = sum(r.get("tokens", 0) for r in results if r)
            total_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
            
            out += "=== Summary ===\n\n"
            out += f"Total Queries: {len(results)}\n"
            out += f"Total Tokens: {total_tokens:,}\n"
            out += f"Total Cost: ${total_cost:.4f}\n"
            out += f"Results Directory: {output_dir}\n"
            out += f"Output File: {output_filepath}\n"
    
    # Write to file
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(out)
    
    # Output to console
    if format_type == "markdown":
        console.print(Markdown(out))
    else:
        click.echo(out)
    
    # Always show the output filepath
    rprint(f"[blue]Results saved to: {output_filepath}[/blue]")
@click.command()
@click.version_option(version=VERSION, prog_name="askp")
@click.argument("query_text", nargs=-1, required=False)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except results")
@click.option("--format", "-f", type=click.Choice(["text", "json", "markdown"]), default="markdown", help="Output format")
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
@click.option("--num-results", "-n", type=int, default=5, help="Number of results to return from Perplexity")
@click.option("--model", default="sonar-pro", help="Model to use (default: sonar-pro)")
@click.option("--temperature", type=float, default=0.7, help="Temperature (0.0-1.0)")
@click.option("--token-max", "-t", type=int, default=8192, help="Maximum tokens to use")
@click.option("--reasoning", "-r", is_flag=True, help="Use reasoning model ($5.00 per million tokens)")
@click.option("--pro-reasoning", is_flag=True, help="Use pro reasoning model ($8.00 per million tokens)")
@click.option("--single", "-s", is_flag=True, help="Process all arguments as a single query (default is multi-query mode)")
@click.option("--max-parallel", type=int, default=5, help="Maximum number of parallel queries")
@click.option("--file", "-f", type=click.Path(exists=True), help="Read queries from file, one per line")
@click.option("--combine", "-c", is_flag=True, help="Combine multi-query results into a single output")
@click.option("--expand", "-e", type=int, help="Expand queries to specified total number by generating related queries")
@click.option("--deep", "-d", is_flag=True, help="Perform deep research by generating a comprehensive research plan")
def cli(query_text, verbose, quiet, format, output, num_results, model, 
        temperature, token_max, reasoning, pro_reasoning, single, 
        max_parallel, file, combine, expand, deep):
    """ASKP CLI - Search Perplexity AI from the command line"""
    
    # Check for incompatible options
    if reasoning and pro_reasoning:
        rprint("[red]Error: Cannot use both --reasoning and --pro-reasoning together[/red]")
        sys.exit(1)
    
    # Track if token_max and reasoning were explicitly set
    ctx = click.get_current_context()
    token_max_set_explicitly = 'token_max' in ctx.params
    reasoning_set_explicitly = 'reasoning' in ctx.params or 'pro_reasoning' in ctx.params
    
    # Process queries
    queries = []
    
    # Handle file input
    if file:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                file_queries = [line.strip() for line in f if line.strip()]
                queries.extend(file_queries)
        except Exception as e:
            rprint(f"[red]Error reading query file: {e}[/red]")
            sys.exit(1)
    
    # Handle direct query input
    if query_text:
        if single:
            queries.append(" ".join(query_text))
        else:
            queries.extend(list(query_text))
    # Handle stdin if no query or file provided
    elif not queries and not sys.stdin.isatty():
        queries.extend([line.strip() for line in sys.stdin.read().splitlines() if line.strip()])
    
    # Ensure we have at least one query
    if not queries:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()
    
    # Set up common options
    options = {
        "verbose": verbose, 
        "quiet": quiet, 
        "format": format, 
        "output": output, 
        "num_results": num_results, 
        "model": model, 
        "temperature": temperature, 
        "max_tokens": token_max, 
        "reasoning": reasoning, 
        "pro_reasoning": pro_reasoning, 
        "combine": combine, 
        "max_parallel": max_parallel, 
        "token_max_set_explicitly": token_max_set_explicitly, 
        "reasoning_set_explicitly": reasoning_set_explicitly, 
        "output_dir": get_output_dir(),
        "multi": not single
    }
    
    # Handle deep research mode
    if deep:
        if verbose: rprint("[blue]Deep research mode enabled. Generating research plan...[/blue]")
        # Add the query to options for filename generation
        main_query = queries[0] if queries else "research"
        options["query"] = main_query
        options["deep"] = True
        results = handle_deep_research(main_query, options)
        if not results: 
            rprint("[red]Error: Failed to process queries[/red]")
            sys.exit(1)
        output_multi_results(results, options)
    
    # Handle query expansion if requested
    elif expand and expand > len(queries):
        if not quiet:
            rprint(f"[blue]Expanding {len(queries)} queries to {expand} total queries...[/blue]")
        from .expand import generate_expanded_queries
        queries = generate_expanded_queries(
            queries, 
            expand, 
            model=model, 
            temperature=temperature
        )
    
    # Process queries based on mode
    elif not single or file or len(queries) > 1:
        results = handle_multi_query(queries, options)
        if not results: 
            rprint("[red]Error: Failed to process queries[/red]")
            sys.exit(1)
        output_multi_results(results, options)
    else:
        res = execute_query(queries[0], 0, options)
        if not res: 
            rprint("[red]Error: Failed to get response from Perplexity API[/red]")
            sys.exit(1)
        output_result(res, options)

def main():
    cli()

if __name__ == "__main__":
    main()