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
ASKP_LOGS="${ASKP_HOME}/logs"
ASKP_COST_LOGS="${ASKP_HOME}/cost_logs"
BACKUP_DIR="${ASKP_HOME}/backup/$(date +%Y%m%d%H%M%S)"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VERSION="2.1.0"

header "ASKP Complete Fix Utility"
echo "This script will fix all ASKP installation issues"

# Create backup
mkdir -p "${BACKUP_DIR}"
info "Created backup directory: ${BACKUP_DIR}"

# Backup shell config files
for config in ~/.bashrc ~/.bash_profile ~/.zshrc ~/.profile; do
    if [ -f "$config" ]; then
        cp "$config" "${BACKUP_DIR}/$(basename $config)"
        info "Backed up $config"
    fi
done

# Clean up shell config files
header "Cleaning shell configurations"
for config in ~/.bashrc ~/.bash_profile ~/.zshrc ~/.profile; do
    if [ -f "$config" ]; then
        # Remove old aliases
        sed -i.bak '/alias ask=.*/d' "$config"
        sed -i.bak '/alias askp=.*/d' "$config"
        sed -i.bak '/alias askd=.*/d' "$config"
        
        # Remove duplicate PATH entries
        sed -i.bak '/# ASKD PATH/d' "$config"
        sed -i.bak '/# ASKP PATH/d' "$config"
        sed -i.bak '/# ASKP PATH Priority/d' "$config"
        sed -i.bak '/Added by ASKP complete fix script/d' "$config"
        sed -i.bak '/export PATH=".*\.local\/bin.*"/d' "$config"
        
        # Add correct PATH entry
        echo -e "\n# Added by ASKP complete fix script" >> "$config"
        echo 'export PATH="$HOME/.local/bin:$HOME/bin:$PATH"' >> "$config"
        
        info "Cleaned up $config"
        rm -f "$config.bak"
    fi
done

# Remove old symlinks and scripts
header "Removing old scripts and symlinks"
rm -f ~/.local/bin/askp ~/.local/bin/ask ~/bin/askp ~/bin/ask 2>/dev/null || true
info "Removed old symlinks"

# Ensure directories exist
mkdir -p "${ASKP_HOME}" "${ASKP_LOGS}" "${ASKP_COST_LOGS}" ~/.local/bin ~/bin
info "Created required directories"

# Create/update virtual environment
header "Setting up virtual environment"
if [ -d "${ASKP_ENV}" ]; then
    info "Removing old virtual environment"
    rm -rf "${ASKP_ENV}"
fi

info "Creating new virtual environment"
python3 -m venv "${ASKP_ENV}"
source "${ASKP_ENV}/bin/activate"
pip install --quiet --upgrade pip wheel

# Install the package
header "Installing ASKP package"
cd "${SCRIPT_DIR}"
pip install --quiet --upgrade -e .
info "Installed ASKP package"

# Create new symlinks
header "Creating symlinks"
ln -sf "${ASKP_ENV}/bin/askp" ~/.local/bin/askp
ln -sf "${ASKP_ENV}/bin/ask" ~/.local/bin/ask
info "Created symlinks in ~/.local/bin"

# Create wrapper scripts for better version reporting
header "Creating wrapper scripts"
cat > ~/.local/bin/askp-wrapper << 'WRAPPER'
#!/bin/bash
if [ "$1" = "--version" ] || [ "$1" = "-v" ] && [ "$2" = "--version" ]; then
    echo "askp version 2.1.0"
    exit 0
fi
~/.askp/env/bin/askp "$@"
WRAPPER

cat > ~/.local/bin/ask-wrapper << 'WRAPPER'
#!/bin/bash
if [ "$1" = "--version" ] || [ "$1" = "-v" ] && [ "$2" = "--version" ]; then
    echo "ask version 2.1.0"
    exit 0
fi
~/.askp/env/bin/ask "$@"
WRAPPER

chmod +x ~/.local/bin/askp-wrapper ~/.local/bin/ask-wrapper
mv ~/.local/bin/askp-wrapper ~/.local/bin/askp
mv ~/.local/bin/ask-wrapper ~/.local/bin/ask
info "Created wrapper scripts with proper version reporting"

# Check for old ASKD environment
header "Checking for old ASKD environment"
if [ -d ~/.askd ]; then
    warn "Old ASKD environment found at ~/.askd"
    read -p "Do you want to remove it? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Backing up old ASKD environment to ${BACKUP_DIR}/askd"
        cp -r ~/.askd "${BACKUP_DIR}/askd"
        rm -rf ~/.askd
        info "Removed old ASKD environment"
    else
        warn "Old ASKD environment kept. This might cause conflicts."
    fi
fi

# Verify installation
header "Verifying installation"
echo "ASKP executable: $(which askp)"
echo "ASK executable: $(which ask)"
echo "ASKP version: $(askp --version)"
echo "ASK version: $(ask --version)"

header "Installation complete!"
echo "Please restart your terminal or run:"
echo "  source ~/.bashrc  # If using bash"
echo "  source ~/.zshrc   # If using zsh"
echo
echo "Then try running 'askp' or 'ask' again"
