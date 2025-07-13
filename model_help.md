# ASKP Model Help

## ⚠️ IMPORTANT COST WARNING ⚠️

**🚨 EXPENSIVE MODELS - USE WITH EXTREME CAUTION 🚨**

The following models are **10-20X MORE EXPENSIVE** than standard models:
- `sonar-reasoning-pro` (-r flag)
- `sonar-pro` 
- Any model with "pro" in the name

**DO NOT USE THESE MODELS UNLESS SPECIFICALLY REQUESTED OR FOR CRITICAL COMPLEX REASONING TASKS**

For most queries, use:
- `sonar-reasoning` (default) - Good balance of quality and cost
- `sonar` (-b flag) - Cheapest for simple factual queries

## Available Models

| Model | Description | Web Search | Cost | Best For | Flag |
|-------|-------------|:---------:|:----:|----------|------|
| `sonar` | Basic model | ✓ | $ | Fast, simple queries | `-b` |
| `sonar-reasoning` | Reasoning model (DEFAULT) | ✓ | $$ | General use | (default) |
| `sonar-reasoning-pro` | Enhanced reasoning | ✓ | $$$ | Complex problems | `-r` |
| `sonar-deep-research` | Research-focused | ✓ | $$$ | Academic research | `--research` |
| `llama-3.1-sonar-small-128k-online` | Code-optimized | ✓ | $$ | Programming tasks | `-c` |
| `sonar-pro` | Premium model | ✓ | $$$$ | Highest quality (EXPENSIVE) | `-m sonar-pro-most-expensive` |

## Cost Comparison

| Model | Input Cost ($/1M tokens) | Output Cost ($/1M tokens) | Search Cost (per 1000 requests) |
|-------|--------------------------|----------------------------|--------------------------------|
| sonar | $1 | $1 | $5 |
| sonar-reasoning | $1 | $5 | $5 |
| sonar-reasoning-pro | $2 | $8 | $5 |
| sonar-deep-research | $2 | $8 + $3 (reasoning) | $5 |
| sonar-pro | $3 | $15 | $5 |

**IMPORTANT**: Sonar-Pro is the MOST expensive model at $15 per million output tokens.

## Search Depth Options

Control how extensively Perplexity searches for information:

| Depth | Flag | Description | Cost Impact |
|-------|------|-------------|-------------|
| Low | `-d low` | Minimal search, basic facts | Lowest cost |
| Medium | `-d medium` | Standard search (default) | Moderate cost |
| High | `-d high` | Deep, extensive search | Highest cost |

## Recommended Usage

```bash
# General purpose (DEFAULT model - good balance)
askp "History of quantum computing"

# Basic queries (CHEAPEST)
askp -b "Population of Japan"

# Enhanced reasoning (better but more expensive)
askp -r "Analyze this mathematical proof step by step"

# Code generation
askp -c "Write a Python function to parse JSON"

# Academic research
askp --research "Compare quantum computing approaches"

# Search depth control
askp -d high "Find recent studies on climate change"
askp -d low "Capital of France"

# Premium quality (MOST EXPENSIVE - use with caution!)
askp -m sonar-pro-most-expensive "Find cutting-edge research in AI ethics"
```

## Flag Reference

| Flag | Description | Example |
|------|-------------|---------|
| `-b` | Use basic sonar model (cheapest) | `askp -b "Population of Tokyo"` |
| `-r` | Use enhanced reasoning model | `askp -r "Explain quantum theory"` |
| `-c` | Use coding-optimized model | `askp -c "Write a Python sort algorithm"` |
| `--research` | Use deep research model | `askp --research "Compare research papers"` |
| `-d low/medium/high` | Set search depth | `askp -d high "Latest AI research"` |
| `-m sonar-pro-most-expensive` | Use premium model (expensive!) | `askp -m sonar-pro-most-expensive "..."` |

## Cost-Saving Tips

1. Use the default `sonar-reasoning` for most queries
2. Use `-b` for simple factual queries
3. Use `-d low` to minimize search costs
4. Be mindful of query length - longer queries cost more
5. Consider limiting output tokens with `--max-tokens`
6. NEVER use sonar-pro unless absolutely necessary
