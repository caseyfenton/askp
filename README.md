# ASKP - Ask Perplexity

ASKP (Ask Perplexity) is a powerful command-line interface for natural language search and knowledge discovery using the Perplexity API, with built-in cost tracking and advanced features. Currently integrated with Perplexity API, with plans to support additional LLM providers like Open Router.

## Features

- Natural language queries through Perplexity API
- Multi-query processing with parallel execution
- Deep research mode for comprehensive topic exploration
- Cost tracking and analytics
- Project-aware context
- Beautiful CLI interface
- Extensible architecture for multiple LLM providers

## Why ASKP?

ASKP is designed specifically for developers using modern AI-powered coding tools like Windsurf, Cursor, or Ader. Instead of performing multiple sequential web searches that consume valuable time, ASKP can:

- Run multiple parallel searches simultaneously, dramatically reducing wait times
- Bring comprehensive research directly into your codebase
- Generate in-depth research plans with the deep research mode
- Integrate seamlessly with local LLM tools - once results are in your project folder, they become instantly searchable in your codebase vector store
- Solve complex problems quickly with minimal cost (e.g., 670 searches for approximately $0.77)
- Support not just coding tasks but also research for legal, academic, or other professional projects

## Future Enhancements

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

# Generate a comprehensive research plan with deep research mode
askp -d "Impact of quantum computing on cryptography"

# Combine multiple query results into a single output
askp -m -c "Query 1" "Query 2" "Query 3"

# Expand your research with auto-generated related queries
askp -e 10 "Python best practices"

# Control the maximum number of parallel processes
askp -m -p 20 "Query 1" "Query 2" "Query 3" "Query 4" "Query 5"

# Set maximum tokens in response
askp -t 4096 "Explain quantum computing"

# View costs
askp costs

# Get help
askp --help
```

## Options

```
Options:
  --version                       Show the version and exit.
  -v, --verbose                   Enable verbose output
  -q, --quiet                     Suppress all output except results
  -f, --format [text|json|markdown]
                                  Output format
  -o, --output PATH               Save output to file
  -n, --num-results INTEGER       Number of results to return from Perplexity
  --model TEXT                    Model to use (default: sonar-pro)
  --temperature FLOAT             Response creativity (default: 0.7)
  -t, --token-max INTEGER         Maximum tokens in response (default: 8192)
  -r, --reasoning                 Use reasoning model ($5.00 per million tokens)
  --pro-reasoning                 Use pro reasoning model ($8.00 per million tokens)
  -m, --multi                     Process each argument as a separate query in parallel
  -p, --max-parallel INTEGER      Maximum number of parallel processes (default: 10)
  -i, --file PATH                 File containing queries (one per line)
  -c, --combine                   Combine all results into a single output
  -e, --expand INTEGER            Expand queries to specified total number by generating related queries
  -d, --deep                      Generate a comprehensive research plan with detailed queries
  --help                          Show this message and exit.
```

## Tips

**TIP**: Run multiple searches in a single command to parallelize your research:
```bash
askp -m "Python packaging best practices" "Common Python security issues" "Cross-platform Python compatibility"
```

**TIP**: Combine results into a single output file for faster reading and analysis:
```bash
askp -m -c -o research.md "Query 1" "Query 2" "Query 3"
```

**TIP**: For complex research topics, break down your question into 5-10 specific queries for more comprehensive results.

**TIP**: Use ASKP with Windsurf or other vector-enabled IDEs to make all search results instantly searchable within your codebase.

**TIP**: Track your API usage costs with `askp costs` to monitor your spending.

**TIP**: Use the new `-e` feature to automatically generate related queries:
```bash
# Start with one query and expand to 5 total queries
askp -e 5 "Machine learning fundamentals"
```

**TIP**: For complex research topics, use the deep research mode to generate a comprehensive research plan:
```bash
# Generate a detailed research plan with focused sub-queries
askp -d "Impact of climate change on agriculture"
```

**TIP**: Increase parallel processing capacity for large batches of queries:
```bash
# Process up to 20 queries in parallel
askp -m -p 20 -i many_queries.txt
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
