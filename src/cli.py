#!/usr/bin/env bash
set -e

# Configuration
ASKP_HOME="${HOME}/.askp"
ASKP_ENV="${ASKP_HOME}/env"

# Ensure environment is active
source "${ASKP_HOME}/env/bin/activate"

# Execute command
if [ "$1" = "--version" ]; then
    echo "askp version 2.4.2"
    exit 0
else
    # Try to run askp.cli, but fall back to perplexity_cli if not available
    if python -c "import askp.cli" &>/dev/null; then
        python -m askp.cli "$@"
    else
        python -m perplexity_cli.cli "$@"
    fi
fi
