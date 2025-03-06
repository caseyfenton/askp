#!/bin/bash
# Script to fix askp import errors by cleaning up old installations

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
log() { echo -e "${2:-$NC}$1${NC}"; }
info() { log "$1" "$GREEN"; }
warn() { log "$1" "$YELLOW"; }
error() { log "$1" "$RED"; }

echo -e "${GREEN}=== ASKP Cleanup Tool ===${NC}"
echo -e "This script will fix import errors by cleaning up old askd/askp installations"
echo

# Find all askp and askd executables
echo -e "${YELLOW}Finding all askp and askd executables...${NC}"
ASKP_EXECS=$(which -a askp 2>/dev/null || echo "")
ASKD_EXECS=$(which -a askd 2>/dev/null || echo "")

echo -e "Found these askp executables:"
echo "$ASKP_EXECS" | awk '{print "  " $0}'
echo
echo -e "Found these askd executables:"
echo "$ASKD_EXECS" | awk '{print "  " $0}'
echo

# Backup the files before removal
echo -e "${YELLOW}Creating backup directory...${NC}"
BACKUP_DIR="$HOME/.askp_backup_$(date +%Y%m%d%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}Backing up executables...${NC}"
for exec_file in $ASKP_EXECS $ASKD_EXECS; do
    # Skip the main .askp/env executable
    if [[ "$exec_file" != "$HOME/.askp/env/bin/askp" ]]; then
        base_name=$(basename "$exec_file")
        dir_name=$(dirname "$exec_file")
        mkdir -p "$BACKUP_DIR/$dir_name"
        cp -p "$exec_file" "$BACKUP_DIR/$exec_file" 2>/dev/null
        rm -f "$exec_file" 2>/dev/null
        echo "  Backed up and removed: $exec_file"
    else
        echo "  Keeping main executable: $exec_file"
    fi
done

# Create new clean scripts in common locations
echo -e "${YELLOW}Creating new clean scripts...${NC}"
for bin_dir in "/usr/local/bin" "$HOME/.local/bin" "$HOME/bin"; do
    if [ -d "$bin_dir" ]; then
        # Create askp
        cat > "$bin_dir/askp" << 'ASKP'
#!/bin/bash
# ASKP CLI Launcher - Clean version
source "$HOME/.askp/env/bin/activate"
python -m askp.cli "$@"
ASKP
        chmod +x "$bin_dir/askp"
        
        # Create ask as symlink
        ln -sf "$bin_dir/askp" "$bin_dir/ask"
        
        echo "  Created clean scripts in $bin_dir"
    fi
done

# Check for site-packages with askd module
echo -e "${YELLOW}Checking for old Python packages...${NC}"
SITE_PACKAGES=$($HOME/.askp/env/bin/python -c "import site; print(site.getsitepackages()[0])")
if [ -d "$SITE_PACKAGES/askd" ]; then
    echo "  Found old askd package in $SITE_PACKAGES"
    mkdir -p "$BACKUP_DIR/site-packages"
    cp -pr "$SITE_PACKAGES/askd" "$BACKUP_DIR/site-packages/"
    rm -rf "$SITE_PACKAGES/askd"
    echo "  Backed up and removed old askd package"
fi

echo
echo -e "${GREEN}Clean-up completed!${NC}"
echo -e "Backup created at: $BACKUP_DIR"
echo -e "Try running 'askp' again - it should now use the correct module."
echo -e "If you still have issues, restart your terminal or try: source ~/.bashrc"
