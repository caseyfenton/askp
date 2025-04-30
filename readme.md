# ASKP - Ask Perplexity

[![PyPI version](https://img.shields.io/pypi/v/askp.svg)](https://pypi.org/project/askp/)
[![Python versions](https://img.shields.io/pypi/pyversions/askp.svg)](https://pypi.org/project/askp/)
[![License](https://img.shields.io/github/license/caseyfenton/askp.svg)](https://github.com/caseyfenton/askp/blob/main/LICENSE)

ASKP (Ask Perplexity) is a powerful command-line interface for natural language search and knowledge discovery using the Perplexity API, with built-in cost tracking and advanced features. Currently integrated with Perplexity API, with plans to support additional LLM providers like Open Router.

## Project Status

**STABLE**: ASKP is now available on PyPI! While core functionality is stable, some features are still being refined and tested. Please report any issues you encounter.

**Cost Tracking Note**: The cost tracking feature provides an estimate based on approximate token counts (calculated as bytes divided by 3) and publicly available pricing information for the models. Actual costs may vary from these estimates. We're continuously working to improve the accuracy of these calculations.

## Features

- Natural language queries through Perplexity API
- Multi-query processing with parallel execution
- Two deep research modes:
  - Built-in deep research mode using Perplexity's specialized model (faster, more cost-effective)
  - Custom deep research implementation with multi-query approach (more transparent, specialized depth)
- Cost tracking and analytics
- Project-aware context
- Beautiful CLI interface
- Extensible architecture for multiple LLM providers

## Why ASKP?

ASKP is designed specifically for developers using modern AI-powered coding tools like Windsurf, Cursor, or Ader. Instead of performing multiple sequential web searches that consume valuable time, ASKP can:

- Run multiple parallel searches simultaneously, dramatically reducing wait times
- Bring comprehensive research directly into your codebase
- Generate in-depth research with two different deep research approaches (built-in or custom)
- Integrate seamlessly with local LLM tools - once results are in your project folder, they become instantly searchable in your codebase vector store
- Solve complex problems quickly with minimal cost (e.g., 670 searches for approximately $0.77)
- Support not just coding tasks but also research for legal, academic, or other professional projects

## Future Enhancements

- MCP Server integration
- Support for Open Router and additional LLM providers
- Enhanced context handling
- Improved cost optimization
- Advanced model selection

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
# Install from PyPI
pip install askp

# Or install with development dependencies
pip install askp[dev]
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/caseyfenton/askp.git
cd askp

# Install
./install.sh
```

You can also use pip to install directly from GitHub:

```bash
pip install git+https://github.com/caseyfenton/askp.git
```

## Usage

```bash
# Basic query
askp "What is the capital of France?"

# With project context
cd your-project
askp "How do I implement a binary search tree in Python?"

# Multi-query mode (process queries in parallel)
askp "What is Python?" "What is TypeScript?" "What is Rust?"

# Process multiple queries from a file
askp -i queries.txt 

# Generate comprehensive research using Perplexity's built-in deep research model
askp -D "Impact of quantum computing on cryptography"

# Generate comprehensive research using custom multi-query implementation
askp --deep-custom "Impact of quantum computing on cryptography"

# Combine query results into a single output (default behavior)
askp "Query 1" "Query 2" "Query 3"

# Keep query results separate
askp --no-combine "Query 1" "Query 2" "Query 3"

# Expand your research with auto-generated related queries
askp -e 10 "Python best practices"

# Control the maximum number of parallel processes
askp --max-parallel 20 "Query 1" "Query 2" "Query 3" "Query 4" "Query 5"

# Set maximum tokens in response
askp --token-max 4096 "Explain quantum computing"

# View costs
askp costs

# Quick mode (combine queries into a single request)
askp -Q "What is pizza?" "Where was pizza invented?" "Popular toppings?"

# Output as JSON
askp -f json "Query"

# Get help
askp --help
```

## Options

```
Options:
  --version                       Show the version and exit.
  -v, --verbose                   Enable verbose output
  -q, --quiet                     Suppress all output except results
  -f, --format [markdown|md|json|text|txt]
                                  Output format
  -o, --output PATH               Save output to file
  -n, --num-results INTEGER       Number of results per query
  -m, --model TEXT                Model to use
  -b, --basic                     Use basic Sonar model (fastest, cheapest)
  -r, --reasoning-pro             Use enhanced reasoning model (sonar-reasoning-pro)
  -c, --code                      Use code-optimized model
  -S, --sonar                     Use Sonar model (same as -b)
  -SP, --sonar-pro                Use Sonar Pro model (EXPENSIVE)
  -d, --search-depth [low|medium|high]
                                  Search depth
  -t, --temperature FLOAT         Temperature
  --token-max INTEGER             Max tokens
  --model-help                    Show detailed model information and costs
  --pro-reasoning                 Use Pro Reasoning model (same as -r)
  --reasoning                     Use Reasoning model
  -s, --single                    Don't combine multiple queries
  --max-parallel INTEGER          Max parallel queries
  --file, -i PATH                 Read queries from file
  --no-combine                    Don't combine multiple queries into one file
  -C, --combine                   Combine multiple queries into one file (default behavior)
  --view                          View query results in terminal
  --view-lines INTEGER            View query results with specified max lines
  -e, --expand INTEGER            Expand queries to specified total number
  -D, --deep                      Perform deep research using Perplexity's built-in model
  --deep-custom                   Use custom deep research implementation (multiple parallel queries)
  --cleanup-component-files       Move component files to trash after deep research is complete
  -Q, --quick                     Combine all queries into a single request with short answers
  --code-check, -cc PATH          File to check for code quality/issues
  --help                          Show this message and exit.
```

## Tips

**TIP**: Run multiple searches in a single command to parallelize your research:

```bash
askp "Python packaging best practices" "Common Python security issues" "Cross-platform Python compatibility"
```

**TIP**: Combine results into a single output file for faster reading and analysis:

```bash
askp -o research.md "Query 1" "Query 2" "Query 3"
```

**TIP**: For complex research topics, break down your question into 5-10 specific queries for more comprehensive results.

**TIP**: Use ASKP with Windsurf or other vector-enabled IDEs to make all search results instantly searchable within your codebase.

**TIP**: Track your API usage costs with `askp costs` to monitor your spending.

**TIP**: Use the `-e` feature to automatically generate related queries:

```bash
# Start with one query and expand to 5 total queries
askp -e 5 "Machine learning fundamentals"
```

**TIP**: For complex research topics, use one of the deep research modes:

```bash
# Use Perplexity's built-in deep research model (faster, cheaper)
askp -D "Impact of climate change on agriculture"

# Use custom deep research implementation with parallel queries (more transparent)
askp --deep-custom "Impact of climate change on agriculture"
```

**TIP**: Increase parallel processing capacity for large batches of queries:

```bash
# Process up to 20 queries in parallel
askp --max-parallel 20 -i many_queries.txt
```

**TIP**: Use quick mode for getting concise answers to multiple related questions:

```bash
askp -Q "What is pizza?" "Where was it invented?" "Popular toppings?"
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

## About the Creator

ASKP is brought to you by Casey Fenton, one of the founders of Couchsurfing. With 30 years of experience as both an entrepreneur and programmer, Casey created ASKP to share powerful AI tools with friends and colleagues. ASKP has become one of his most valuable day-to-day tools, saving significant time and multiplying productivity.

> "It's really wonderful and magical when you find a tool that really serves as a timesaver and force multiplier. I hope other people find this to be as helpful as I have experienced it being." - Casey Fenton

## License

MIT