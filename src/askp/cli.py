#!/usr/bin/env python3
"""ASKP – Ask Perplexity CLI with Multi-Query Support. Interface to the Perplexity API for search and knowledge discovery."""
import os, sys, json, uuid, threading, click, time, re, shutil
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from openai import OpenAI
from .cost_tracking import log_query_cost
console = Console(); VERSION = "2.4.1"
def sanitize_filename(q: str) -> str:
    s = ''.join(c if c.isalnum() else '_' for c in q); return s[:50] if s.strip('_') else "query"
def load_api_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY"); 
    if key: return key
    for p in [Path.home()/".env", Path.home()/" .perplexity"/".env", Path.home()/" .askp"/".env"]:
        if p.exists():
            try:
                for line in p.read_text().splitlines():
                    if line.startswith("PERPLEXITY_API_KEY="): return line.split("=",1)[1].strip().strip('"\'' )
            except Exception as e: rprint(f"[yellow]Warning: Error reading {p}: {e}[/yellow]")
    rprint("[red]Error: Could not find Perplexity API key.[/red]"); sys.exit(1)
def get_model_info(m: str, reasoning: bool=False, pro_reasoning: bool=False) -> dict:
    if reasoning: return {"id": "reasoning", "model": "sonar-reasoning", "cost_per_million":5.00, "reasoning":True}
    if pro_reasoning: return {"id": "pro-reasoning", "model": "sonar-reasoning-pro", "cost_per_million":8.00, "reasoning":True}
    return {"id": m, "model": m, "cost_per_million":1.00, "reasoning":False}
def estimate_cost(toks: int, model_info: dict) -> float:
    return (toks/1_000_000)*model_info["cost_per_million"]
def search_perplexity(q: str, opts: dict) -> dict:
    m = opts.get("model", "sonar-pro"); temp = opts.get("temperature", 0.7); max_tokens = opts.get("max_tokens",8192)
    if opts.get("deep",False) and not opts.get("token_max_set_explicitly",False): max_tokens=16384
    reasoning = opts.get("reasoning",False); pro_reasoning = opts.get("pro_reasoning",False)
    model_info = get_model_info(m, reasoning, pro_reasoning); m = model_info["model"]
    try:
        api_key = load_api_key(); client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        messages = [{"role": "user", "content": q}]; ib = len(q.encode("utf-8"))
        resp = client.chat.completions.create(model=m, messages=messages, temperature=temp, max_tokens=max_tokens, stream=False)
        content = resp.choices[0].message.content; ob = len(content.encode("utf-8")); total = resp.usage.total_tokens
        if not opts.get("suppress_model_display",False):
            disp = model_info["model"] + (" (reasoning)" if reasoning or pro_reasoning else ""); print(f"[{disp} | Temp: {temp}]")
        try: log_query_cost(str(uuid.uuid4()), model_info, total, os.path.basename(os.getcwd()))
        except Exception as e: rprint(f"[yellow]Warning: Failed to log query cost: {e}[/yellow]")
        return {"query":q, "results":[{"content":content}], "citations":[], "model":m, "tokens":total, "bytes":ib+ob,
                "metadata":{"model":m, "tokens":total, "cost":estimate_cost(total,model_info),"num_results":1,"verbose":opts.get("verbose",False)},
                "model_info":model_info, "tokens_used":total}
    except Exception as e: rprint(f"[red]Error in search_perplexity: {e}[/red]"); return None
def get_output_dir() -> str:
    d = Path(os.getcwd())/"perplexity_results"; d.mkdir(exist_ok=True); return str(d)
