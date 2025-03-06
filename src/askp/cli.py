#!/usr/bin/env python3
"""ASKP – Ask Perplexity CLI with Multi-Query Support. Interface to the Perplexity API for search and knowledge discovery."""
import os, sys, json, uuid, threading, click
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from openai import OpenAI
from .cost_tracking import log_query_cost
console = Console(); VERSION = "2.1.0"
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
    model = options.get("model", "sonar-pro"); temperature = options.get("temperature", 0.7); max_tokens = options.get("max_tokens", 8192)
    reasoning = options.get("reasoning", False); pro_reasoning = options.get("pro_reasoning", False)
    model_info = get_model_info(model, reasoning, pro_reasoning); model = model_info["model"]
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
def save_result_file(query: str, result: dict, index: int, output_dir: str) -> None:
    base_filename = sanitize_filename(query); 
    if not base_filename.strip("_"): base_filename = f"query_{index}"
    file_path = Path(output_dir) / f"{base_filename}_result.md"
    with file_path.open("w", encoding="utf-8") as f:
        f.write(f"# Query: {query}\n\n## Search Configuration\n- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n- Model: {result['model']}\n")
        mode = "Reasoning" if result["model_info"].get("reasoning", False) else ("Pro Reasoning" if result["model_info"].get("id") == "pro-reasoning" else "Standard")
        f.write(f"- Mode: {mode}\n- Max Tokens: {result['metadata'].get('max_tokens', 8192)}\n- Temperature: {result['metadata'].get('temperature', 0.7)}\n- Tokens Used: {result['tokens']}\n- Cost: ${result['metadata']['cost']:.4f}\n\n## Result\n\n" + result["results"][0]["content"] + "\n")
        if result.get("citations"): f.write("\n## Citations\n" + "\n".join(f"- {c}" for c in result["citations"]))
def append_to_combined(query: str, result: dict, index: int, output_dir: str, lock: threading.Lock) -> None:
    combined_path = Path(output_dir) / "combined_results.md"; header_needed = (not combined_path.exists() or combined_path.stat().st_size == 0)
    with lock, combined_path.open("a" if combined_path.exists() else "w", encoding="utf-8") as f:
        if header_needed:
            f.write("# Perplexity Search Results\n\n## Search Configuration\n- Time: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n- Model: " + result["model"] + "\n")
            if result["model_info"].get("reasoning", False): f.write("- Mode: Reasoning\n")
            elif result["model_info"].get("id") == "pro-reasoning": f.write("- Mode: Pro Reasoning\n")
            f.write(f"- Max Tokens: {result['metadata'].get('max_tokens',8192)}\n- Temperature: {result['metadata'].get('temperature',0.7)}\n\n## Results\n")
        f.write(f"\n### Query {index+1}: {query}\n" + "-"*40 + "\n" + result["results"][0]["content"] + "\n")
        if result.get("citations"): f.write("\nCitations:\n" + "\n".join(f"- {c}" for c in result["citations"]))
        f.write("="*40 + "\n\n")
def execute_query(query: str, index: int, options: dict, lock: threading.Lock = None) -> dict:
    result = search_perplexity(query, options); 
    if not result: return None
    out_dir = get_output_dir(); save_result_file(query, result, index, out_dir)
    if options.get("combine") and lock: append_to_combined(query, result, index, out_dir, lock)
    if options.get("suppress_model_display", False):
        truncated = query[:40] + "..." if len(query) > 40 else query; print(f"Query {index+1}: {truncated} | {result.get('bytes',0):,} bytes | {result.get('tokens',0):,} tokens | ${result['metadata']['cost']:.4f}")
    return result
