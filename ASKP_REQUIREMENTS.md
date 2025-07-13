# ASKP Project Requirements & Invariants

This document specifies the key requirements, invariants, and design goals for the ASKP project. All code and test changes should be consistent with these requirements.

---

## 1. CLI and Command Behavior
- ASKP must provide a command-line interface (`askp`) for querying Perplexity AI.
- CLI must support single and multi-query modes, file input, and stdin input.
- CLI must provide clear help, usage, and error messages.
- Command-line flags must be documented and function as described.
- The `-o`/`--output` flag must set the output file or directory.

## 2. Output Directory and File Handling
- By default, all results must be saved in `./perplexity_results` in the current working directory.
- If the `-o`/`--output` flag is set, results must be saved to the specified path.
- No fallback to the home directory or temp directories is allowed for output.
- Output files must use `.md` extension for markdown.
- The output directory must be created if it does not exist.

## 3. API Key and Security
- The Perplexity API key must be loaded from environment variables or `.env` files, never hardcoded.
- API keys must never be exposed in logs or output.
- The CLI must exit with a clear error if the API key is missing.

## 4. Query Processing and Results
- ASKP must support both single and batch (multi) queries.
- Results must be formatted as markdown, JSON, or plain text according to user flags.
- Output must include model, token, and cost information when verbose mode is enabled.
- Multi-query output must combine results clearly and provide a summary section.

## 5. Error Handling and User Feedback
- All errors must be reported clearly to the user, with actionable messages.
- The CLI must exit with a non-zero code on error.
- Invalid or missing arguments must result in usage/help output.

## 6. Extensibility and Modularity
- Code must be modular: major logic in separate modules (executor, utils, api, etc.).
- Adding new output formats or query types should not require major refactoring.

## 7. Testing and Quality Assurance
- All core functions and CLI commands must have unit tests.
- Tests must not rely on deprecated or removed functions.
- Test mocks must match the current module/function structure.
- All tests must pass before merging or deploying.

## 8. Documentation and Usability
- All CLI options and environment variables must be documented in the README.
- The requirements in this file must be kept up-to-date with project changes.

---

_Last updated: 2025-05-08_

If you add or change a requirement, update this file accordingly to keep the project aligned with its goals.
