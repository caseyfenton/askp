# ASKP Module Structure

This document provides an overview of ASKP's modular architecture, explaining the purpose and responsibilities of each module.

## Core Modules

### `__init__.py`
- **Purpose**: Entry point and version information
- **Exports**: Main functions and version for easy importing
- **Usage**: `import askp` will expose the most commonly used functions

### `api.py`
- **Purpose**: Handles all interactions with the Perplexity API
- **Key Functions**: 
  - `search_perplexity()`: Sends queries to Perplexity API and handles responses
- **Features**: Error handling, response validation, debug mode for troubleshooting

### `cli.py`
- **Purpose**: Defines the command-line interface using Click
- **Key Functions**:
  - `cli()`: Main CLI entry point with all command options
  - `main()`: Wrapper function for the CLI
- **Features**: Command options, parameter validation, help text

### `codecheck.py`
- **Purpose**: Handles code quality checking functionality
- **Key Functions**:
  - `handle_code_check()`: Analyzes code files for issues and improvements
- **Features**: Code extraction, prompt generation, result formatting

### `executor.py`
- **Purpose**: Manages query execution and results processing
- **Key Functions**:
  - `execute_query()`: Processes individual queries
  - `handle_multi_query()`: Manages multiple parallel queries
  - `output_result()`: Formats and saves query results
- **Features**: Parallel processing, result saving, combined output generation

### `formatters.py`
- **Purpose**: Formats API responses into different output formats
- **Key Functions**:
  - `format_json()`: JSON output
  - `format_markdown()`: Markdown output
  - `format_text()`: Plain text output
- **Features**: Consistent formatting across output types, error handling

### `file_utils.py`
- **Purpose**: Utilities for file operations
- **Key Functions**:
  - `format_path()`: Formats file paths for display
  - `get_file_stats()`: Gets file size and line count
  - `generate_cat_commands()`: Creates commands for viewing result files
- **Features**: Path normalization, file stats, display helpers

### `utils.py`
- **Purpose**: General utility functions used across modules
- **Key Functions**:
  - `format_size()`: Formats byte sizes for display
  - `sanitize_filename()`: Cleans strings for use as filenames
  - `load_api_key()`: Loads API keys from environment or files
  - `get_model_info()`: Gets information about AI models
- **Features**: File naming, size formatting, API key handling

## Extension Modules

### `bgrun_integration.py`
- **Purpose**: Integration with BGRun for notifications and status updates
- **Key Functions**:
  - `notify_query_completed()`: Notifies BGRun about query completion
  - `update_askp_status_widget()`: Updates BGRun status widgets

### `deep_research.py`
- **Purpose**: Implements deep research mode
- **Key Functions**:
  - `generate_research_plan()`: Creates a comprehensive research plan
  - `process_research_plan()`: Executes a research plan
  - `synthesize_research()`: Combines research results

### `expand.py`
- **Purpose**: Implements query expansion functionality
- **Key Functions**:
  - `generate_expanded_queries()`: Expands a set of queries with related ones

### `prompts.py`
- **Purpose**: Manages prompt templates
- **Key Functions**:
  - `get_prompt_template()`: Gets the appropriate prompt template based on options

## Entry Points

### `__main__.py`
- **Purpose**: Enables running as a module (`python -m askp`)
- **Features**: Import optimization to avoid circular dependencies

### `askp_cli.py`
- **Purpose**: Standalone CLI entry script
- **Features**: Path configuration for proper imports

## Development Guidelines

When modifying or extending ASKP:

1. **Respect Module Boundaries**: Keep functionality in its appropriate module
2. **Maintain API Compatibility**: Preserve function signatures for backward compatibility
3. **Follow Error Handling Patterns**: Use consistent error handling across modules
4. **Update Documentation**: Keep this document updated when adding or changing modules

## Testing

To run tests for individual modules:
```bash
pytest tests/test_api.py
pytest tests/test_formatters.py
# etc.
```

For complete test coverage:
```bash
pytest
```
