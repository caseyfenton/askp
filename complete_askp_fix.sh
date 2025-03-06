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
BACKUP_DIR="${ASKP_HOME}/backup/$(date +%Y%m%d%H%M%S)"

header "ASKP Complete Fix Script"
echo "This script will completely fix the ASKP CLI installation"

# Create backup directory
mkdir -p "${BACKUP_DIR}"
info "Created backup directory: ${BACKUP_DIR}"

# Backup shell config files
for config in ~/.bashrc ~/.bash_profile ~/.zshrc ~/.profile; do
    if [ -f "$config" ]; then
        cp "$config" "${BACKUP_DIR}/$(basename $config)"
        info "Backed up $config"
    fi
done

# Remove all askp and ask binaries from PATH
header "Removing all askp and ask binaries from PATH"
for dir in $(echo $PATH | tr ':' ' '); do
    if [ -f "$dir/askp" ]; then
        mv "$dir/askp" "${BACKUP_DIR}/askp_$(basename $dir)"
        info "Moved $dir/askp to backup"
    fi
    if [ -f "$dir/ask" ]; then
        mv "$dir/ask" "${BACKUP_DIR}/ask_$(basename $dir)"
        info "Moved $dir/ask to backup"
    fi
done

# Clean up shell config files
header "Cleaning shell configurations"
for config in ~/.bashrc ~/.bash_profile ~/.zshrc ~/.profile; do
    if [ -f "$config" ]; then
        # Remove old aliases and PATH entries
        sed -i.bak '/alias ask=.*/d' "$config"
        sed -i.bak '/alias askp=.*/d' "$config"
        sed -i.bak '/alias askd=.*/d' "$config"
        sed -i.bak '/# ASKD PATH/d' "$config"
        sed -i.bak '/# ASKP PATH/d' "$config"
        sed -i.bak '/export PATH=.*\.askd.*/d' "$config"
        sed -i.bak '/export PATH=.*\.askp.*/d' "$config"
        
        # Add correct PATH entry
        echo -e "\n# ASKP PATH - Added by complete_askp_fix.sh" >> "$config"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$config"
        
        info "Cleaned up $config"
        rm -f "$config.bak"
    fi
done

# Backup old ASKD environment
if [ -d "${HOME}/.askd" ]; then
    header "Backing up old ASKD environment"
    cp -r "${HOME}/.askd" "${BACKUP_DIR}/askd"
    info "Backed up old ASKD environment to ${BACKUP_DIR}/askd"
    
    # Rename the old ASKD directory to avoid conflicts
    mv "${HOME}/.askd" "${HOME}/.askd.old"
    info "Renamed old ASKD directory to ~/.askd.old"
fi

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

# Create direct executable scripts
header "Creating executable scripts"
mkdir -p ~/.local/bin

cat > ~/.local/bin/askp << SCRIPT
#!/bin/bash
# Direct ASKP CLI wrapper script
# Version: ${VERSION}

if [ "\$1" = "--version" ] || [ "\$1" = "-v" ]; then
    echo "askp version ${VERSION}"
    exit 0
fi

# Use the full path to the Python executable and the module
${ASKP_ENV}/bin/python -m askp.cli "\$@"
SCRIPT

cat > ~/.local/bin/ask << SCRIPT
#!/bin/bash
# Direct ASK CLI wrapper script
# Version: ${VERSION}

if [ "\$1" = "--version" ] || [ "\$1" = "-v" ]; then
    echo "ask version ${VERSION}"
    exit 0
fi

# Use the full path to the Python executable and the module
${ASKP_ENV}/bin/python -m askp.cli "\$@"
SCRIPT

chmod +x ~/.local/bin/askp ~/.local/bin/ask
info "Created executable scripts"

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
