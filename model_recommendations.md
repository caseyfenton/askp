# ASKP Model Recommendations

## Recommended Default Models

Based on comprehensive analysis of Perplexity AI's models (April 2025), here are the optimal choices for different use cases:

| Use Case | Recommended Model | Flag | Description | Cost Factor |
|----------|------------------|------|-------------|------------|
| **General Purpose** | `sonar-reasoning` | (default) | Good reasoning with web search | $$ |
| **Advanced Reasoning** | `sonar-reasoning-pro` | `-r` | Enhanced reasoning with better results | $$$ |
| **Coding with Web Search** | `llama-3.1-sonar-small-128k-online` | `-c` | Code generation with web search | $$ |
| **Detailed Research** | `sonar-deep-research` | `--research` | Thorough research with citations | $$$ |
| **Basic Queries** | `sonar` | `-b` | Cheapest, quickest responses | $ |
| **Premium Quality** | `sonar-pro` | `-m sonar-pro-most-expensive` | Highest quality (MOST EXPENSIVE) | $$$$ |

## Command Examples

```bash
# General purpose (recommended default)
askp "History of quantum computing"

# Advanced reasoning (better quality)
askp -r "Explain the mathematical proof of the Riemann hypothesis"

# Basic, simple queries (most cost-effective)
askp -b "Population of Tokyo"

# Coding with web search
askp -c "Write a Python function for binary search"

# Detailed research
askp --research "Compare different approaches to quantum error correction"

# Search depth control (low/medium/high)
askp -d high "Find recent studies on climate change"
askp --search-depth low "Capital of France"

# Premium quality (requires explicit acknowledgment of cost)
askp -m sonar-pro-most-expensive "Find cutting-edge research in AI ethics"
```

## Search Depth Options

The `-d` or `--search-depth` flag controls how many sources Perplexity will search:

| Depth | Flag | Description | Cost Impact |
|-------|------|-------------|-------------|
| Low | `-d low` | Minimal search, basic facts | Lowest cost |
| Medium | `-d medium` | Standard search (default) | Moderate cost |
| High | `-d high` | Deep, extensive search | Highest cost |

Example:
```bash
# Deep search with many sources
askp -d high "Latest research on quantum computing"

# Quick, cost-effective search
askp -d low -b "Population of Tokyo"
```

## Model Features Matrix

| Feature | sonar (-b) | sonar-reasoning (default) | sonar-reasoning-pro (-r) | sonar-pro (most-expensive) | sonar-deep-research |
|---------|:-----:|:-------------------:|:---------------------:|:----------------------:|:-------------------:|
| Web Search | ✓ | ✓✓ | ✓✓ | ✓✓✓ | ✓✓✓ |
| Coding | ✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ |
| Reasoning | ✓ | ✓✓✓ | ✓✓✓✓ | ✓✓ | ✓✓✓ |
| Speed | ✓✓✓ | ✓✓ | ✓✓ | ✓ | ✓ |
| Citations | ✓ | ✓✓ | ✓✓ | ✓✓✓ | ✓✓✓✓ |
| Creativity | ✓ | ✓✓ | ✓✓ | ✓✓ | ✓ |

## Price Comparison (April 2025)

| Model | Input Tokens ($/1M) | Output Tokens ($/1M) | Relative Cost |
|-------|---------------------|----------------------|---------------|
| sonar | $1 | $1 | $ |
| sonar-reasoning | $1 | $5 | $$ |
| sonar-reasoning-pro | $2 | $8 | $$$ |
| sonar-deep-research | $2 | $8 + $3 (reasoning) | $$$ |
| sonar-pro | $3 | $15 | $$$$ | 
| llama-3.1-sonar-small-128k-online | ~$2 | ~$8 | $$ |
| llama-3.1-sonar-large-128k-online | ~$4 | ~$12 | $$$ |

*Note: All models incur an additional $5 per 1,000 search requests. Search depth (high/medium/low) also affects cost.*

## Implementation Suggestions for ASKP

1. **Default to `sonar-reasoning`** - This provides good reasoning and search capabilities at a reasonable cost.

2. **Use simplified flags**:
   - `-b` for basic sonar model (most cost-effective)
   - `-r` for enhanced reasoning with sonar-reasoning-pro
   - `-c` for coding-optimized model
   - `-d [low/medium/high]` for search depth
   - Require explicit `-m sonar-pro-most-expensive` for the expensive model

3. **Update CLI help**:
   - Add a `--model-help` command to display cost information
   - Include warnings about expensive models in main help
   - Show search depth options
   - Provide cost estimates for typical usage

4. **Cost-saving tips**:
   - Use the default `sonar-reasoning` for most queries
   - Use `-b` flag for simple factual queries
   - Use `-d low` to minimize search costs
   - Be aware that high search depth increases costs
   - Never use `sonar-pro-most-expensive` unless absolutely necessary
