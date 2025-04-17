#!/usr/bin/env python3
"""
Deep research module for ASKP CLI.
Provides functions to generate research plans and expand a query into focused research queries.
"""
import json
import os
from typing import List, Dict, Optional, Any, Tuple
from openai import OpenAI
from rich import print as rprint

from .utils import load_api_key


def process_deep_research(results: List[Dict], options: Dict):
    """
    Process deep research results and synthesize a comprehensive report.
    
    Args:
        results: List of query results
        options: Options for processing
        
    Returns:
        List of processed results
    """
    # Get the original query and research plan
    if not results or len(results) == 0:
        return results
    
    # Extract metadata from the results
    original_query = options.get("query", "")
    overview = results[0]["metadata"].get("research_overview", "Deep Research Results")
    
    # Calculate total tokens and cost 
    total_tokens = sum(r.get("tokens", 0) for r in results if r)
    total_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
    
    # Generate introduction and conclusion
    print("\nSynthesizing research results...")
    synthesis = synthesize_research(original_query, results[0]["metadata"], options)
    
    # Add the synthesis to the results
    results[0]["research_synthesis"] = synthesis
    
    # Display final summary
    print("\nDeep Research Complete!")
    print(f"Original Query: {original_query}")
    print(f"Research Queries Processed: {len(results)}")
    print(f"Total Tokens: {total_tokens:,}")
    print(f"Total Cost: ${total_cost:.4f}")
    
    # Show the output file path
    if "metadata" in results[0] and "saved_path" in results[0]["metadata"]:
        print(f"Results saved to: {results[0]['metadata']['saved_path']}")
    
    # Return the processed results
    return results


