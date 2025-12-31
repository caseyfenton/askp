#!/usr/bin/env python3
"""Model definitions and capabilities for ASKP."""
from typing import Dict

# Model registry with costs and capabilities
MODEL_REGISTRY: Dict[str, Dict] = {
    "sonar": {
        "id": "sonar",
        "cost_per_million": 1.00,
        "tokens_per_second": 1200,
        "context_window": 127000,
        "max_output_tokens": 4000,
        "description": "Best for real-time search",
        "confidence_score": 0.95,
        "capabilities": ["real-time-search", "code-completion", "documentation"]
    },
    "sonar-pro": {
        "id": "sonar-pro",
        "cost_per_million": 5.00,
        "tokens_per_second": 1200,
        "context_window": 256000,
        "max_output_tokens": 32000,
        "description": "Best for enterprise research",
        "confidence_score": 0.95,
        "capabilities": ["enterprise-research", "large-context", "advanced-analysis"]
    },
    "sonar-reasoning-pro": {
        "id": "sonar-reasoning-pro",
        "cost_per_million": 10.00,
        "tokens_per_second": 800,
        "context_window": 128000,
        "max_output_tokens": 32000,
        "description": "Advanced reasoning with chain-of-thought",
        "confidence_score": 0.97,
        "capabilities": ["advanced-reasoning", "chain-of-thought", "complex-analysis", "json-output"]
    },
    "sonar-deep-research": {
        "id": "sonar-deep-research",
        "cost_per_million": 15.00,
        "tokens_per_second": 600,
        "context_window": 200000,
        "max_output_tokens": 32000,
        "description": "Exhaustive multi-source research",
        "confidence_score": 0.98,
        "capabilities": ["deep-research", "multi-source", "academic-research", "market-analysis"]
    },
    "pplx": {
        "id": "pplx-api",
        "cost_per_million": 1.50,
        "tokens_per_second": 2400,
        "context_window": 128000,
        "max_output_tokens": 4000,
        "description": "Best for high-throughput applications",
        "confidence_score": 0.93,
        "capabilities": ["high-throughput", "fast-processing", "scalable-apps"]
    },
    "gpt4": {
        "id": "gpt4-omni",
        "cost_per_million": 12.00,
        "tokens_per_second": 380,
        "context_window": 32000,
        "max_output_tokens": 4000,
        "description": "Best for complex analysis",
        "confidence_score": 0.95,
        "capabilities": ["complex-analysis", "expert-reasoning", "system-design"]
    },
    "claude": {
        "id": "claude-3.5-sonnet",
        "cost_per_million": 9.00,
        "tokens_per_second": 420,
        "context_window": 32000,
        "max_output_tokens": 4000,
        "description": "Best for technical writing",
        "confidence_score": 0.95,
        "capabilities": ["technical-writing", "documentation", "code-review"]
    }
}

def get_model_info(model_name: str) -> Dict:
    """Get information about a specific model."""
    return MODEL_REGISTRY.get(model_name, MODEL_REGISTRY["sonar"])

def list_models() -> Dict[str, Dict]:
    """Get the full model registry."""
    return MODEL_REGISTRY

def get_model_capabilities(model_name: str) -> list:
    """Get capabilities for a specific model."""
    model = get_model_info(model_name)
    return model.get("capabilities", [])