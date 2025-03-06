#!/usr/bin/env python3
"""
Deep research module for ASKP CLI.

This module provides functionality for generating comprehensive research plans
and expanding a single query into multiple focused research queries. It uses
the Perplexity API to generate structured research plans that can be used
to create in-depth research documents.

Example:
    ```python
    from askp.deep_research import generate_research_plan, create_research_queries
    
    # Generate a research plan
    plan = generate_research_plan("Impact of quantum computing on cryptography")
    
    # Create specific research queries from the plan
    queries = create_research_queries("Impact of quantum computing on cryptography")
    ```
"""

import json
from typing import List, Dict, Any, Tuple, Optional
from openai import OpenAI
from rich import print as rprint
import re

from .cli import load_api_key


def generate_research_plan(query, model="sonar-pro", temperature=0.7):
    """Generate a research plan for deep research."""
    print("Deep research mode enabled. Generating research plan...")
    
    # Create a prompt for generating a research plan
    prompt = f"""
    Create a comprehensive research plan to answer the following question:
    "{query}"
    
    Please provide:
    1. A list of 8-12 specific research areas to explore
    2. For each area, formulate a clear, focused search query that will yield relevant information
    
    Format your response as a JSON object with the following structure:
    {{
        "research_areas": [
            {{
                "title": "Area title",
                "query": "Specific search query for this area"
            }}
        ]
    }}
    
    Make each query specific, detailed, and designed to retrieve precise information.
    """
    
    # Get the research plan
    from .cli import search_perplexity
    options = {"model": model, "temperature": temperature}
    plan_result = search_perplexity(prompt, options)
    
    try:
        # Extract the JSON content from the response
        content = plan_result.get("content", "")
        if not content and "results" in plan_result and plan_result["results"]:
            content = plan_result["results"][0].get("content", "")
        
        # Find JSON in the content
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without markdown code blocks
            json_match = re.search(r'({.*})', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
        
        # Parse the JSON
        plan_data = json.loads(json_str)
        
        # Extract research areas and queries
        research_areas = plan_data.get("research_areas", [])
        
        # Generate the queries
        queries = []
        for i, area in enumerate(research_areas):
            query_text = area.get("query", "")
            if query_text:
                # Format the filename with a number prefix for ordering
                queries.append(query_text)
        
        print(f"Generated research plan with {len(research_areas)} sections.")
        print(f"Generated {len(queries)} research queries.\n")
        
        return queries, query
        
    except Exception as e:
        print(f"Error generating research plan: {str(e)}")
        # Fallback to a simpler approach
        return [query], query


def create_research_queries(query, model="sonar-pro", temperature=0.7):
    """Create research queries for deep research."""
    # Generate the research plan
    queries, _ = generate_research_plan(query, model, temperature)
    
    # Ensure we have at least the original query
    if not queries:
        queries = [query]
    
    return queries


def synthesize_research(
    query: str,
    results: List[Dict[str, Any]],
    options: Dict[str, Any] = None
) -> Dict[str, str]:
    """
    Synthesize research results into a cohesive document with introduction,
    conclusion, and suggested edits for better flow.
    
    This function takes the original query and a list of research results,
    then generates an introduction, conclusion, and suggested edits to improve
    the overall document.
    
    Args:
        query: Original research query or topic
        results: List of research result dictionaries
        options: Dictionary of options including model and temperature
        
    Returns:
        Dictionary containing the synthesis with the following structure:
        {
            "introduction": "Introduction text...",
            "conclusion": "Conclusion text...",
            "suggested_edits": [
                {"section": "Section title", "original": "Text to replace", "replacement": "New text"}
            ]
        }
    """
    # Set default options if not provided
    if options is None:
        options = {}
    
    model = options.get("model", "sonar-pro")
    temperature = options.get("temperature", 0.7)
    
    try:
        # Load API key
        api_key = load_api_key()
        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        
        # Convert list of results to dictionary format for synthesis
        results_dict = {}
        for i, result in enumerate(results):
            # Extract the query and content
            if isinstance(result, dict):
                query_text = result.get("query", f"Research Area {i+1}")
                content = result.get("content", "")
                
                # Handle nested results structure
                if not content and "results" in result and result["results"]:
                    if isinstance(result["results"], list) and result["results"]:
                        content = result["results"][0].get("content", "")
                    elif isinstance(result["results"], dict):
                        content = result["results"].get("content", "")
                
                results_dict[query_text] = content
        
        # Create the prompt for synthesis
        prompt = _create_synthesis_prompt(query, results_dict)
        
        # Make API call
        rprint("[green]Generating research synthesis...[/green]")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=2048
        )
        
        # Parse the response
        content = response.choices[0].message.content
        try:
            # Try to extract JSON from the response text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
                
                # Create standardized output format
                synthesis = {
                    "introduction": result.get("introduction", ""),
                    "conclusion": result.get("conclusion", ""),
                    "suggested_edits": result.get("suggested_edits", [])
                }
                
                rprint("[green]Successfully generated research synthesis.[/green]")
                
                # Create a result in the same format as other results
                return {
                    "query": f"Research Synthesis: {query}",
                    "content": f"# {query}\n\n## Introduction\n\n{synthesis['introduction']}\n\n## Conclusion\n\n{synthesis['conclusion']}",
                    "model": model,
                    "tokens": response.usage.completion_tokens,
                    "cost": response.usage.completion_tokens * 0.000001,  # Approximate cost
                    "num_results": 1,
                    "verbose": options.get("verbose", True)
                }
            
            # Fallback: create a basic synthesis
            rprint("[yellow]Warning: Could not parse synthesis as JSON. Creating basic synthesis.[/yellow]")
            return {
                "query": f"Research Synthesis: {query}",
                "content": f"# {query}\n\n## Introduction\n\nResearch on: {query}\n\n## Conclusion\n\nBased on the research conducted, further investigation is recommended.",
                "model": model,
                "tokens": 0,
                "cost": 0,
                "num_results": 1,
                "verbose": options.get("verbose", True)
            }
            
        except json.JSONDecodeError:
            rprint("[yellow]Warning: Could not parse synthesis response as JSON. Creating basic synthesis.[/yellow]")
            return {
                "query": f"Research Synthesis: {query}",
                "content": f"# {query}\n\n## Introduction\n\nResearch on: {query}\n\n## Conclusion\n\nBased on the research conducted, further investigation is recommended.",
                "model": model,
                "tokens": 0,
                "cost": 0,
                "num_results": 1,
                "verbose": options.get("verbose", True)
            }
            
    except Exception as e:
        rprint(f"[yellow]Warning: Failed to generate research synthesis: {e}. Creating basic synthesis.[/yellow]")
        return {
            "query": f"Research Synthesis: {query}",
            "content": f"# {query}\n\n## Introduction\n\nResearch on: {query}\n\n## Conclusion\n\nBased on the research conducted, further investigation is recommended.",
            "model": model,
            "tokens": 0,
            "cost": 0,
            "num_results": 1,
            "verbose": options.get("verbose", True)
        }


