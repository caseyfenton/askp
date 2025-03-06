# ASKP - Ask Perplexity

ASKP (Ask Perplexity) is a powerful command-line interface for natural language search and knowledge discovery using the Perplexity API, with built-in cost tracking and advanced features. Currently integrated with Perplexity API, with plans to support additional LLM providers like Open Router.

## Features

- Natural language queries through Perplexity API
- Multi-query processing with parallel execution
- Cost tracking and analytics
- Project-aware context
- Beautiful CLI interface
- Extensible architecture for multiple LLM providers

## Future Enhancements

- Support for Open Router and additional LLM providers
- Enhanced context handling
- Improved cost optimization
- Advanced model selection

## Installation

```bash
# Clone the repository
git clone https://github.com/caseyfenton/askp.git
cd askp

# Install
./install.sh
```

## Usage

```bash
# Basic query
askp "What is the capital of France?"

# With project context
cd your-project
askp "How do I implement a binary search tree in Python?"

# Multi-query mode (process queries in parallel)
askp -m "What is Python?" "What is TypeScript?" "What is Rust?"

# Process multiple queries from a file
askp -i queries.txt -m

# Combine multiple query results into a single output
askp -m -c "Query 1" "Query 2" "Query 3"

# View costs
askp costs

# Get help
askp --help
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
flake8
```

## License

MIT
