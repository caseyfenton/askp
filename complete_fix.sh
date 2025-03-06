#!/bin/bash
# Comprehensive fix for askp/askd conflicts

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

echo -e "${GREEN}=== ASKP Complete Fix Tool ===${NC}"
echo -e "This script will completely resolve all askp/askd conflicts"
echo

# Create backup directory
BACKUP_DIR="$HOME/.askp_complete_backup_$(date +%Y%m%d%H%M%S)"
mkdir -p "$BACKUP_DIR"
info "Created backup directory: $BACKUP_DIR"

# Step 1: Backup and disable old .askd environment
if [ -d "$HOME/.askd" ]; then
    echo -e "${YELLOW}Found old .askd environment - backing up${NC}"
    cp -pr "$HOME/.askd" "$BACKUP_DIR/"
    # Rename rather than delete to preserve data but prevent usage
    mv "$HOME/.askd" "$HOME/.askd_old"
    echo "  ✓ Old .askd environment backed up and renamed"
fi

# Step 2: Remove any remaining askp/askd executables
echo -e "${YELLOW}Removing any remaining askp/askd executables...${NC}"
ASKP_EXECS=$(which -a askp 2>/dev/null || echo "")
ASKD_EXECS=$(which -a askd 2>/dev/null || echo "")
ASK_EXECS=$(which -a ask 2>/dev/null || echo "")

# Create backup subdirectories
mkdir -p "$BACKUP_DIR/bin"

# Process all executables
for exec_file in $ASKP_EXECS $ASKD_EXECS $ASK_EXECS; do
    # Skip the main askp env executable
    if [[ "$exec_file" != "$HOME/.askp/env/bin/askp" ]]; then
        base_name=$(basename "$exec_file")
        dir_name=$(dirname "$exec_file")
        mkdir -p "$BACKUP_DIR/$dir_name"
        cp -p "$exec_file" "$BACKUP_DIR/$exec_file" 2>/dev/null
        rm -f "$exec_file" 2>/dev/null
        echo "  ✓ Removed: $exec_file"
    else
        echo "  ✓ Keeping main executable: $exec_file"
    fi
done

# Step 3: Create fresh clean scripts in common bin directories
echo -e "${YELLOW}Creating new clean scripts...${NC}"
for bin_dir in "$HOME/.local/bin" "$HOME/bin"; do
    if [ -d "$bin_dir" ]; then
        # Create askp launcher
        cat > "$bin_dir/askp" << 'ASKP'
#!/bin/bash
# ASKP CLI Launcher - Clean version

# Environment setup
export ASKP_HOME="$HOME/.askp"
export ASKP_ENV="$ASKP_HOME/env"

# Ensure we use the right Python interpreter
if [ -f "$ASKP_ENV/bin/python" ]; then
    "$ASKP_ENV/bin/python" -m askp.cli "$@"
else
    echo "Error: ASKP environment not found. Please reinstall ASKP."
    exit 1
fi
ASKP
        chmod +x "$bin_dir/askp"
        
        # Create ask symlink
        ln -sf "$bin_dir/askp" "$bin_dir/ask"
        
        echo "  ✓ Created clean scripts in $bin_dir"
    fi
done

# Step 4: Update PATH precedence to ensure new scripts are found first
echo -e "${YELLOW}Updating PATH settings...${NC}"
PATH_UPDATE=$(cat << 'PATH_SCRIPT'
# Added by ASKP complete fix script
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"
PATH_SCRIPT
)

for rc_file in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    if [ -f "$rc_file" ]; then
        if ! grep -q "Added by ASKP complete fix script" "$rc_file"; then
            cp -p "$rc_file" "$BACKUP_DIR/"
            echo -e "\n$PATH_UPDATE" >> "$rc_file"
            echo "  ✓ Updated PATH in $rc_file"
        fi
    fi
done

# Step 5: Final verification
echo -e "${YELLOW}Verifying installation...${NC}"

# Ensure askp environment is properly set up
if [ ! -d "$HOME/.askp/env" ]; then
    echo "  ⚠ ASKP environment not found, creating it..."
    mkdir -p "$HOME/.askp"
    cd "$HOME/.askp"
    python3 -m venv env
    source env/bin/activate
    pip install --quiet --upgrade pip

    # Install askp package
    if [ -d "/Users/casey/CascadeProjects/askp" ]; then
        pip install --quiet -e "/Users/casey/CascadeProjects/askp"
        echo "  ✓ Installed ASKP package from /Users/casey/CascadeProjects/askp"
    else
        echo "  ⚠ Could not find ASKP package directory"
    fi
else
    echo "  ✓ ASKP environment exists"
fi

echo
echo -e "${GREEN}Clean-up and fixes completed!${NC}"
echo -e "Backup created at: $BACKUP_DIR"
echo -e "To use the new installation immediately, please run:"
echo -e "  source $HOME/.bashrc  # or .zshrc if using zsh"
echo -e "\nThen try running 'askp' or 'ask'"
