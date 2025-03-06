#!/usr/bin/env python3
"""Deep research module for ASKP CLI."""

import json
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from rich import print as rprint

from .cli import load_api_key


def generate_deep_research_plan(
    query: str,
    model: str = "sonar-pro",
    temperature: float = 0.7
) -> Tuple[str, List[str]]:
    """
    Generate a deep research plan based on the original query.
    
    Args:
        query: Original research query
        model: Model to use for generating the research plan
        temperature: Temperature for plan generation
        
    Returns:
        Tuple containing (research_overview, list_of_research_queries)
    """
    try:
        # Load API key
        api_key = load_api_key()
        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        
        # Create the prompt for generating the research plan
        prompt = _create_deep_research_prompt(query)
        
        # Make API call
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=1024
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
                overview = result.get("overview", "")
                research_queries = result.get("research_queries", [])
            else:
                # Fallback: try to parse lines that look like queries
                lines = content.split('\n')
                overview = query  # Default overview is the original query
                research_queries = []
                
                # Look for a line that might be the overview
                for i, line in enumerate(lines):
                    if "overview" in line.lower() or "research plan" in line.lower():
                        if i+1 < len(lines) and lines[i+1].strip():
                            overview = lines[i+1].strip()
                            break
                
                # Extract queries
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith('"') or line.startswith('-') or line.startswith('*')):
                        # Clean up the line
                        research_query = line.lstrip('-*"\' ').rstrip('",\' ')
                        if research_query and len(research_query) > 10:  # Minimum length to filter out noise
                            research_queries.append(research_query)
            
            # Validate and clean up research queries
            valid_research_queries = []
            for research_query in research_queries:
                if isinstance(research_query, str) and research_query.strip():
                    valid_research_queries.append(research_query.strip())
            
            if valid_research_queries:
                rprint(f"[green]Generated research plan with {len(valid_research_queries)} research queries.[/green]")
                return overview, valid_research_queries
            else:
                rprint("[yellow]Warning: Could not generate research queries. Using original query.[/yellow]")
                return query, [query]
            
        except json.JSONDecodeError:
            rprint("[yellow]Warning: Could not parse deep research response as JSON. Using original query.[/yellow]")
            return query, [query]
            
    except Exception as e:
        rprint(f"[yellow]Warning: Failed to generate deep research plan: {e}. Using original query.[/yellow]")
        return query, [query]


def _create_deep_research_prompt(query: str) -> str:
    """
    Create a prompt for generating a deep research plan.
    
    Args:
        query: Original research query
        
    Returns:
        Prompt string
    """
    prompt = f"""The user would like to perform deep research on the following topic:

"{query}"

Please create a comprehensive research plan that breaks down this topic into specific research queries that, when sewn together, will form a complete deep research paper.

Your task is to:
1. Define the overarching research project with a clear overview
2. Break down the research into 5-10 specific, focused queries that cover different aspects of the topic
3. Organize these queries in a logical order that builds knowledge progressively

The research plan should:
1. Be comprehensive and cover the topic thoroughly
2. Include specific, actionable research queries
3. Ensure each query explores a distinct aspect of the topic
4. Build toward a complete understanding when all queries are answered
5. Consider recent developments and time-sensitive information
6. Focus on practical, actionable insights when applicable

Return your response as a JSON object with the following structure:
{{
  "overview": "A concise description of the overall research project",
  "research_queries": [
    "First specific research query",
    "Second specific research query",
    ...
  ]
}}
"""
    return prompt