def handle_multi_query(queries: list, options: dict) -> list:
    print(f"\nProcessing {len(queries)} queries in parallel..."); 
    model_info = get_model_info(options.get("model", "sonar-pro"), options.get("reasoning", False), options.get("pro_reasoning", False))
    print(f"Model: {model_info['model']}{' (reasoning)' if model_info.get('reasoning', False) else ''} | Temperature: {options.get('temperature',0.7)}")
    options["suppress_model_display"] = True; results_lock = threading.Lock(); results = []; total_tokens = 0; total_cost = 0
    with ThreadPoolExecutor(max_workers=min(10, len(queries))) as executor:
        futures = {executor.submit(execute_query, q, i, options, results_lock): i for i, q in enumerate(queries)}
        for future in futures:
            try:
                res = future.result(); 
                if res: results.append(res); total_tokens += res.get("tokens", 0); total_cost += res["metadata"].get("cost", 0)
            except Exception as e: rprint(f"[red]Error in future: {e}[/red]")
    print("\nProcessing complete!"); 
    print(f"Results saved in directory: {get_output_dir()}"); 
    print(f"Queries processed: {len(results)}/{len(queries)}"); 
    print(f"Total tokens used: {total_tokens:,}"); 
    print(f"Total cost: ${total_cost:.4f}"); 
    return results
def format_json(result: dict) -> str: return json.dumps(result, indent=2)
def format_markdown(result: dict) -> str:
    parts = ["# Search Results\n"]
    if result["metadata"]["verbose"]:
        parts.extend([f"**Query:** {result['query']}", f"**Model:** {result['metadata']['model']}", f"**Tokens Used:** {result['metadata']['tokens']}", f"**Estimated Cost:** ${result['metadata']['cost']:.6f}\n"])
    parts.append(result["results"][0]["content"])
    if result.get("citations") and result["metadata"]["verbose"]:
        parts.append("\n**Citations:**"); parts.extend(f"- {c}" for c in result["citations"])
    if result["metadata"]["verbose"]:
        parts.append("\n## Metadata"); 
        for key, value in result["metadata"].items():
            parts.append(f"- **{key}:** {f'${value:.6f}' if key=='cost' else value}")
    return "\n".join(parts)
def format_text(result: dict) -> str:
    parts = ["=== Search Results ==="]
    if result["metadata"]["verbose"]:
        parts.extend([f"Query: {result['query']}", f"Model: {result['metadata']['model']}", f"Tokens: {result['metadata']['tokens']}", f"Cost: ${result['metadata']['cost']:.6f}\n"])
    parts.append(result["results"][0]["content"]); return "\n".join(parts)
def output_result(result: dict, options: dict) -> None:
    if not result: return; 
    fmt = options.get("format", "markdown")
    out = format_json(result) if fmt=="json" else (format_text(result) if fmt=="text" else format_markdown(result))
    if fmt in {"markdown","text"}:
        model_disp = result["model"] + (" (reasoning)" if result["model_info"].get("reasoning", False) else "")
        out += f"\n{model_disp} | {result['tokens_used']:,} tokens | ${result['metadata']['cost']:.4f}"
    if options.get("output"):
        p = Path(options["output"])
        if not p.parent.exists(): rprint(f"[red]Error: Directory {p.parent} does not exist[/red]")
        else:
            try: p.write_text(out, encoding="utf-8"); rprint(f"[green]Output saved to {options['output']}[/green]")
            except PermissionError: rprint(f"[red]Error: Permission denied writing to {options['output']}[/red]")
    else:
        if fmt=="markdown": console.print(Markdown(out))
        else: click.echo(out)