def generate_research_plan(query: str, model: str = "sonar-pro", temperature: float = 0.7, options: Optional[Dict[str, Any]] = None):
    """
    Generate a research plan for a given query.
    
    Args:
        query: The query to generate a research plan for
        model: The model to use for generating the plan
        temperature: The temperature to use for generation
        options: Additional options for customizing the plan generation
        
    Returns:
        A dictionary containing the research plan with overview and sections
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
                print(f"Generated research plan with {len(valid_research_queries)} research queries.")
                return {"research_overview": overview, "research_sections": valid_research_queries}
            else:
                print("Warning: Could not generate research queries. Using original query.")
                return {"research_overview": query, "research_sections": [query]}
            
        except json.JSONDecodeError:
            print("Warning: Could not parse deep research response as JSON. Using original query.")
            return {"research_overview": query, "research_sections": [query]}
            
    except Exception as e:
        print(f"Warning: Failed to generate deep research plan: {e}. Using original query.")
        return {"research_overview": query, "research_sections": [query]}


def process_research_plan(plan: Dict, options: Dict):
    """
    Process a research plan and execute the queries.
    
    Args:
        plan: The research plan to process
        options: Options for query execution
        
    Returns:
        A list of query results
    """
    if not plan or not isinstance(plan, dict):
        print("Error: Invalid research plan")
        return []
    
    overview = plan.get("research_overview", "")
    sections = plan.get("research_sections", [])
    
    if not sections:
        print("Error: No research sections found in plan")
        return []
    
    # Print research plan overview
    print("\nResearch Plan:")
    print(f"Overview: {overview}")
    print(f"Research Queries:")
    for i, section in enumerate(sections):
        print(f"{i+1}. {section}")
    
    # Process all queries using existing multi-query handler
    from .executor import handle_multi_query
    original_opts = options.copy()
    
    # Set the processing_subqueries flag to true
    # This will ensure the deep research processing happens after all subqueries
    original_opts["processing_subqueries"] = True
    
    # Store the original query and plan for later synthesis
    original_opts["original_query"] = original_opts.get("query", "")
    original_opts["research_overview"] = overview
    original_opts["research_sections"] = sections
    
    # Process all the research queries
    results = handle_multi_query(sections, original_opts)
    
    # Store the overview and original query for synthesis
    if results:
        results[0]["metadata"]["research_overview"] = overview
        results[0]["metadata"]["original_query"] = original_opts.get("original_query", "")
        results[0]["metadata"]["research_sections"] = sections
        
        # Store all research components for reference
        components = []
        for i, r in enumerate(results):
            if r and "query" in r and "content" in r:
                components.append({
                    "query": r["query"],
                    "content": r.get("content", ""),
                    "tokens": r.get("tokens", 0)
                })
        results[0]["metadata"]["research_components"] = components
    
    return results


def synthesize_research(query: str, results: Dict[str, str], options: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Synthesize research results into an introduction and conclusion.
    This uses Perplexity AI to stitch together multiple research components into a cohesive document.
    
    Args:
        query: The original query
        results: Dictionary mapping section titles to content
        options: Options for synthesis
        
    Returns:
        Dictionary with introduction and conclusion
    """
    if not results:
        return {"introduction": "", "conclusion": ""}
    
    try:
        # Load API key
        api_key = load_api_key()
        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        
        # Extract relevant information
        overview = results.get("research_overview", query)
        
        # Create prompt for synthesis
        synthesis_prompt = _create_synthesis_prompt(query, overview, results)
        
        print("Creating introduction and conclusion using Perplexity API...")
        
        # Request synthesis from API
        response = client.chat.completions.create(
            model=options.get("model", "sonar-reasoning-pro"),
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=options.get("temperature", 0.7),
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        
        # Try to extract JSON
        try:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                synthesis = json.loads(json_str)
                intro = synthesis.get("introduction", "")
                conclusion = synthesis.get("conclusion", "")
            else:
                # Try to extract sections based on headers
                intro = ""
                conclusion = ""
                lines = content.split('\n')
                
                current_section = None
                for line in lines:
                    line_lower = line.lower()
                    if "introduction" in line_lower or "intro" in line_lower:
                        current_section = "introduction"
                    elif "conclusion" in line_lower:
                        current_section = "conclusion"
                    elif current_section and line.strip():
                        if current_section == "introduction":
                            intro += line + "\n"
                        elif current_section == "conclusion":
                            conclusion += line + "\n"
            
            return {
                "introduction": intro.strip(),
                "conclusion": conclusion.strip()
            }
            
        except json.JSONDecodeError:
            print("Warning: Could not parse synthesis response as JSON. Generating basic synthesis.")
            return {
                "introduction": f"# Introduction\n\nThis is a deep research report on: {query}\n\n{overview}",
                "conclusion": "# Conclusion\n\nThis concludes our research on this topic."
            }
            
    except Exception as e:
        print(f"Warning: Failed to synthesize research: {e}. Generating basic synthesis.")
        return {
            "introduction": f"# Introduction\n\nThis is a deep research report on: {query}\n\n{overview}",
            "conclusion": "# Conclusion\n\nThis concludes our research on this topic."
        }


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


def _create_synthesis_prompt(query: str, overview: str, results: Dict[str, Any]) -> str:
    """
    Create a prompt for synthesizing research results.
    
    Args:
        query: Original query
        overview: Research overview
        results: Dictionary of results
        
    Returns:
        Prompt string
    """
    prompt = f"""You are synthesizing a deep research report on the following topic:

Original Query: "{query}"
Research Overview: "{overview}"

The report has several sections of research. Your task is to create:

1. An introduction that frames the research, explains its importance, and outlines what the reader will find in the report
2. A conclusion that summarizes the key findings, connects the different research sections, and provides final thoughts

Format your response as a JSON object with two keys, "introduction" and "conclusion", containing markdown-formatted text.
Example:
{{
  "introduction": "# Introduction\\n\\nThis research explores...",
  "conclusion": "# Conclusion\\n\\nIn summary, our research has shown..."
}}
"""
    return prompt
