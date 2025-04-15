#!/bin/bash
# ASKP Results Widget - Shows recent Perplexity query results

RESULTS_DIR="$HOME/perplexity_results"
MAX_RESULTS=5  # Show up to 5 most recent results
MAX_AGE_MINS=10  # Show results from the last 10 minutes

# Make sure the directory exists
if [[ ! -d "$RESULTS_DIR" ]]; then
  echo "### ASKP Results"
  echo "No results directory found at $RESULTS_DIR"
  exit 0
fi

# Find recent result files (MD, JSON, TXT)
find_recent_files() {
  find "$RESULTS_DIR" -type f \( -name "*.md" -o -name "*.json" -o -name "*.txt" \) -mmin -$MAX_AGE_MINS | sort -r
}

# Generate content for widget
RECENT_FILES=$(find_recent_files | head -n $MAX_RESULTS)

if [[ -z "$RECENT_FILES" ]]; then
  CONTENT="### ASKP Results\nNo recent results found in the last $MAX_AGE_MINS minutes."
else
  CONTENT="### ASKP Results (Last $MAX_AGE_MINS mins)"
  
  # Process each file
  while IFS= read -r file; do
    filename=$(basename "$file")
    # Get file stats - modified time and size
    mod_time=$(stat -f "%Sm" -t "%H:%M:%S" "$file")
    file_size=$(stat -f "%z" "$file" | numfmt --to=iec)
    
    # Create clickable file:// URL
    file_url="file://$file"
    
    # Extract query text if it's a markdown file
    if [[ "$file" == *.md ]]; then
      # Try to extract query using simple pattern matching
      query=$(grep -m 1 -A 1 "^##\s*Query" "$file" | tail -n 1 | sed 's/^[#\s]*//')
      if [[ -z "$query" ]]; then
        # Alternative: just take the first non-empty, non-header line
        query=$(grep -v "^#" "$file" | grep -v "^$" | head -n 1 | cut -c 1-50)
        
        # If still empty, use filename as fallback
        if [[ -z "$query" ]]; then
          query="$filename"
        fi
      fi
      
      # Truncate long queries
      if [[ ${#query} -gt 40 ]]; then
        query="${query:0:40}..."
      fi
    else
      # For non-markdown files, just use the filename
      query="$filename"
    fi
    
    # Add the result to the content
    CONTENT="$CONTENT\n- **$query** [$mod_time, $file_size] [$file_url]"
  done <<< "$RECENT_FILES"
  
  # Add footer with update info
  CONTENT="$CONTENT\n\n*Updated every 5 minutes*"
fi

# Output the content
echo -e "$CONTENT"

# Register with bgrun widget system if requested
if [[ "$1" == "--register" ]]; then
  # Find bgrun
  if command -v bgrun &> /dev/null; then
    BGRUN_PATH=$(command -v bgrun)
  elif [[ -x "$HOME/bin/bgrun" ]]; then
    BGRUN_PATH="$HOME/bin/bgrun"
  elif [[ -x "/Users/casey/CascadeProjects/bgrun/bgrun" ]]; then
    BGRUN_PATH="/Users/casey/CascadeProjects/bgrun/bgrun"
  else
    echo "Error: bgrun not found"
    exit 1
  fi
  
  # Register the widget with a 5 minute update interval
  "$BGRUN_PATH" --widget "askp-results" --interval 5m "$0"
fi