def output_multi_results(results: list, options: dict) -> None:
    fmt = options.get("format", "markdown")
    if fmt=="json":
        combined = [json.loads(format_json(r)) for r in results if r]; out = json.dumps(combined, indent=2)
    elif fmt=="markdown":
        out = "# Multiple Query Results\n\n"
        for i, r in enumerate(results):
            if r: out += f"## Query {i+1}: {r['query'][:50]}...\n\n" + format_markdown(r) + "\n\n" + "-"*50 + "\n\n"
        total_tokens = sum(r["tokens"] for r in results if r); total_cost = sum(r["metadata"]["cost"] for r in results if r)
        out += f"\n## Summary\n\n- Total Queries: {len(results)}\n- Total Tokens: {total_tokens:,}\n- Total Cost: ${total_cost:.4f}\n"
    else:
        out = "=== Multiple Query Results ===\n\n"
        for i, r in enumerate(results):
            if r: out += f"--- Query {i+1}: {r['query'][:50]}... ---\n\n" + format_text(r) + "\n\n" + "-"*50 + "\n\n"
    if options.get("output"):
        p = Path(options["output"])
        if not p.parent.exists():
            rprint(f"[red]Error: Directory {p.parent} does not exist[/red]"); sys.exit(1)
        try: p.write_text(out, encoding="utf-8")
        except PermissionError: rprint(f"[red]Error: Permission denied writing to {options['output']}[/red]"); sys.exit(1)
        if not options.get("quiet"): rprint(f"[green]Output saved to {options['output']}[/green]")
    else:
        if fmt=="markdown": console.print(Markdown(out))
        else: click.echo(out)
@click.command()
@click.version_option(version=VERSION, prog_name="askp")
@click.argument("query_text", nargs=-1, required=False)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except results")
@click.option("--format", "-f", type=click.Choice(["text", "json", "markdown"]), default="markdown", help="Output format")
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
@click.option("--num-results", "-n", type=int, default=5, help="Number of results to return")
@click.option("--model", default="sonar-pro", help="Model to use (default: sonar-pro)")
@click.option("--temperature", type=float, default=0.7, help="Response creativity (default: 0.7)")
@click.option("--max-tokens", type=int, default=8192, help="Maximum tokens in response (default: 8192)")
@click.option("--reasoning", "-r", is_flag=True, help="Use reasoning model ($5.00 per million tokens)")
@click.option("--pro-reasoning", is_flag=True, help="Use pro reasoning model ($8.00 per million tokens)")
@click.option("--multi", "-m", is_flag=True, help="Process each argument as a separate query in parallel")
@click.option("--file", "-i", type=click.Path(exists=True), help="File containing queries (one per line)")
@click.option("--combine", "-c", is_flag=True, help="Combine all results into a single output")
def cli(query_text, verbose, quiet, format, output, num_results, model, temperature, max_tokens, reasoning, pro_reasoning, multi, file, combine):
    queries: list = []
    if file:
        try:
            with open(file, "r", encoding="utf-8") as f: queries.extend([line.strip() for line in f if line.strip()])
        except Exception as e: rprint(f"[red]Error reading queries file: {e}[/red]"); sys.exit(1)
    if query_text:
        queries.extend(query_text if multi else [" ".join(query_text)])
    elif not queries and not sys.stdin.isatty():
        queries.extend([line.strip() for line in sys.stdin.read().splitlines() if line.strip()])
    if not queries:
        ctx = click.get_current_context(); click.echo(ctx.get_help()); ctx.exit()
    if reasoning and pro_reasoning:
        rprint("[red]Error: Cannot use both --reasoning and --pro-reasoning together[/red]"); sys.exit(1)
    options = {"verbose": verbose, "quiet": quiet, "format": format, "output": output, "num_results": num_results, "model": model, "temperature": temperature, "max_tokens": max_tokens, "reasoning": reasoning, "pro_reasoning": pro_reasoning, "combine": combine}
    if multi or file or len(queries) > 1:
        results = handle_multi_query(queries, options)
        if not results: rprint("[red]Error: Failed to process queries[/red]"); sys.exit(1)
        output_multi_results(results, options)
    else:
        res = execute_query(queries[0], 0, options)
        if not res: rprint("[red]Error: Failed to get response from Perplexity API[/red]"); sys.exit(1)
        output_result(res, options)
def main(): cli()
if __name__=="__main__": main()