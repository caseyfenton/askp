#!/bin/bash

# Load environment variables from ~/.env
if [ -f ~/.env ]; then
  source ~/.env
fi

# Check if PERPLEXITY_API_KEY is set
if [ -z "$PERPLEXITY_API_KEY" ]; then
  echo "Error: PERPLEXITY_API_KEY is not set in your environment."
  echo "Please make sure it's defined in ~/.env or set it manually."
  exit 1
fi

# Navigate to the MCP server directory
cd "$(dirname "$0")/modelcontextprotocol/perplexity-ask"

# Run the MCP server using node
echo "Starting Perplexity Ask MCP server..."
echo "The server is running. Press Ctrl+C to stop."
node dist/index.js
