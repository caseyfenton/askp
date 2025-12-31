# ASKP - Advanced Search Knowledge Processing

A powerful command-line tool for intelligent search and knowledge discovery powered by Perplexity AI.

[![PyPI version](https://badge.fury.io/py/askp.svg)](https://pypi.org/project/askp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **🔍 Natural Language Search**: Ask questions in plain English and get comprehensive answers
- **🚀 Multiple Models**: Choose from fast basic search to advanced reasoning models
- **📊 Agent Mode**: Structured JSON output optimized for AI agents and automation
- **🔐 PII Protection**: Built-in validation to prevent accidental leakage of sensitive data
- **⚡ Parallel Queries**: Process multiple questions simultaneously for faster results
- **🧠 Deep Research**: Comprehensive multi-query research with source aggregation
- **💾 Smart Caching**: SEMA integration for intelligent result caching
- **📝 Multiple Formats**: Output in Markdown, JSON, or plain text

## Installation

### From PyPI (Recommended)

```bash
pip install askp
```

### From GitHub (Latest Development Version)

```bash
pip install git+https://github.com/caseyfenton/askp.git
```

### From Source

```bash
git clone https://github.com/caseyfenton/askp.git
cd askp
pip install -e .
```

## Quick Start

### Basic Usage

```bash
# Simple search
askp "What is quantum computing?"

# Multiple questions
askp "Python packaging" "Virtual environments" "Poetry vs pip"

# Deep research mode
askp -D "History and impact of renewable energy"

# Use reasoning model for complex analysis
askp -r "Explain the implications of quantum entanglement"
```

### Agent Mode (Default)

```bash
# Get structured JSON output optimized for AI agents
askp "Latest AI developments"

# View just the index (lightweight)
askp --agent-index --query-id <UUID>

# Get specific content module
askp --agent-module 3 --query-id <UUID>
```

### PII Protection (New in v2.5.0)

```bash
# View PII configuration
askp --pii-config

# Queries with PII are automatically blocked
askp "My email is john@example.com"  # BLOCKED

# Bypass PII check when needed (use cautiously)
askp --no-pii-check "query with sensitive data"
```

See [PII_PROTECTION.md](PII_PROTECTION.md) for comprehensive PII protection documentation.

## Available Models

| Model | Flag | Cost | Best For |
|-------|------|------|----------|
| Sonar | `-b`, `--basic` | $ | Quick factual queries |
| Sonar Pro | `-SP` | $$$ | Critical research (20x cost) |
| Sonar Reasoning Pro | `-r` | $$ | Complex analysis, logic chains |
| Code Optimized | `-X` | $ | Programming questions |

```bash
# View detailed model information
askp --model-help
```

## Advanced Features

### Multi-Query Modes

```bash
# Combined mode (default): single API call for multiple questions
askp "Question 1" "Question 2" "Question 3"

# Comprehensive mode: process each separately
askp -c "Question 1" "Question 2" "Question 3"

# Expand: generate additional related queries
askp -e 5 "Main topic"  # Expands to 5 total queries
```

### Output Formats

```bash
# Markdown (default)
askp "query" -f markdown

# JSON for programmatic processing
askp "query" -f json

# Plain text
askp "query" -f text
```

### Deep Research

```bash
# Perplexity's built-in deep research (faster)
askp -D "topic"

# Custom deep research (more transparent)
askp --deep-custom "topic"
```

### Comparison Modes

```bash
# Compare agent vs human output formats
askp --compare "query"

# Compare regular vs reasoning models
askp --compare-reasoning "complex question"
```

## Configuration

### API Key Setup

```bash
# Set Perplexity API key
export PERPLEXITY_API_KEY="your-api-key-here"

# Or create ~/.askp/.env
echo "PERPLEXITY_API_KEY=your-key" > ~/.askp/.env
```

Get your API key from [Perplexity AI](https://www.perplexity.ai/).

### PII Protection Configuration

Edit `~/.askp/pii_config.json` to customize:

- Modes: `block` (default), `warn`, or `silent`
- Custom patterns for domain-specific PII
- Whitelist exceptions
- Severity levels

See [PII_PROTECTION.md](PII_PROTECTION.md) for details.

## Command Reference

### Essential Options

```bash
-v, --verbose          Enable verbose output
-q, --quiet           Suppress all output except results
-f, --format          Output format: markdown, json, text
-o, --output          Custom output file path
-n, --num-results     Number of results per query
-m, --model          Model to use (default: sonar)
```

### Model Selection

```bash
-b, --basic          Use basic Sonar (fastest, cheapest)
-r, --reasoning-pro  Use reasoning model (better analysis)
-X, --code           Use code-optimized model
-SP, --sonar-pro     Use Sonar Pro (most expensive)
```

### Research Modes

```bash
-D, --deep           Deep research mode (built-in)
--deep-custom        Custom deep research
-c, --comprehensive  Process queries separately
-e, --expand N       Expand to N total queries
```

### Advanced Options

```bash
--agent-mode         Structured JSON output (default)
--human-mode         Verbose prose output
--no-cache          Bypass SEMA cache
--debug             Save raw API responses
--pii-config        Show PII configuration
--no-pii-check      Disable PII validation (use cautiously)
```

### Information Commands

```bash
--model-help        Show detailed model information
--account-status    Check API credits
--pii-config        Show PII protection status
-h, --help          Show help message
```

## Use Cases

### Research & Analysis

```bash
# Academic research
askp -D "Recent developments in CRISPR gene editing"

# Market research
askp "AI startup trends 2025" "Funding patterns" "Key players"

# Technical deep dive
askp -r "How does transformer architecture work?"
```

### Development

```bash
# Code examples
askp -X "Python async/await best practices"

# Debugging
askp -X "Why does my React useEffect run twice?"

# Architecture decisions
askp -r "Microservices vs monolith for 10-person team"
```

### AI Agent Integration

```bash
# Get structured data for agent processing
askp --agent-mode "Latest tech news"

# Retrieve specific modules programmatically
askp --agent-module 2 --query-id abc-123-def
```

## Output Structure

### Markdown (Default)

```markdown
# Query: Your Question

## Answer
[Comprehensive answer...]

## Sources
- [Source 1](url)
- [Source 2](url)

## Metadata
- Model: sonar
- Tokens: 1234
- Cost: $0.001
```

### JSON (Agent Mode)

```json
{
  "decision_context": {
    "outcome": "definitive",
    "confidence": 0.95
  },
  "entity_graph": [...],
  "content_modules": [...]
}
```

## Examples

### Basic Research

```bash
# Simple factual query
$ askp "What is the capital of France?"
Saved: perplexity_results/query_1_..._capital_france.md

# Multiple related queries
$ askp "Python history" "Python 3 vs 2" "Python use cases"
Saved: perplexity_results/combined_..._3queries.md
```

### PII Protection in Action

```bash
$ askp "My email is john@example.com"

🚨 PII DETECTED IN QUERY

• Email address (1 match)
  → jo************om

Query blocked. Remove sensitive data to proceed.
To configure: edit ~/.askp/pii_config.json
```

### Comparison Analysis

```bash
$ askp --compare-reasoning "Should we use TypeScript or JavaScript?"

# Generates two files:
# 1. Regular model output (Q&A style)
# 2. Reasoning model output (logic chain)
```

## Troubleshooting

### API Key Issues

```bash
# Check if key is set
echo $PERPLEXITY_API_KEY

# Verify account status
askp --account-status
```

### Cache Problems

```bash
# Bypass cache
askp --no-cache "query"

# Clear SEMA cache manually
rm -rf ~/.askp/agent_cache/
```

### PII False Positives

```bash
# Disable for single query
askp --no-pii-check "query"

# Or edit config to add whitelist
nano ~/.askp/pii_config.json
```

## Development

### Running Tests

```bash
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

### PII Protection

ASKP includes built-in protection against accidentally sending sensitive data:

- Automatic detection of emails, phone numbers, SSNs, credit cards
- Detection of API keys, passwords, private keys, JWT tokens
- Configurable validation modes (block/warn/silent)
- Custom pattern support for organization-specific PII

See [PII_PROTECTION.md](PII_PROTECTION.md) for comprehensive security documentation.

### Reporting Security Issues

Please report security vulnerabilities to the maintainers privately before public disclosure.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **PyPI**: https://pypi.org/project/askp/
- **GitHub**: https://github.com/caseyfenton/askp
- **Documentation**: [PII_PROTECTION.md](PII_PROTECTION.md)
- **Perplexity AI**: https://www.perplexity.ai/

## Credits

Built with:
- [Perplexity AI](https://www.perplexity.ai/) - Powerful AI search engine
- [Click](https://click.palletsprojects.com/) - Command line interface creation
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal formatting

## Changelog

### v2.5.0 (2025-12-30)
- **Security**: Added comprehensive PII protection system
- **Feature**: Automatic detection and blocking of sensitive data
- **Feature**: `--pii-config` flag to manage PII settings
- **Feature**: `--no-pii-check` flag to bypass validation when needed
- **Feature**: Support for custom PII patterns and whitelisting
- **Docs**: Added comprehensive PII_PROTECTION.md documentation

### v2.4.5
- Added sonar-reasoning-pro model support
- Improved agent mode with token compression
- Cost protection for expensive models
- Bug fixes and stability improvements

See [changelog.md](changelog.md) for full version history.
