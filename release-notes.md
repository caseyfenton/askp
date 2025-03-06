# ASKP 2.3.0 Release Notes

## Overview

ASKP 2.3.0 introduces significant usability and performance enhancements to make your research experience more efficient and informative. This update makes multi-query mode the default behavior, adds performance metrics, and improves output file location visibility.

## New Features

### Multi-Query Mode as Default

Multi-query mode is now the default behavior, allowing you to process multiple queries in parallel without explicitly using the `-m` flag:

```bash
# These queries will automatically run in parallel
askp "Machine learning fundamentals" "Python best practices" "Data visualization techniques"
```

If you prefer to process all arguments as a single query, use the new `-s/--single` flag:

```bash
# Process all arguments as a single query
askp -s "Machine learning fundamentals" "with Python" "and data visualization"
```

### Performance Metrics

Multi-query searches now include a "queries per second" performance metric, helping you understand and optimize your research efficiency:

```bash
Processing 5 queries in parallel...
Model: sonar-pro | Temperature: 0.7

Processing complete!
Results saved in directory: ~/askp_results/2025-03-06_15-30-45
Queries processed: 5/5
Total tokens used: 42,500
Total cost: $0.0425
Performance: 0.83 queries/second
```

### Enhanced Output File Location Visibility

The output file location is now clearly displayed for both single and multi-query searches, making it easier to find and reference your results:

```
Results directory: ~/askp_results/2025-03-06_15-30-45
```

In markdown output, the results directory is also included in the summary section for multi-query searches.

## Changes

- The `-m/--multi` flag has been renamed to `-s/--single` with inverted behavior
- Performance metrics are now displayed for multi-query searches
- Output file locations are more prominently displayed
- Version updated to 2.3.0 across all relevant files

## Previous Features

### Query Expansion

The `-e/--expand` option allows you to automatically generate related queries from your initial query, providing more comprehensive research results:

```bash
# Start with one query and expand to 5 total queries
askp -e 5 "Machine learning fundamentals"
```

### Enhanced Solution-Focused Query Expansion

The `-e/--expand` option generates queries that:
- Focus on providing comprehensive understanding of topics
- Identify specific problem solutions
- Consider recent developments and time-sensitive information
- Drive toward practical, actionable solutions

## Getting Started

Update to the latest version:

```bash
pip install -U askp
```

Run a basic multi-query search:

```bash
askp "Python async programming" "Concurrent execution models" "Event loops explained"
```

For more information, run:

```bash
askp --help