def save_result_file(q: str, res: dict, i: int, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    fname = f"{i:03d}_{sanitize_filename(q)[:50]}.json"; fpath = os.path.join(out_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f: json.dump(res, f, indent=2)
    return fpath
def append_to_combined(q: str, res: dict, i: int, out_dir: str, lock: threading.Lock) -> str:
    combined = os.path.join(out_dir, "combined_results.md")
    with lock:
        with open(combined, "a", encoding="utf-8") as f:
            f.write(f"\n\n## Query {i+1}: {q}\n\n"); f.write(res["results"][0]["content"]); f.write("\n\n---\n\n")
    return combined
def execute_query(q: str, i: int, opts: dict, lock: threading.Lock=None) -> dict:
    res = search_perplexity(q, opts); 
    if not res: return None
    od = get_output_dir(); rf = save_result_file(q, res, i, od)
    if opts.get("combine") and lock: 
        cf = append_to_combined(q, res, i, od, lock); rprint(f"[green]Combined results saved to {cf}[/green]")
    if opts.get("suppress_model_display",False):
        t = q[:40]+"..." if len(q)>40 else q; print(f"Query {i+1}: {t} | {res.get('bytes',0):,} bytes | {res.get('tokens',0):,} tokens | ${res['metadata']['cost']:.4f}")
    rprint(f"[green]Result saved: {rf}[/green]"); return res
def handle_multi_query(queries: list, opts: dict) -> list:
    print(f"\nProcessing {len(queries)} queries in parallel..."); 
    mi = get_model_info(opts.get("model", "sonar-pro"), opts.get("reasoning",False), opts.get("pro_reasoning",False))
    print(f"Model: {mi['model']}{' (reasoning)' if mi.get('reasoning',False) else ''} | Temp: {opts.get('temperature',0.7)}")
    opts["suppress_model_display"] = True; lock = threading.Lock(); results = []; total_tokens = 0; total_cost = 0; start = time.time()
    max_workers = opts.get("max_parallel",10)
    with ThreadPoolExecutor(max_workers=min(max_workers, len(queries))) as ex:
        futures = {ex.submit(execute_query, q, i, opts, lock): i for i, q in enumerate(queries)}
        for f in futures:
            try:
                r = f.result(); 
                if r: results.append(r); total_tokens += r.get("tokens",0); total_cost += r["metadata"].get("cost",0)
            except Exception as e: rprint(f"[red]Error in future: {e}[/red]")
    elapsed = time.time()-start; qps = len(results)/elapsed if elapsed>0 else 0
    if opts.get("deep",False) and len(results)>1:
        try:
            if opts.get("verbose",False): rprint("[blue]Synthesizing research results...[/blue]")
            from .deep_research import synthesize_research
            sections = {}
            for i, r in enumerate(results):
                if i==0: continue
                sec = f"Section {i}: {r.get('query','')}"
                content = r.get("results", [{}])[0].get("content", "")
                sections[sec] = content
            orig = opts.get("research_overview", results[0]["query"])
            if isinstance(orig, tuple): orig = " ".join(orig)
            synthesis = synthesize_research(query=orig, results=sections, model=opts.get("model","sonar-pro"), temperature=opts.get("temperature",0.7))
            intro = {"query":"Introduction","content":synthesis.get("introduction",""),"tokens":int(len(synthesis.get("introduction","").split())*1.3),
                     "metadata":{"cost":int(len(synthesis.get("introduction","").split())*1.3)*0.000001,"verbose":opts.get("verbose",False),"model":opts.get("model","sonar-pro"),"tokens":int(len(synthesis.get("introduction","").split())*1.3),"num_results":1}}
            concl = {"query":"Conclusion","content":synthesis.get("conclusion",""),"tokens":int(len(synthesis.get("conclusion","").split())*1.3),
                     "metadata":{"cost":int(len(synthesis.get("conclusion","").split())*1.3)*0.000001,"verbose":opts.get("verbose",False),"model":opts.get("model","sonar-pro"),"tokens":int(len(synthesis.get("conclusion","").split())*1.3),"num_results":1}}
            results.insert(0,intro); results.append(concl); total_tokens += intro["tokens"]+concl["tokens"]; total_cost += intro["metadata"]["cost"]+concl["metadata"]["cost"]
        except Exception as e:
            if opts.get("verbose",False): rprint(f"[yellow]Warning: Failed to synthesize research: {e}[/yellow]")
    print("\nProcessing complete!"); od = get_output_dir()
    if len(results)==1: print(f"Result: {od}/{os.path.basename(save_result_file(results[0]['query'], results[0], 0, od))}")
    else: print(f"Results: {od}")
    print(f"Queries: {len(results)}/{len(queries)}"); tb = sum(r.get("bytes",0) for r in results if r)
    print(f"Totals | {tb:,} bytes | {total_tokens:,} tokens | ${total_cost:.4f} | {elapsed:.1f}s ({qps:.2f} q/s)")
    if results: 
        results[0]["metadata"].update({"queries_per_second":qps,"elapsed_time":elapsed,"output_dir":od})
    return results
def handle_deep_research(query, opts):
    from .deep_research import generate_research_plan, process_research_plan
    plan = generate_research_plan(query, opts)
    if not plan: rprint("[red]Error: Failed to generate research plan[/red]"); return None
    opts["deep"] = True; opts["query"] = query
    res = process_research_plan(plan, opts)
    if res:
        for r in res:
            if r and "metadata" in r and "file_path" not in r.get("metadata", {}):
                if "components_dir" in opts and "query" in r:
                    s = re.sub(r'[^\w\s-]', '', r["query"]).strip().replace(' ', '_')[:30]
                    idx = res.index(r); fname = f"{idx:03d}_{s}.json"; fpath = os.path.join(opts["components_dir"], fname)
                    if os.path.exists(fpath): r["metadata"]["file_path"] = fpath
    return res
def format_json(res: dict) -> str: return json.dumps(res, indent=2)
def format_markdown(res: dict) -> str:
    p = ["# Search Results\n"]
    if res.get("metadata",{}).get("verbose",False):
        p += [f"**Query:** {res.get('query','No query')}", f"**Model:** {res.get('metadata',{}).get('model','Unknown')}", f"**Tokens Used:** {res.get('metadata',{}).get('tokens',0)}", f"**Estimated Cost:** ${res.get('metadata',{}).get('cost',0):.6f}\n"]
    if "content" in res: p.append(res["content"])
    elif "results" in res and res["results"] and "content" in res["results"][0]: p.append(res["results"][0]["content"])
    else: p.append("No content available")
    if res.get("citations") and res.get("metadata",{}).get("verbose",False):
        p.append("\n**Citations:**"); p += [f"- {c}" for c in res["citations"]]
    if res.get("metadata",{}).get("verbose",False):
        p.append("\n## Metadata"); 
        for k,v in res.get("metadata",{}).items():
            p.append(f"- **{k}:** {f'${v:.6f}' if k=='cost' else v}")
    return "\n".join(p)
def format_text(res: dict) -> str:
    p = ["=== Search Results ==="]
    if res.get("metadata",{}).get("verbose",False):
        p += [f"Query: {res.get('query','No query')}", f"Model: {res.get('metadata',{}).get('model','Unknown')}", f"Tokens: {res.get('metadata',{}).get('tokens',0)}", f"Cost: ${res.get('metadata',{}).get('cost',0):.6f}\n"]
    if "content" in res: p.append(res["content"])
    elif "results" in res and res["results"] and "content" in res["results"][0]: p.append(res["results"][0]["content"])
    else: p.append("No content available")
    return "\n".join(p)
def output_result(res: dict, opts: dict) -> None:
    if not res or opts.get("quiet",False): return
    fmt = opts.get("format","markdown")
    out = format_json(res) if fmt=="json" else (format_text(res) if fmt=="text" else format_markdown(res))
    if fmt in {"markdown","text"}:
        disp = res.get("model","") + (" (reasoning)" if res.get("model_info",{}).get("reasoning",False) else "")
        out += f"\n{disp} | {res.get('tokens_used',0):,} tokens | ${res.get('metadata',{}).get('cost',0):.4f}"
    if opts.get("output"):
        p = Path(opts["output"]); 
        if not p.parent.exists(): rprint(f"[red]Error: Directory {p.parent} does not exist[/red]")
        else:
            try: p.write_text(out, encoding="utf-8"); rprint(f"[green]Output saved to {opts['output']}[/green]")
            except PermissionError: rprint(f"[red]Error: Permission denied writing to {opts['output']}[/red]")
    else:
        if fmt=="markdown": console.print(Markdown(out))
        else: click.echo(out)
    if not opts.get("quiet") and fmt!="json": rprint(f"[blue]Results directory: {get_output_dir()}[/blue]")
    if not opts.get("quiet",False) and not opts.get("multi",False):
        from .tips import get_formatted_tip; tip = get_formatted_tip(); 
        if tip: rprint(tip)
def output_multi_results(results: list, opts: dict) -> None:
    if not results: return
    out_dir = opts.get("output_dir", os.path.join(os.getcwd(),"perplexity_results")); os.makedirs(out_dir, exist_ok=True)
    is_deep = opts.get("deep",False); overview = opts.get("research_overview","")
    if isinstance(overview, (tuple,list)): overview = " ".join(str(x) for x in overview)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S"); fmt = opts.get("format","markdown")
    ext = "md" if fmt=="markdown" else ("json" if fmt=="json" else "txt")
    if is_deep:
        s_query = re.sub(r'[^\w\s-]','',overview).strip().replace(' ','_')[:30]
        fname = f"deep_research_{s_query}_{ts}.{ext}"
    elif len(results)==1:
        s_query = re.sub(r'[^\w\s-]','',results[0].get("query","")).strip().replace(' ','_')[:30]
        fname = f"query_result_{s_query}_{ts}.{ext}"
    else: fname = f"multi_query_results_{ts}.{ext}"
    out_fp = os.path.join(out_dir, fname)
    if fmt=="json":
        combined = [json.loads(format_json(r)) for r in results if r]
        if is_deep: combined.insert(0, {"research_overview": overview})
        out = json.dumps(combined, indent=2)
    elif fmt=="markdown":
        if is_deep:
            qdisp = overview if isinstance(overview,str) else " ".join(overview)
            out = f"# Deep Research: {qdisp}\n\n## Research Overview\n\n{qdisp}\n\n## Research Findings\n\n"
            for i, r in enumerate(results):
                if r: out += f"### {i+1}. {r.get('query','Section '+str(i+1))}\n\n" + format_markdown(r) + "\n\n" + "-"*50 + "\n\n"
            tot_toks = sum(r.get("tokens",0) for r in results if r); tot_cost = sum(r.get("metadata",{}).get("cost",0) for r in results if r)
            qps = results[0].get("metadata",{}).get("queries_per_second",0) if results else 0; et = results[0].get("metadata",{}).get("elapsed_time",0) if results else 0
            out += f"\n## Summary\n\nTotals | Model: {opts.get('model','sonar-pro')} | {len(results)} queries | {tot_toks:,} tokens | ${tot_cost:.4f} | {et:.1f}s ({qps:.2f} q/s)\n\nResults: {out_fp}\n"
        else:
            out = "# Multiple Query Results\n\n" if len(results)>1 else "# Single Query Result\n\n"
            for i, r in enumerate(results):
                if r: 
                    qdisp = r.get('query','Query '+str(i+1))[:50]+"..." if len(r.get('query',''))>50 else r.get('query','')
                    out += f"## Query {i+1}: {qdisp}\n\n" + format_markdown(r) + "\n\n" + "-"*50 + "\n\n"
            tot_toks = sum(r.get("tokens",0) for r in results if r); tot_cost = sum(r.get("metadata",{}).get("cost",0) for r in results if r)
            out += f"\n## Summary\n\nTotals | {len(results)} queries | {tot_toks:,} tokens | ${tot_cost:.4f}\n\nResults: {out_fp}\n"
    else:
        if is_deep:
            qdisp = overview if isinstance(overview,str) else " ".join(overview)
            out = f"=== Deep Research: {qdisp} ===\n\n=== Research Overview ===\n\n{qdisp}\n\n=== Research Findings ===\n\n"
            for i, r in enumerate(results):
                if r: out += f"=== {i+1}. {r.get('query','Section '+str(i+1))} ===\n\n" + format_text(r) + "\n\n" + "="*50 + "\n\n"
            tot_toks = sum(r.get("tokens",0) for r in results if r); tot_cost = sum(r.get("metadata",{}).get("cost",0) for r in results if r)
            qps = results[0].get("metadata",{}).get("queries_per_second",0) if results else 0; et = results[0].get("metadata",{}).get("elapsed_time",0) if results else 0
            out += "=== Summary ===\n\n" + f"Totals | Model: {opts.get('model','sonar-pro')} | {len(results)} queries | {tot_toks:,} tokens | ${tot_cost:.4f} | {et:.1f}s ({qps:.2f} q/s)\n\nResults: {out_fp}\n"
        else:
            out = "=== Multi-Query Results ===\n\n" if len(results)>1 else "=== Single Query Result ===\n\n"
            for i, r in enumerate(results):
                if r: 
                    qdisp = r.get('query','Query '+str(i+1))[:50]+"..." if len(r.get('query',''))>50 else r.get('query','')
                    out += f"=== Query {i+1}: {qdisp} ===\n\n" + format_text(r) + "\n\n" + "="*50 + "\n\n"
            tot_toks = sum(r.get("tokens",0) for r in results if r); tot_cost = sum(r.get("metadata",{}).get("cost",0) for r in results if r)
            out += "=== Summary ===\n\n" + f"Totals | {len(results)} queries | {tot_toks:,} tokens | ${tot_cost:.4f}\n\nResults: {out_fp}\n"
    with open(out_fp, "w", encoding="utf-8") as f: f.write(out)
    if not opts.get("quiet",False) and (len(results)==1 or opts.get("verbose",False)):
        if fmt=="markdown": console.print(Markdown(out))
        else: click.echo(out)
    return out_fp
@click.command()
@click.version_option(version=VERSION, prog_name="askp")
@click.argument("query_text", nargs=-1, required=False)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress console output for multiple queries")
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
@click.option("--file", "-i", type=click.Path(exists=True), help="Read queries from file, one per line")
@click.option("--combine", "-c", is_flag=True, help="Combine multi-query results into a single output")
@click.option("--expand", "-e", type=int, help="Expand queries to specified total number by generating related queries")
@click.option("--deep", "-d", is_flag=True, help="Perform deep research by generating a comprehensive research plan")
@click.option("--cleanup-component-files", is_flag=True, help="Move component files to trash after deep research is complete")
def cli(query_text, verbose, quiet, format, output, num_results, model, temperature, token_max, reasoning, pro_reasoning, single, max_parallel, file, combine, expand, deep, cleanup_component_files):
    """ASKP CLI - Search Perplexity AI from the command line"""
    if reasoning and pro_reasoning:
        rprint("[red]Error: Cannot use both --reasoning and --pro-reasoning together[/red]"); sys.exit(1)
    ctx = click.get_current_context(); 
    token_max_set = 'token_max' in ctx.params; reasoning_set = 'reasoning' in ctx.params or 'pro_reasoning' in ctx.params
    queries = []
    if file:
        try:
            with open(file, 'r', encoding='utf-8') as f: queries.extend([l.strip() for l in f if l.strip()])
        except Exception as e: rprint(f"[red]Error reading query file: {e}[/red]"); sys.exit(1)
    if query_text:
        queries.append(" ".join(query_text)) if single else queries.extend(list(query_text))
    elif not queries and not sys.stdin.isatty():
        queries.extend([l.strip() for l in sys.stdin.read().splitlines() if l.strip()])
    if not queries:
        click.echo(ctx.get_help()); ctx.exit()
    opts = {"verbose":verbose, "quiet":quiet, "format":format, "output":output, "num_results":num_results, "model":model, "temperature":temperature, "max_tokens":token_max, "reasoning":reasoning, "pro_reasoning":pro_reasoning, "combine":combine, "max_parallel":max_parallel, "token_max_set_explicitly":token_max_set, "reasoning_set_explicitly":reasoning_set, "output_dir":get_output_dir(), "multi":not single, "cleanup_component_files":cleanup_component_files}
    if expand:
        opts["expand"] = expand
    if deep:
        if not quiet: rprint("[blue]Deep research mode enabled. Generating research plan...[/blue]")
        if not reasoning_set: opts["model"] = "sonar-pro"
        if not quiet: rprint(f"[blue]Using model: {opts['model']} | Temperature: {opts['temperature']}[/blue]")
        comp_dir = os.path.join(opts["output_dir"], "components"); os.makedirs(comp_dir, exist_ok=True)
        final_out_dir = opts["output_dir"]; opts["components_dir"] = comp_dir; opts["deep"] = True; opts["cleanup_component_files"] = cleanup_component_files; opts["query"] = queries[0]
        res = handle_deep_research(queries[0], opts)
        opts["output_dir"] = final_out_dir
        if not res: rprint("[red]Error: Failed to process queries[/red]"); sys.exit(1)
        output_multi_results(res, opts)
    elif expand and expand > len(queries):
        rprint(f"[blue]Expanding {len(queries)} queries to {expand} total queries...[/blue]")
        from .expand import generate_expanded_queries; queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)
    elif not single or file or len(queries) > 1:
        res = handle_multi_query(queries, opts)
        if not res: rprint("[red]Error: Failed to process queries[/red]"); sys.exit(1)
        output_multi_results(res, opts)
    else:
        r = execute_query(queries[0], 0, opts)
        if not r: rprint("[red]Error: Failed to get response from Perplexity API[/red]"); sys.exit(1)
        output_result(r, opts)
def main(): cli()
if __name__=="__main__": main()