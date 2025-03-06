#!/usr/bin/env python3
"""
ASKP – Advanced Search Knowledge Discovery CLI with Multi-Query Support
Integrated with Reflex City for powerful search and knowledge discovery.
"""
import os
import sys
import json
import click
import threading
from pathlib import Path
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from openai import OpenAI
from datetime import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Tuple, Optional

from .cost_tracking import analyze_costs, log_query_cost

VERSION = "2.1.0"  # Updated for multi-query support
console = Console()

def sanitize_filename(query: str) -> str:
    """Create a safe filename from a query string."""
    safe_name = ''.join(c if c.isalnum() else '_' for c in query)
    # Limit length to 50 characters
    return safe_name[:50] if safe_name.strip('_') else "query"

def load_api_key() -> str:
    """Load Perplexity API key from environment variable or environment file."""
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if api_key:
        return api_key

    env_paths = [
        os.path.expanduser('~/.env'),
        os.path.expanduser('~/.perplexity/.env'),
        os.path.expanduser('~/.askp/.env'),
    ]
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.startswith('PERPLEXITY_API_KEY='):
                            key = line.split('=')[1].strip().strip('"').strip("'")
                            return key
            except Exception as e:
                rprint(f"[yellow]Warning: Error reading {env_path}: {e}[/yellow]")
    
    rprint("[red]Error: Could not find Perplexity API key.[/red]")
    sys.exit(1)

def get_model_info(model_name: str, reasoning: bool = False, pro_reasoning: bool = False) -> Dict[str, Any]:
    """Get model information including cost per million tokens."""
    if reasoning:
        return {
            'id': 'reasoning',
            'model': 'sonar-reasoning',
            'cost_per_million': 5.00,
            'reasoning': True
        }
    elif pro_reasoning:
        return {
            'id': 'pro-reasoning',
            'model': 'sonar-reasoning-pro',
            'cost_per_million': 8.00,
            'reasoning': True
        }
    return {
        'id': model_name,
        'model': model_name,
        'cost_per_million': 1.00,
        'reasoning': False
    }

def estimate_cost(tokens_used: int, model_info: Dict[str, Any]) -> float:
    """Calculate cost based on actual tokens used and model."""
    return (tokens_used / 1_000_000) * model_info['cost_per_million']

def search_perplexity(query: str, options: dict) -> Dict[str, Any]:
    """
    Search using Perplexity API with optional reasoning models.
    
    Args:
        query: The search query
        options: Dictionary of search options
    
    Returns:
        Dict containing response content, citations, and model info
    """
    model = options.get('model', 'sonar-pro')
    temperature = options.get('temperature', 0.7)
    max_tokens = options.get('max_tokens', 8192)
    reasoning = options.get('reasoning', False)
    pro_reasoning = options.get('pro_reasoning', False)
    
    # Update model based on reasoning flags
    model_info = get_model_info(model, reasoning, pro_reasoning)
    model = model_info['model']
    
    try:
        api_key = load_api_key()
        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        
        # Prepare the messages
        messages = [{"role": "user", "content": query}]
        
        # Calculate input bytes
        input_bytes = len(query.encode('utf-8'))
        
        # Make the API call
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        # Extract content and calculate output bytes
        content = response.choices[0].message.content
        output_bytes = len(content.encode('utf-8'))
        citations = []  # Citations will be extracted from the content if present
        
        # Get actual token usage
        total_tokens = response.usage.total_tokens
        
        # Only display model info if not suppressed (for multi-query mode)
        if not options.get('suppress_model_display', False):
            model_display = model_info['model']
            if reasoning or pro_reasoning:
                model_display += " (reasoning)"
            print(f"[{model_display} | Temp: {temperature}]")
        
        # Log the cost of this query
        try:
            project = os.path.basename(os.getcwd())
            log_query_cost(str(uuid.uuid4()), model_info, total_tokens, project)
        except Exception as e:
            # Don't fail the main operation if logging fails
            rprint(f"[yellow]Warning: Failed to log query cost: {str(e)}[/yellow]")
        
        return {
            'query': query,
            'results': [{'content': content}],
            'citations': citations,
            'model': model,
            'tokens': total_tokens,
            'bytes': input_bytes + output_bytes,
            'metadata': {
                'model': model,
                'tokens': total_tokens,
                'cost': estimate_cost(total_tokens, model_info),
                'num_results': 1,
                'verbose': options.get('verbose', False)
            },
            'model_info': model_info,
            'tokens_used': total_tokens,
        }
    except Exception as e:
        rprint(f"[red]Error in search_perplexity: {str(e)}[/red]")
        return None

