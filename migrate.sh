#!/usr/bin/env bash
# migrate.sh - Migration script from askd to askp

set -e

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

# Print banner
print_banner() {
    echo -e "
    _    ____  _  ______  
   / \  / ___|| |/ /  _ \ 
  / _ \ \___ \| ' /| |_) |
 / ___ \ ___) | . \|  __/ 
/_/   \_\____/|_|\_\_|    

ASKP Migration Tool
------------------
This script helps migrate from askd to askp.
"
}

# Main migration function
migrate() {
    local old_dir="${HOME}/.askd"
    local new_dir="${HOME}/.askp"
    
    # Create new directory if it doesn't exist
    mkdir -p "$new_dir/logs" "$new_dir/backup"
    
    info "Checking for previous askd installation..."
    if [ -d "$old_dir" ]; then
        info "Found previous askd installation at $old_dir"
        
        # Copy over configuration files if they exist
        if [ -f "$old_dir/.env" ]; then
            info "Migrating API keys and configuration..."
            cp "$old_dir/.env" "$new_dir/" 2>/dev/null || true
        fi
        
        if [ -f "$old_dir/config" ]; then
            info "Migrating configuration file..."
            cp "$old_dir/config" "$new_dir/" 2>/dev/null || true
        fi
        
        # Copy cost logs if they exist
        if [ -d "$old_dir/cost_logs" ]; then
            info "Migrating cost logs..."
            mkdir -p "$new_dir/cost_logs" 2>/dev/null || true
            cp -r "$old_dir/cost_logs/"* "$new_dir/cost_logs/" 2>/dev/null || true
        fi
        
        # Remove old command wrappers
        for cmd in "ask" "askd"; do
            for dir in "/usr/local/bin" "$HOME/.local/bin" "$HOME/bin"; do
                if [ -f "$dir/$cmd" ]; then
                    info "Removing old command wrapper: $dir/$cmd"
                    rm -f "$dir/$cmd" 2>/dev/null || true
                fi
            done
        done
        
        # Update pip install
        info "Updating virtual environment..."
        if [ -d "$new_dir/env" ]; then
            # Fix virtual environment paths
            if [ -f "$new_dir/env/bin/activate" ]; then
                info "Activating virtual environment..."
                source "$new_dir/env/bin/activate"
                
                # Install from current directory
                info "Installing package from current directory..."
                SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
                pip install --quiet --upgrade -e "$SCRIPT_DIR" || warn "Failed to install package"
                
                # Deactivate virtual environment
                deactivate 2>/dev/null || true
            fi
        fi
        
        # Backup old installation instead of removing it
        local backup_dir="$old_dir.bak.$(date +%Y%m%d%H%M%S)"
        info "Creating backup of old installation at $backup_dir"
        mv "$old_dir" "$backup_dir" 2>/dev/null || warn "Failed to create backup"
        
        info "Migration from askd to askp completed successfully!"
        info "Your old installation has been backed up to: $backup_dir"
        info "To complete the process, run: ./install.sh --wizard"
    else
        info "No previous askd installation found, nothing to migrate"
        info "Please run: ./install.sh --wizard for a fresh installation"
    fi
}

# Main execution
print_banner
migrate
