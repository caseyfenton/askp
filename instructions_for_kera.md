# Installing the Fixed askp Version on Windows with Windsurf

Hi Kera! I've created a fixed version of askp that works on Windows and resolves the module import issues. 

## Option 1: Direct Installation with Windsurf (Recommended)

1. Open Windsurf
2. Run this command to install the fixed branch:
   ```
   pip install git+https://github.com/caseyfenton/askp.git@kera-windows-fix
   ```

3. Verify installation with:
   ```
   python -m askp.cli --version
   ```
   This should output: `askp, version 2.4.1`

## Option 2: Using Python pip Directly

If you prefer using pip directly:

```
pip install git+https://github.com/caseyfenton/askp.git@kera-windows-fix
```

## Testing Your Installation

Run a simple test query:
```
python -m askp.cli --model sonar "What is the capital of Germany?" --verbose
```

## Important Notes About Output Files

This version saves results to a `perplexity_results` folder in your current working directory:

- **Location**: Files are saved to `./perplexity_results/` in your current directory, not in your home folder
- **File Naming**: Two files are created for each query:
  1. `query_1_TIMESTAMP_Your_query_text.md` - Contains just that query's result
  2. `Your_query_text_TIMESTAMP.markdown` - Another format of the same result

- **Finding Your Files**: The version doesn't consistently display where files are saved, so if you don't see a message, check in the `perplexity_results` folder in your current directory

- **Adding an Output File Explicitly**: Use the `-o` flag to specify a file:
  ```
  python -m askp.cli -m sonar "Your query" -o specific_output_file.md
  ```

## Troubleshooting

- If you get import errors, ensure you're using the correct Python environment where askp was installed
- For API connection issues, check your API key and internet connection
- For any permission errors, try running your command prompt as administrator
- If you can't find output files, check both `./perplexity_results/` and `./src/perplexity_results/` 

## API Key Setup

You need a valid Perplexity API key set in one of these ways:
1. As an environment variable: `PERPLEXITY_API_KEY=your_key`
2. In a `.env` file in your current working directory
```