def process_query(query: str, index: int, options: dict, results_lock: threading.Lock) -> Dict[str, Any]:
    """
    Process a single query and save its results.
    
    Args:
        query: The search query
        index: Query index for multi-query mode
        options: Dictionary of search options
        results_lock: Lock for thread-safe file operations
        
    Returns:
        Dict containing response content, citations, and model info
    """
    try:
        result = search_perplexity(query, options)
        if not result:
            return None
            
        # Display query information for multi-query mode
        if options.get('suppress_model_display', False):
            truncated_query = query[:40] + "..." if len(query) > 40 else query
            bytes_size = result.get('bytes', 0)
            tokens = result.get('tokens', 0)
            cost = result['metadata']['cost']
            print(f"Query {index+1}: {truncated_query} | {bytes_size:,} bytes | {tokens:,} tokens | ${cost:.4f}")
            
        # Create output files
        output_dir = get_output_dir()
        
        # Generate filename based on query
        base_filename = sanitize_filename(query)
        if not base_filename.strip('_'):
            base_filename = f"query_{index}"
        
        # Save individual result file
        content_path = os.path.join(output_dir, f"{base_filename}_result.md")
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(f"# Query: {query}\n\n")
            f.write("## Search Configuration\n")
            f.write(f"- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- Model: {result['model']}\n")
            if options.get('reasoning', False):
                f.write("- Mode: Reasoning\n")
            elif options.get('pro_reasoning', False):
                f.write("- Mode: Pro Reasoning\n")
            f.write(f"- Max Tokens: {options.get('max_tokens', 8192)}\n")
            f.write(f"- Temperature: {options.get('temperature', 0.7)}\n")
            f.write(f"- Tokens Used: {result['tokens']}\n")
            f.write(f"- Cost: ${result['metadata']['cost']:.4f}\n\n")
            f.write("## Result\n\n")
            content = result['results'][0]['content']
            f.write(content + "\n")
            if result.get('citations'):
                f.write("\n## Citations\n")
                for citation in result['citations']:
                    f.write(f"- {citation}\n")
        
        # If combining results is enabled, add to combined file
        if options.get('combine', False):
            combined_file = "combined_results.md"
            with results_lock:
                combined_path = os.path.join(output_dir, combined_file)
                # Create header if this is the first query
                if index == 0:
                    with open(combined_path, 'w', encoding='utf-8') as f:
                        f.write("# Perplexity Search Results\n\n")
                        f.write("## Search Configuration\n")
                        f.write(f"- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"- Model: {result['model']}\n")
                        if options.get('reasoning', False):
                            f.write("- Mode: Reasoning\n")
                        elif options.get('pro_reasoning', False):
                            f.write("- Mode: Pro Reasoning\n")
                        f.write(f"- Max Tokens: {options.get('max_tokens', 8192)}\n")
                        f.write(f"- Temperature: {options.get('temperature', 0.7)}\n\n")
                        f.write("## Results\n")
                
                # Append this query's results
                with open(combined_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n### Query {index + 1}: {query}\n")
                    f.write("-" * 40 + "\n")
                    f.write(content + "\n")
                    if result.get('citations'):
                        f.write("\nCitations:\n")
                        for citation in result['citations']:
                            f.write(f"- {citation}\n")
                    f.write("=" * 40 + "\n\n")
        return result
    except Exception as e:
        rprint(f"[red]Error processing query {index + 1}: {str(e)}[/red]")
        return None

def handle_query(query: str, options: dict) -> dict:
    """Handle a query and return results from Perplexity API."""
    result = search_perplexity(query, options)
    if result:
        # Always save single query results to file
        output_dir = get_output_dir()
        
        # Generate filename based on query
        base_filename = sanitize_filename(query)
        if not base_filename.strip('_'):
            base_filename = "query"
        
        # Save individual result file
        content_path = os.path.join(output_dir, f"{base_filename}_result.md")
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(f"# Query: {query}\n\n")
            f.write("## Search Configuration\n")
            f.write(f"- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- Model: {result['model']}\n")
            if options.get('reasoning', False):
                f.write("- Mode: Reasoning\n")
            elif options.get('pro_reasoning', False):
                f.write("- Mode: Pro Reasoning\n")
            f.write(f"- Max Tokens: {options.get('max_tokens', 8192)}\n")
            f.write(f"- Temperature: {options.get('temperature', 0.7)}\n")
            f.write(f"- Tokens Used: {result['tokens']}\n")
            f.write(f"- Cost: ${result['metadata']['cost']:.4f}\n\n")
            f.write("## Result\n\n")
            content = result['results'][0]['content']
            f.write(content + "\n")
            if result.get('citations'):
                f.write("\n## Citations\n")
                for citation in result['citations']:
                    f.write(f"- {citation}\n")
    return result

def handle_multi_query(queries: List[str], options: dict) -> List[dict]:
    """
    Handle multiple queries in parallel and return combined results.
    
    Args:
        queries: List of search queries
        options: Dictionary of search options
        
    Returns:
        List of result dictionaries
    """
    print(f"\nProcessing {len(queries)} queries in parallel...")
    
    # Display model information once at the beginning
    model = options.get('model', 'sonar-pro')
    temperature = options.get('temperature', 0.7)
    reasoning = options.get('reasoning', False)
    pro_reasoning = options.get('pro_reasoning', False)
    model_info = get_model_info(model, reasoning, pro_reasoning)
    model_display = model_info['model']
    if reasoning or pro_reasoning:
        model_display += " (reasoning)"
    print(f"Model: {model_display} | Temperature: {temperature}")
    
    # Flag to suppress model info display in search_perplexity
    options['suppress_model_display'] = True
    
    # Create a lock for thread-safe file operations
    results_lock = threading.Lock()
    
    # Get output directory
    output_dir = get_output_dir()
    
    # Process queries in parallel
    results = []
    valid_results = []
    total_tokens = 0
    total_cost = 0
    
    with ThreadPoolExecutor(max_workers=min(10, len(queries))) as executor:
        # Submit all tasks and create a mapping of futures to their index
        future_to_index = {
            executor.submit(process_query, query, i, options, results_lock): i 
            for i, query in enumerate(queries)
        }
        
        # Process results as they complete
        for future in future_to_index:
            try:
                result = future.result()
                if result:
                    index = future_to_index[future]
                    results.append(result)
                    valid_results.append(result)
                    total_tokens += result.get('tokens', 0)
                    total_cost += result['metadata'].get('cost', 0)
            except Exception as e:
                print(f"[red]Error in future: {str(e)}[/red]")
    
    # If combining results is enabled, add summary to combined file
    if options.get('combine', False) and valid_results:
        combined_file = "combined_results.md"
        combined_path = os.path.join(output_dir, combined_file)
        
        # Add summary section to the combined file
        with open(combined_path, 'a', encoding='utf-8') as f:
            f.write("\n## Summary\n\n")
            f.write(f"- Total Queries: {len(valid_results)}\n")
            f.write(f"- Total Tokens: {total_tokens:,}\n")
            f.write(f"- Total Cost: ${total_cost:.4f}\n")
    
    # Display summary
    print("\nProcessing complete!")
    print(f"Results saved in directory: {output_dir}")
    print(f"Queries processed: {len(valid_results)}/{len(queries)}")
    print(f"Total tokens used: {total_tokens:,}")
    print(f"Total cost: ${total_cost:.4f}")
    
    return results

def output_result(result: dict, options: dict):
    """Output results based on chosen format and output options."""
    if not result:
        return
    
    format_type = options.get('format', 'markdown')
    
    if format_type == 'json':
        output = format_json(result)
    elif format_type == 'markdown':
        output = format_markdown(result)
    else:
        output = format_text(result)
    
    # Add summary information for single queries
    cost = result['metadata']['cost']
    tokens = result['tokens_used']
    
    if format_type == 'markdown' or format_type == 'text':
        model_display = result['model']
        if result['model_info'].get('reasoning', False):
            model_display += " (reasoning)"
        summary_line = f"\n{model_display} | {tokens:,} tokens | ${cost:.4f}"
        output += summary_line
    
    # Handle output to file
    if options.get('output'):
        try:
            path = Path(options['output'])
            if not path.parent.exists():
                rprint(f"[red]Error: Directory {path.parent} does not exist[/red]")
            else:
                try:
                    with open(options['output'], 'w', encoding='utf-8') as f:
                        f.write(output)
                    rprint(f"[green]Output saved to {options['output']}[/green]")
                except:
                    rprint(f"[red]Error: Permission denied writing to {options['output']}[/red]")
        except:
            pass
    else:
        # Print to console
        if format_type == 'markdown':
            console = Console()
            console.print(Markdown(output))

def output_multi_results(results: List[dict], options: dict):
    """Output multiple results based on chosen format and output options."""
    # For non-combined output, display a summary of the processing
    if options['format'] == 'json':
        # Format as JSON array
        combined_results = []
        for result in results:
            if result:
                combined_results.append(json.loads(format_json(result)))
        output = json.dumps(combined_results, indent=2)
    elif options['format'] == 'markdown':
        # Format as markdown with sections for each query
        output = "# Multiple Query Results\n\n"
        
        for i, result in enumerate(results):
            if result:
                output += f"## Query {i+1}: {result['query'][:50]}...\n\n"
                output += format_markdown(result)
                output += "\n\n" + "-" * 50 + "\n\n"
        
        # Add summary section
        total_tokens = sum(r['tokens'] for r in results if r)
        total_cost = sum(r['metadata']['cost'] for r in results if r)
        output += f"\n## Summary\n\n"
        output += f"- Total Queries: {len(results)}\n"
        output += f"- Total Tokens: {total_tokens:,}\n"
        output += f"- Total Cost: ${total_cost:.4f}\n"
    else:
        # Format as plain text with sections for each query
        output = "=== Multiple Query Results ===\n\n"
        
        for i, result in enumerate(results):
            if result:
                output += f"--- Query {i+1}: {result['query'][:50]}... ---\n\n"
                output += format_text(result)
                output += "\n\n" + "-" * 50 + "\n\n"
    if options['output']:
        path = Path(options['output'])
        # Do not auto-create parent directories; require existing directory
        if not path.parent.exists():
            rprint(f"[red]Error: Directory {path.parent} does not exist[/red]")
            sys.exit(1)
        try:
            path.write_text(output)
            if not options['quiet']:
                rprint(f"[green]Output saved to {options['output']}[/green]")
        except PermissionError:
            rprint(f"[red]Error: Permission denied writing to {options['output']}[/red]")
            sys.exit(1)
    else:
        if options['format'] == 'markdown':
            console.print(Markdown(output))
        else:
            click.echo(output)

def format_json(result: dict) -> str:
    """Format result as JSON."""
    return json.dumps(result, indent=2)

def format_markdown(result: dict) -> str:
    """Format result as Markdown with rich formatting."""
    output = []
    output.append("# Search Results\n")
    
    if result['metadata']['verbose']:
        output.append(f"**Query:** {result['query']}")
        output.append(f"**Model:** {result['metadata']['model']}")
        output.append(f"**Tokens Used:** {result['metadata']['tokens']}")
        output.append(f"**Estimated Cost:** ${result['metadata']['cost']:.6f}\n")
    
    for item in result['results']:
        output.append(item['content'])
    
    if result.get('citations') and result['metadata']['verbose']:
        output.append("\n**Citations:**")
        for citation in result['citations']:
            output.append(f"- {citation}")
    
    if result['metadata']['verbose']:
        output.append("\n## Metadata")
        for key, value in result['metadata'].items():
            if key == 'cost':
                output.append(f"- **{key}:** ${value:.6f}")
            else:
                output.append(f"- **{key}:** {value}")
    
    return "\n".join(output)

def format_text(result: dict) -> str:
    """Format result as plain text."""
    output = []
    output.append("=== Search Results ===")
    
    if result['metadata']['verbose']:
        output.append(f"Query: {result['query']}")
        output.append(f"Model: {result['metadata']['model']}")
        output.append(f"Tokens: {result['metadata']['tokens']}")
        output.append(f"Cost: ${result['metadata']['cost']:.6f}\n")
    
    for item in result['results']:
        output.append(item['content'])
    
    return "\n".join(output)

def get_output_dir() -> str:
    """Get the output directory in the current working directory (or create it if it doesn't exist)."""
    # Always use the current directory for output results
    current_dir = os.path.abspath(os.getcwd())
    
    # Create output directory in current directory
    output_dir = os.path.join(current_dir, 'perplexity_results')
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

@click.command()
@click.argument('query_text', nargs=-1, required=False)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress all output except results')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'markdown']), default='markdown', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Save output to file')
@click.option('--num-results', '-n', type=int, default=5, help='Number of results to return')
@click.option('--model', default="sonar-pro", help='Model to use (default: sonar-pro)')
@click.option('--temperature', type=float, default=0.7, help='Response creativity: 0.0=focused, 1.0=creative (default: 0.7)')
@click.option('--max-tokens', type=int, default=8192, help='Maximum tokens in response (default: 8192)')
@click.option('--reasoning', '-r', is_flag=True, help='Use reasoning model ($5.00 per million tokens)')
@click.option('--pro-reasoning', is_flag=True, help='Use pro reasoning model ($8.00 per million tokens)')
@click.option('--multi', '-m', is_flag=True, help='Process each argument as a separate query in parallel')
@click.option('--file', '-i', type=click.Path(exists=True), help='File containing queries (one per line)')
@click.option('--combine', '-c', is_flag=True, help='Combine all results into a single output')
def cli(query_text, verbose, quiet, format, output, num_results, model, temperature, max_tokens, 
        reasoning, pro_reasoning, multi, file, combine):
    """ASKP – Advanced Search Knowledge Discovery CLI with Multi-Query Support"""
    queries = []
    
    # Get queries from file if specified
    if file:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                file_queries = [line.strip() for line in f if line.strip()]
                queries.extend(file_queries)
        except Exception as e:
            rprint(f"[red]Error reading queries file: {str(e)}[/red]")
            sys.exit(1)
    
    # Get queries from command line arguments
    if query_text:
        if multi:
            # In multi mode, each argument is a separate query
            queries.extend(query_text)
        else:
            # In single mode, join all arguments into one query
            query = ' '.join(query_text)
            queries.append(query)
    # If no queries from args or file, try stdin
    elif not queries and not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()
        if multi:
            # In multi mode, each line is a separate query
            queries.extend(line.strip() for line in stdin_content.split('\n') if line.strip())
        else:
            # In single mode, all stdin content is one query
            queries.append(stdin_content)
    
    # Show help if no queries found
    if not queries:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()

    # Check for conflicting flags
    if reasoning and pro_reasoning:
        rprint("[red]Error: Cannot use both --reasoning and --pro-reasoning together[/red]")
        sys.exit(1)
    
    # Create options dictionary
    options = {
        'verbose': verbose,
        'quiet': quiet,
        'format': format,
        'output': output,
        'num_results': num_results,
        'model': model,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'reasoning': reasoning,
        'pro_reasoning': pro_reasoning,
        'combine': combine
    }
    
    # Process queries
    if multi or file or len(queries) > 1:
        # Process multiple queries in parallel
        results = handle_multi_query(queries, options)
        if not results:
            rprint("[red]Error: Failed to process queries[/red]")
            sys.exit(1)
        output_multi_results(results, options)
    else:
        # Process single query
        result = handle_query(queries[0], options)
        if result is None:
            rprint("[red]Error: Failed to get response from Perplexity API[/red]")
            sys.exit(1)
        output_result(result, options)

def main():
    """Entry point for the CLI."""
    cli()

if __name__ == '__main__':
    main()