def apply_synthesis(
    results: Dict[str, str],
    synthesis: Dict[str, str]
) -> Dict[str, str]:
    """
    Apply the synthesis to the research results to create a final document.
    
    This function takes the original research results and the synthesis,
    then applies the introduction, conclusion, and suggested edits to
    create a cohesive final document.
    
    Args:
        results: Dictionary mapping section titles to their content
        synthesis: Synthesis dictionary from synthesize_research
        
    Returns:
        Dictionary with the updated content including introduction and conclusion
        
    Example:
        ```python
        # Apply synthesis to results
        final_document = apply_synthesis(results, synthesis)
        
        # Write to file
        with open("research.md", "w") as f:
            f.write(final_document["introduction"])
            for section, content in final_document.items():
                if section not in ["introduction", "conclusion"]:
                    f.write(f"## {section}\n\n{content}\n\n")
            f.write(final_document["conclusion"])
        ```
    """
    # Create a copy of the results to avoid modifying the original
    final_document = results.copy()
    
    # Add introduction and conclusion
    final_document["introduction"] = synthesis.get("introduction", "")
    final_document["conclusion"] = synthesis.get("conclusion", "")
    
    # Apply suggested edits
    for edit in synthesis.get("suggested_edits", []):
        section = edit.get("section", "")
        original = edit.get("original", "")
        replacement = edit.get("replacement", "")
        
        if section in final_document and original in final_document[section]:
            final_document[section] = final_document[section].replace(original, replacement)
    
    return final_document


def _create_synthesis_prompt(query: str, results: Dict[str, str]) -> str:
    """
    Create a prompt for synthesizing research results.
    
    Args:
        query: Original research query or topic
        results: Dictionary mapping section titles to their content
        
    Returns:
        Formatted prompt string for the Perplexity API
    """
    # Create a condensed version of the results to fit within token limits
    condensed_results = {}
    for title, content in results.items():
        # Limit each section to ~1000 characters
        if len(content) > 1000:
            condensed_results[title] = content[:500] + "..." + content[-500:]
        else:
            condensed_results[title] = content
    
    # Format the results as a string
    results_text = ""
    for title, content in condensed_results.items():
        results_text += f"## {title}\n\n{content}\n\n"
    
    prompt = f"""I've conducted deep research on the topic: "{query}"

Below are the research results for different aspects of this topic:

{results_text}

Based on these research results, please:

1. Generate a compelling introduction (250-500 words) that frames the entire research topic, introduces key themes, and sets up the exploration that follows.

2. Create a thoughtful conclusion (250-500 words) that synthesizes the key findings, highlights important connections between different sections, and offers final insights or future directions.

3. Suggest up to 5 specific edits to improve flow between sections. For each edit, specify the section title, the original text to replace, and the replacement text.

Format your response as a JSON object with the following structure:
{{
  "introduction": "Introduction text...",
  "conclusion": "Conclusion text...",
  "suggested_edits": [
    {{
      "section": "Section title",
      "original": "Text to replace",
      "replacement": "New text"
    }},
    ...
  ]
}}

Only include the JSON object in your response, with no additional text or explanation."""
    return prompt
