#!/usr/bin/env bash
set -e

# Configuration
ASKD_HOME="${HOME}/.askd"
ASKD_ENV="${ASKD_HOME}/env"

# Ensure environment is active
source "${ASKD_ENV}/bin/activate"

# Execute command
if [ "$1" = "--version" ]; then
    echo "askd version 2.0.0"
else
    # Try to run askd.cli, but fall back to perplexity_cli if not available
    if python -c "import askd.cli" &>/dev/null; then
        python -m askd.cli "$@"
    else
        python -m perplexity_cli.cli "$@"
    fi
fi
