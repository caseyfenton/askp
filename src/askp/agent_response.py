#!/usr/bin/env python3
"""
Agent-centric response handling for ASKP with Perplexity.
Implements structured JSON responses optimized for autonomous agents.
"""
import json
import os
from typing import Dict, List, Any, Optional, Literal
from pathlib import Path
from datetime import datetime

# Agent-centric JSON schema for Perplexity structured outputs
# This schema is designed for machine consumption, not human readability
AGENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "decision_context": {
            "type": "object",
            "properties": {
                "outcome": {
                    "type": "string",
                    "enum": ["definitive", "ambiguous", "insufficient_data"]
                },
                "confidence": {"type": "number"},
                "complexity": {
                    "type": "string",
                    "enum": ["low", "medium", "high"]
                }
            },
            "required": ["outcome", "confidence", "complexity"]
        },
        "entity_graph": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                    "data_type": {
                        "type": "string",
                        "enum": ["string", "int", "bool", "code"]
                    }
                },
                "required": ["key", "value", "data_type"]
            }
        },
        "content_modules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "token_estimate": {"type": "integer"},
                    "raw_content": {"type": "string"}
                },
                "required": ["id", "tags", "raw_content"]
            }
        }
    },
    "required": ["decision_context", "entity_graph", "content_modules"],
    "additionalProperties": False
}

# System prompt for agent-only output mode
AGENT_SYSTEM_PROMPT = """You are a headless JSON data engine for autonomous agents. You output only raw JSON that strictly conforms to the provided schema. You never talk to humans, never use markdown, and you encode all knowledge into the schema fields instead of asking clarifying questions.

Output structure:
- decision_context: Small state header with outcome, confidence, and complexity
- entity_graph: Key-value facts as structured data
- content_modules: Heavy text blocks with tags and token estimates for selective loading

Focus on machine-readable, structured data. No prose, no markdown, no human-oriented explanations."""


class AgentResponseCache:
    """Cache for storing and retrieving agent responses with lazy module loading."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the cache with optional custom directory."""
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.askp/agent_cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, query_id: str) -> Path:
        """Get the cache file path for a given query ID."""
        return self.cache_dir / f"{query_id}.json"

    def store(self, query_id: str, response: Dict[str, Any]) -> None:
        """Store a full agent response in the cache."""
        cache_path = self._get_cache_path(query_id)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2)

    def load(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Load a full agent response from the cache."""
        cache_path = self._get_cache_path(query_id)
        if not cache_path.exists():
            return None
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_index(self, query_id: str) -> Optional[Dict[str, Any]]:
        """
        Get lightweight index for a cached response.
        Returns decision_context, entity_graph, and module index (without raw_content).
        """
        response = self.load(query_id)
        if not response:
            return None

        # Extract the structured response if it's nested
        structured = response.get('structured_content', response)

        # Build lightweight index
        index = {
            "decision_context": structured.get("decision_context", {}),
            "entity_graph": structured.get("entity_graph", []),
            "module_index": []
        }

        # Create module index without raw_content
        for module in structured.get("content_modules", []):
            index["module_index"].append({
                "id": module.get("id"),
                "tags": module.get("tags", []),
                "token_estimate": module.get("token_estimate", 0)
            })

        return index

    def get_module(self, query_id: str, module_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific content module by ID.
        Returns the full module including raw_content.
        """
        response = self.load(query_id)
        if not response:
            return None

        # Extract the structured response if it's nested
        structured = response.get('structured_content', response)

        # Find the module
        for module in structured.get("content_modules", []):
            if module.get("id") == module_id:
                return module

        return None


def parse_agent_response(raw_content: str) -> Dict[str, Any]:
    """
    Parse agent response content, handling potential markdown fences.

    Args:
        raw_content: Raw response string from Perplexity API

    Returns:
        Parsed JSON structure
    """
    # Strip potential markdown code fences
    content = raw_content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse agent response as JSON: {e}\nContent: {content[:200]}...")


def validate_agent_response(response: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate that a response conforms to the agent schema.

    Args:
        response: Parsed JSON response

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required top-level fields
    required_fields = ["decision_context", "entity_graph", "content_modules"]
    for field in required_fields:
        if field not in response:
            return False, f"Missing required field: {field}"

    # Validate decision_context
    dc = response["decision_context"]
    if not isinstance(dc, dict):
        return False, "decision_context must be an object"

    dc_required = ["outcome", "confidence", "complexity"]
    for field in dc_required:
        if field not in dc:
            return False, f"decision_context missing required field: {field}"

    if dc["outcome"] not in ["definitive", "ambiguous", "insufficient_data"]:
        return False, f"Invalid outcome value: {dc['outcome']}"

    if dc["complexity"] not in ["low", "medium", "high"]:
        return False, f"Invalid complexity value: {dc['complexity']}"

    # Validate entity_graph
    if not isinstance(response["entity_graph"], list):
        return False, "entity_graph must be an array"

    # Validate content_modules
    if not isinstance(response["content_modules"], list):
        return False, "content_modules must be an array"

    for i, module in enumerate(response["content_modules"]):
        if "id" not in module:
            return False, f"Module {i} missing required field: id"
        if "raw_content" not in module:
            return False, f"Module {i} missing required field: raw_content"

    return True, None


def format_agent_index(index: Dict[str, Any]) -> str:
    """
    Format agent index for display.

    Args:
        index: Index structure from get_index()

    Returns:
        Formatted string representation
    """
    output = []

    # Decision context
    dc = index.get("decision_context", {})
    output.append("## Decision Context")
    output.append(f"- Outcome: {dc.get('outcome', 'unknown')}")
    output.append(f"- Confidence: {dc.get('confidence', 0):.2f}")
    output.append(f"- Complexity: {dc.get('complexity', 'unknown')}")
    output.append("")

    # Entity graph
    eg = index.get("entity_graph", [])
    if eg:
        output.append("## Entity Graph")
        for entity in eg:
            output.append(f"- {entity.get('key')}: {entity.get('value')} ({entity.get('data_type')})")
        output.append("")

    # Module index
    modules = index.get("module_index", [])
    if modules:
        output.append("## Content Modules")
        for module in modules:
            tags = ", ".join(module.get("tags", []))
            output.append(f"- Module {module.get('id')}: [{tags}] (~{module.get('token_estimate', 0)} tokens)")
        output.append("")

    return "\n".join(output)


def get_response_format_config() -> Dict[str, Any]:
    """
    Get the response_format configuration for Perplexity API.

    Returns:
        Dictionary with type and json_schema fields
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "schema": AGENT_JSON_SCHEMA
        }
    }
