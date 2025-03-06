# ASKP Changelog

## 2.3.0 (2025-03-06)

### Added
- Made multi-query mode the default behavior (use `-s/--single` for single query mode)
- Added queries per second performance metric for multi-query searches
- Enhanced output file location visibility for all search results

### Changed
- Renamed `-m/--multi` flag to `-s/--single` (inverted behavior)
- Updated version to 2.3.0 across all relevant files

## 2.2.1 (2025-02-20)

### Changed
- Enhanced query expansion to focus on solution-oriented and time-sensitive results
- Updated version to 2.2.1 across all relevant files

## 2.2.0 (2025-02-15)

### Added
- Query expansion feature with `-e/--expand` option to generate related queries
- Random tips feature that provides helpful usage suggestions
- Max parallel processes option with `-p/--max-parallel` to control concurrency
- Improved documentation with examples for new features
- PyPI deployment script for easier package publishing

### Changed
- Updated version to 2.2.0 across all relevant files
- Renamed `--max-tokens` to `--token-max` with `-t` shorthand
- Enhanced CLI interface with better error handling and more intuitive options
- Improved output formatting for better readability
- Updated keywords to reflect new capabilities

### Fixed
- Various small bugs and improvements
- More robust JSON parsing for query expansion

## 2.1.0 (2025-01-25)

### Added
- Multi-query support with parallel processing
- File-based query input
- Combined results output option
- Cost tracking and reporting

### Changed
- Improved API key handling with multiple lookup paths
- Enhanced error messages and user feedback
- Updated documentation with more examples

## 2.0.0 (2025-01-10)

### Added
- Initial public release with Perplexity API support
- Basic CLI interface
- Multiple output formats (text, JSON, markdown)
- Model selection options

### Changed
- Complete rewrite from previous version
- New architecture for better extensibility

## 1.0.0 (2025-01-01)

### Added
- Initial internal release
