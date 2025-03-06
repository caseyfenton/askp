#!/bin/bash

# Create a temporary file for the prompt
output_file="askd_deep_reasoning_prompt.txt"

# Start with a fresh file and add the prompt instructions
cat > "$output_file" << 'PROMPT'
# ASKD Codebase Analysis Request

You are tasked with performing a deep analysis of the ASKD (Advanced Search Knowledge Discovery) codebase. Below you'll find:

1. A tree view of the entire codebase with file sizes
2. The full content of all important files in the project

## Your Tasks:

1. Analyze the overall architecture and structure of the codebase
2. Identify any potential issues, bugs, or areas for improvement
3. Suggest optimizations or refactorings that could enhance the code quality
4. Evaluate the test coverage and suggest additional tests if needed
5. Provide insights on the project's scalability and maintainability
6. Provide EXACT code fixes for any issues you identify

Please be thorough in your analysis and provide specific, actionable recommendations with exact code implementations. When suggesting changes, provide the complete code that should replace the existing code, not just descriptions of what should be changed.

## Codebase Structure:

PROMPT

# Add the tree command output with file sizes
echo "Running tree command to get file structure..."
echo -e "\n\`\`\`" >> "$output_file"
find . -type f -not -path "*/\.*" -not -path "*/askd.egg-info/*" -exec ls -la {} \; | sort -k5 -n >> "$output_file"
echo -e "\`\`\`\n" >> "$output_file"

# Function to add a file with a clear delimiter
add_file() {
  echo -e "\n## File: $1\n\n\`\`\`" >> "$output_file"
  if [[ "$1" == *.py ]]; then
    echo "python" >> "$output_file"
  elif [[ "$1" == *.sh ]]; then
    echo "bash" >> "$output_file"
  fi
  cat "$1" >> "$output_file"
  echo -e "\n\`\`\`" >> "$output_file"
}

# Add files in a logical order
echo -e "\n# Source Code Files\n" >> "$output_file"

add_file "src/askd/__init__.py"
add_file "src/askd/models.py"
add_file "src/askd/cli.py"
add_file "src/askd/cost_tracking.py"
add_file "setup.py"
add_file "scripts/system_wrapper"
add_file "src/backfill_cost_data.py"

echo -e "\n# Test Files\n" >> "$output_file"
add_file "tests/test_models.py"
add_file "tests/test_cli.py"
add_file "tests/test_cost_tracking.py"

# Add closing instructions
cat >> "$output_file" << 'CLOSING'

# Analysis Request

Based on the codebase provided above, please provide:

1. A high-level overview of the ASKD project architecture
2. Detailed analysis of each component
3. Identification of any bugs, code smells, or anti-patterns
4. Suggestions for improving code quality, performance, and maintainability with EXACT code implementations
5. Recommendations for enhancing test coverage with example test code
6. Any additional insights that would be valuable for improving this codebase

For each issue or improvement you identify, please provide:
- The exact file and line numbers where the issue occurs
- The current problematic code
- The exact replacement code that fixes the issue
- An explanation of why your solution is better

Use code blocks to clearly show the before and after code. Be specific and provide complete implementations, not just snippets or descriptions.
CLOSING

echo "Prompt has been generated in $output_file"
echo "Copying to clipboard..."

# Copy to clipboard based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  cat "$output_file" | pbcopy
  echo "Content copied to clipboard using pbcopy"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # Linux with xclip
  if command -v xclip &> /dev/null; then
    cat "$output_file" | xclip -selection clipboard
    echo "Content copied to clipboard using xclip"
  elif command -v xsel &> /dev/null; then
    cat "$output_file" | xsel --clipboard
    echo "Content copied to clipboard using xsel"
  else
    echo "Warning: xclip or xsel not found. Could not copy to clipboard."
  fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
  # Windows
  cat "$output_file" | clip
  echo "Content copied to clipboard using clip"
else
  echo "Warning: Unknown OS. Could not copy to clipboard."
fi

echo "Done!"
