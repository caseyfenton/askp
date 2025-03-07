#!/usr/bin/env python3
"""Deep research module for ASKP CLI. Provides functions to generate research plans and expand a query into focused research queries."""
import json, os, re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from rich import print as rprint
from .cli import load_api_key
def generate_research_plan(query, options=None):
    if options is None: options = {}
    model = options.get("model", "sonar-pro"); temp = options.get("temperature", 0.7)
    prompt = f"""Create a comprehensive research plan to answer: "{query}" Provide 8-12 research areas and for each a specific search query. Format your response as JSON: {{"research_areas": [{{"title": "Area title", "query": "Specific search query"}}]}}"""
    from .cli import search_perplexity
    plan_result = search_perplexity(prompt, {"model": model, "temperature": temp})
    try:
        content = plan_result.get("content", "")
        if not content and plan_result.get("results"): content = plan_result["results"][0].get("content", "")
        m = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        json_str = m.group(1) if m else (re.search(r'({.*})', content, re.DOTALL).group(1) if re.search(r'({.*})', content, re.DOTALL) else content)
        data = json.loads(json_str); areas = data.get("research_areas", [])
        queries = [a.get("query", "") for a in areas if a.get("query", "")]
        if not options.get("quiet", False): print(f"Generated plan with {len(areas)} sections and {len(queries)} queries.")
        return queries
    except Exception as e:
        print(f"Error generating research plan: {e}"); return None
def create_research_queries(query, options=None):
    q = generate_research_plan(query, options)
    return q if q else [query]
def process_research_plan(queries, options):
    if not queries: return None
    if "components_dir" in options:
        orig = options.get("output_dir"); options["output_dir"] = options["components_dir"]
    from .cli import handle_multi_query
    results = handle_multi_query(queries, options)
    if "components_dir" in options and orig: options["output_dir"] = orig
    if not results: return None
    if "components_dir" in options:
        for i, r in enumerate(results):
            if r and "metadata" in r:
                s = re.sub(r'[^\w\s-]', '', r.get("query", "")).strip().replace(' ', '_')[:30]
                r["metadata"]["file_path"] = os.path.join(options["components_dir"], f"{i:03d}_{s}.json")
    try:
        if options.get("verbose", False): print("Synthesizing research results...")
        synthesis = synthesize_research(options.get("query", "Deep Research"), results, options)
        if synthesis:
            if options.get("verbose", False): print("Synthesis generated."); synthesis["metadata"] = {"file_path": None}; results.append(synthesis)
        else:
            if options.get("verbose", False): print("Synthesis generation failed.")
            results.append({"query": f"Research Synthesis: {options.get('query','Deep Research')}",
                           "content": f"# {options.get('query','Deep Research')}\n\n## Introduction\n\nResearch on: {options.get('query','Deep Research')}\n\n## Conclusion\n\nFurther investigation is recommended.",
                           "model": options.get("model", "sonar-pro"), "tokens": 0, "cost": 0, "num_results": 1, "verbose": options.get("verbose", True)})
    except Exception as e:
        if options.get("verbose", False): print(f"Warning: {e}"); results.append({"query": f"Research Synthesis: {options.get('query','Deep Research')}",
                           "content": f"# {options.get('query','Deep Research')}\n\n## Introduction\n\nResearch on: {options.get('query','Deep Research')}\n\n## Conclusion\n\nFurther investigation is recommended.",
                           "model": options.get("model", "sonar-pro"), "tokens": 0, "cost": 0, "num_results": 1, "verbose": options.get("verbose", True)})
    return results
def synthesize_research(query: str, results: List[Dict[str, Any]], options: Dict[str, Any]=None) -> Dict[str, str]:
    if options is None: options = {}
    model = options.get("model", "sonar-pro"); temp = options.get("temperature", 0.7)
    try:
        api_key = load_api_key(); client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        res_dict = {}
        for i, r in enumerate(results):
            if isinstance(r, dict):
                q = r.get("query", f"Area {i+1}"); cont = r.get("content", "")
                if not cont and r.get("results"): 
                    cont = r["results"][0].get("content", "")
                res_dict[q] = cont
        prompt = _create_synthesis_prompt(query, res_dict)
        rprint("[green]Generating research synthesis...[/green]")
        response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], temperature=temp, max_tokens=2048)
        content = response.choices[0].message.content
        try:
            js = content[content.find('{'):content.rfind('}')+1]
            synth = json.loads(js)
            rprint("[green]Synthesis generated.[/green]")
            return {"query": f"Research Synthesis: {query}", "content": f"# {query}\n\n## Introduction\n\n{synth.get('introduction','')}\n\n## Conclusion\n\n{synth.get('conclusion','')}",
                    "model": model, "tokens": response.usage.completion_tokens, "cost": response.usage.completion_tokens * 0.000001, "num_results": 1, "verbose": options.get("verbose", True)}
        except json.JSONDecodeError:
            rprint("[yellow]Warning: JSON parse failed. Creating basic synthesis.[/yellow]")
            return {"query": f"Research Synthesis: {query}", "content": f"# {query}\n\n## Introduction\n\nResearch on: {query}\n\n## Conclusion\n\nFurther investigation is recommended.", "model": model, "tokens": 0, "cost": 0, "num_results": 1, "verbose": options.get("verbose", True)}
    except Exception as e:
        rprint(f"[yellow]Warning: {e}. Creating basic synthesis.[/yellow]")
        return {"query": f"Research Synthesis: {query}", "content": f"# {query}\n\n## Introduction\n\nResearch on: {query}\n\n## Conclusion\n\nFurther investigation is recommended.", "model": model, "tokens": 0, "cost": 0, "num_results": 1, "verbose": options.get("verbose", True)}
def apply_synthesis(results: Dict[str, str], synthesis: Dict[str, str]) -> Dict[str, str]:
    final = results.copy(); final["introduction"] = synthesis.get("introduction", ""); final["conclusion"] = synthesis.get("conclusion", "")
    for edit in synthesis.get("suggested_edits", []):
        sec, orig, repl = edit.get("section", ""), edit.get("original", ""), edit.get("replacement", "")
        if sec in final and orig in final[sec]:
            final[sec] = final[sec].replace(orig, repl)
    return final
def _create_synthesis_prompt(query: str, results: Dict[str, str]) -> str:
    condensed = {title: (content[:500] + "..." + content[-500:] if len(content)>1000 else content) for title, content in results.items()}
    res_text = "".join(f"## {t}\n\n{c}\n\n" for t, c in condensed.items())
    return f"""I've conducted deep research on: "{query}" Below are the results for different aspects of this topic:\n\n{res_text}\nBased on these, please:\n1. Generate an introduction (250-500 words) framing the topic and key themes.\n2. Create a conclusion (250-500 words) that synthesizes findings and offers insights.\n3. Suggest up to 5 specific edits to improve flow between sections (specify section, original text, and replacement text).\n\nFormat your response as a JSON object with keys "introduction", "conclusion", and "suggested_edits". Only include the JSON object in your response."""