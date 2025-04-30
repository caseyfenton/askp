#!/usr/bin/env python3
"""
Debug script to examine the full Perplexity API response structure
"""
import os
import json
from openai import OpenAI

def load_api_key():
    """Load the Perplexity API key from environment or .env files."""
    key = os.environ.get("PERPLEXITY_API_KEY")
    if key:
        return key
    for p in [os.path.join(os.path.expanduser("~"), ".env"), 
              os.path.join(os.path.expanduser("~"), ".perplexity", ".env"),
              os.path.join(os.path.expanduser("~"), ".askp", ".env")]:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    for line in f:
                        if line.startswith("PERPLEXITY_API_KEY="):
                            return line.split("=", 1)[1].strip().strip('"\'' )
            except Exception as e:
                print(f"Warning: Error reading {p}: {e}")
    print("Error: Could not find Perplexity API key.")
    return None

def examine_response():
    """Examine the full structure of a Perplexity API response."""
    api_key = load_api_key()
    if not api_key:
        return
        
    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    query = "What are the top 3 best practices for software development?"
    messages = [{"role": "user", "content": query}]
    
    try:
        # Get the response
        resp = client.chat.completions.create(
            model="sonar-pro", 
            messages=messages, 
            temperature=0.7, 
            max_tokens=1000, 
            stream=False
        )
        
        # Convert to dictionary to examine structure
        resp_dict = resp.model_dump()
        
        # Save full response to a file for examination
        with open("perplexity_full_response.json", "w") as f:
            json.dump(resp_dict, f, indent=2)
        
        print(f"Full response saved to perplexity_full_response.json")
        
        # Print basic info
        print("\nBasic Response Info:")
        print(f"ID: {resp.id}")
        print(f"Model: {resp.model}")
        print(f"Content: {resp.choices[0].message.content[:100]}...")
        
        # Check for citation related properties
        print("\nChecking for Citation Data:")
        found_citations = False
        
        # Examine message structure for citation data
        message = resp.choices[0].message
        message_dict = message.model_dump()
        print(f"Message properties: {list(message_dict.keys())}")
        
        # Check top-level response properties
        print(f"Response properties: {list(resp_dict.keys())}")
        
        # Check for tool_calls which might contain citation data
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"Found tool_calls: {message.tool_calls}")
            found_citations = True
            
        # Special handling for 'function_call' property if it exists
        if hasattr(message, 'function_call') and message.function_call:
            print(f"Found function_call: {message.function_call}")
            found_citations = True
        
        # Check for any unused properties
        print("\nUnused Properties:")
        for key, value in resp_dict.items():
            if key not in ['id', 'model', 'choices', 'created', 'object', 'system_fingerprint', 'usage']:
                print(f"  - {key}: {value}")
                found_citations = True
                
        if not found_citations:
            print("No obvious citation data found in the response structure.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    examine_response()
