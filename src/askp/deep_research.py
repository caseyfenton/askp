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

from .cli import load_api_key


def generate_research_plan(
    query: str,
    model: str = "sonar-pro",
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Generate a comprehensive research plan based on the original query.
    
    This function calls the Perplexity API to create a structured research plan
    with an overview and multiple research sections. The plan is designed to
    cover different aspects of the topic for thorough exploration.
    
    Args:
        query: Original research query or topic
        model: Perplexity model to use for generating the research plan
        temperature: Temperature for controlling response creativity (0.0-1.0)
        
    Returns:
        Dictionary containing the research plan with the following structure:
        {
            "research_overview": "Overview of the research topic",
            "research_sections": [
                {"title": "Section 1", "description": "Description of section 1"},
                {"title": "Section 2", "description": "Description of section 2"},
                ...
            ]
        }
        
    Example:
        ```python
        plan = generate_research_plan("Impact of quantum computing on cryptography")
        print(plan["research_overview"])
        for section in plan["research_sections"]:
            print(f"- {section['title']}")
        ```
    """
    try:
        # Load API key
        api_key = load_api_key()
        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        
        # Create the prompt for generating the research plan
        prompt = _create_research_prompt(query)
        
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
                
                # Create standardized output format
                research_plan = {
                    "research_overview": result.get("overview", query),
                    "research_sections": []
                }
                
                # Process research queries into sections
                for i, research_query in enumerate(result.get("research_queries", [])):
                    if isinstance(research_query, str) and research_query.strip():
                        research_plan["research_sections"].append({
                            "title": f"Section {i+1}: {research_query.strip()}",
                            "description": research_query.strip()
                        })
                
                if research_plan["research_sections"]:
                    rprint(f"[green]Generated research plan with {len(research_plan['research_sections'])} sections.[/green]")
                    return research_plan
            
            # Fallback: create a basic plan from the original query
            rprint("[yellow]Warning: Could not parse research plan as JSON. Creating basic plan.[/yellow]")
            return {
                "research_overview": query,
                "research_sections": [{"title": query, "description": query}]
            }
            
        except json.JSONDecodeError:
            rprint("[yellow]Warning: Could not parse research plan response as JSON. Creating basic plan.[/yellow]")
            return {
                "research_overview": query,
                "research_sections": [{"title": query, "description": query}]
            }
            
    except Exception as e:
        rprint(f"[yellow]Warning: Failed to generate research plan: {e}. Creating basic plan.[/yellow]")
        return {
            "research_overview": query,
            "research_sections": [{"title": query, "description": query}]
        }


def create_research_queries(
    query: str,
    model: str = "sonar-pro",
    temperature: float = 0.7
) -> List[str]:
    """
    Create a list of focused research queries based on the original query.
    
    This function generates a research plan and then converts it into a list
    of specific research queries that can be used with the ASKP CLI.
    
    Args:
        query: Original research query or topic
        model: Perplexity model to use for generating the research queries
        temperature: Temperature for controlling response creativity (0.0-1.0)
        
    Returns:
        List of research queries, including the original query as the first item
        
    Example:
        ```python
        queries = create_research_queries("Impact of quantum computing on cryptography")
        for i, q in enumerate(queries):
            print(f"{i+1}. {q}")
        ```
    """
    # Generate the research plan
    research_plan = generate_research_plan(query, model, temperature)
    
    # Extract queries from the research plan
    queries = [query]  # Start with the original query
    
    for section in research_plan["research_sections"]:
        section_query = section["description"]
        if section_query and section_query != query:
            queries.append(section_query)
    
    return queries


def _create_research_prompt(query: str) -> str:
    """
    Create a prompt for generating a comprehensive research plan.
    
    Args:
        query: Original research query or topic
        
    Returns:
        Formatted prompt string for the Perplexity API
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
