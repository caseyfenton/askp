#!/bin/bash
set -e

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() { echo -e "${2:-$NC}$1${NC}"; }
info() { log "$1" "$GREEN"; }
warn() { log "$1" "$YELLOW"; }
error() { log "$1" "$RED"; }
header() { echo -e "\n${BLUE}=== $1 ===${NC}\n"; }

# Configuration
ASKP_HOME="${HOME}/.askp"
ASKP_ENV="${ASKP_HOME}/env"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VERSION="2.1.0"

header "ASKP CLI Fix Script"
echo "This script will fix the ASKP CLI issues"

# Check for old ASKD environment and symlinks
header "Checking for old ASKD references"
if [ -d "${HOME}/.askd" ]; then
    warn "Old ASKD environment found at ~/.askd"
    info "Checking for any symlinks that might be pointing to the old environment"
    
    # Check if askp or ask symlinks point to the old environment
    for cmd in askp ask; do
        cmd_path=$(which $cmd 2>/dev/null || echo "")
        if [[ -n "$cmd_path" && "$cmd_path" == *".askd"* ]]; then
            warn "Found $cmd pointing to old ASKD environment: $cmd_path"
            rm -f "$cmd_path"
            info "Removed old symlink: $cmd_path"
        fi
    done
fi

# Create/update virtual environment
header "Setting up virtual environment"
if [ ! -d "${ASKP_ENV}" ]; then
    info "Creating new virtual environment"
    python3 -m venv "${ASKP_ENV}"
fi

source "${ASKP_ENV}/bin/activate"
pip install --quiet --upgrade pip wheel

# Install the package
header "Installing ASKP package"
cd "${SCRIPT_DIR}"
pip install --quiet --upgrade -e .
info "Installed ASKP package"

# Create direct executable scripts
header "Creating direct executable scripts"
mkdir -p ~/.local/bin

cat > ~/.local/bin/askp << 'SCRIPT'
#!/bin/bash
# Direct ASKP CLI wrapper script
# Version: 2.1.0

if [ "$1" = "--version" ] || [ "$1" = "-v" ]; then
    echo "askp version 2.1.0"
    exit 0
fi

# Activate the virtual environment and run the command
source "${HOME}/.askp/env/bin/activate"
python -m askp.cli "$@"
SCRIPT

cat > ~/.local/bin/ask << 'SCRIPT'
#!/bin/bash
# Direct ASK CLI wrapper script
# Version: 2.1.0

if [ "$1" = "--version" ] || [ "$1" = "-v" ]; then
    echo "ask version 2.1.0"
    exit 0
fi

# Activate the virtual environment and run the command
source "${HOME}/.askp/env/bin/activate"
python -m askp.cli "$@"
SCRIPT

chmod +x ~/.local/bin/askp ~/.local/bin/ask
info "Created direct executable scripts"

# Verify installation
header "Verifying installation"
echo "ASKP executable: $(which askp)"
echo "ASK executable: $(which ask)"
echo "Testing version reporting:"
~/.local/bin/askp --version
~/.local/bin/ask --version

header "Testing help command"
~/.local/bin/askp --help | head -5

header "Installation complete!"
echo "Please restart your terminal or run:"
echo "  source ~/.bashrc  # If using bash"
echo "  source ~/.zshrc   # If using zsh"
echo
echo "Then try running 'askp' or 'ask' again"
