#!/bin/bash

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

info() { echo -e "${GREEN}$1${NC}"; }
error() { echo -e "${RED}$1${NC}"; }

# Installation options
INSTALL_LOCAL_BIN=false
INSTALL_HOME_BIN=false
CREATE_ALIAS=false
SHELL_RC=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER_PATH="$SCRIPT_DIR/system_wrapper"

prompt_install_options() {
    echo "Where would you like to install askp?"
    echo "1) ~/.local/bin (recommended, no sudo required)"
    echo "2) ~/bin (no sudo required)"
    echo "3) Create shell alias"
    echo "4) Skip installation"
    read -p "Choose option [1-4]: " choice
    
    case $choice in
        1) INSTALL_LOCAL_BIN=true ;;
        2) INSTALL_HOME_BIN=true ;;
        3) CREATE_ALIAS=true
           # Detect shell
           if [ -n "$ZSH_VERSION" ]; then
               SHELL_RC="$HOME/.zshrc"
           elif [ -n "$BASH_VERSION" ]; then
               SHELL_RC="$HOME/.bashrc"
           else
               read -p "Enter path to shell rc file: " SHELL_RC
           fi
           ;;
        4) info "Skipping system installation" ;;
        *) error "Invalid choice" && exit 1 ;;
    esac
}

install_command() {
    local install_dir
    local cmd_name
    
    if [ "${INSTALL_LOCAL_BIN}" = true ]; then
        install_dir="$HOME/.local/bin"
        mkdir -p "$install_dir"
        cmd_name="$install_dir/askp"
        cp "$WRAPPER_PATH" "$cmd_name"
        chmod +x "$cmd_name"
        ln -sf "$cmd_name" "$install_dir/ask"
        ln -sf "$cmd_name" "$install_dir/askp"
        info "✓ Installed to ~/.local/bin"
        
        # Add to PATH if needed
        if [[ ":$PATH:" != *":$install_dir:"* ]]; then
            echo 'export PATH="$PATH:$HOME/.local/bin"' >> "$HOME/.profile"
            info "Added ~/.local/bin to PATH in ~/.profile"
            info "Run 'source ~/.profile' to update your PATH"
        fi
    fi
    
    if [ "${INSTALL_HOME_BIN}" = true ]; then
        install_dir="$HOME/bin"
        mkdir -p "$install_dir"
        cmd_name="$install_dir/askp"
        cp "$WRAPPER_PATH" "$cmd_name"
        chmod +x "$cmd_name"
        ln -sf "$cmd_name" "$install_dir/ask"
        ln -sf "$cmd_name" "$install_dir/askp"
        info "✓ Installed to ~/bin"
        
        # Add to PATH if needed
        if [[ ":$PATH:" != *":$install_dir:"* ]]; then
            echo 'export PATH="$PATH:$HOME/bin"' >> "$HOME/.profile"
            info "Added ~/bin to PATH in ~/.profile"
            info "Run 'source ~/.profile' to update your PATH"
        fi
    fi
    
    if [ "${CREATE_ALIAS}" = true ]; then
        echo "alias askp='$WRAPPER_PATH'" >> "$SHELL_RC"
        echo "alias ask='$WRAPPER_PATH'" >> "$SHELL_RC"
        echo "alias askp='$WRAPPER_PATH'" >> "$SHELL_RC"
        info "✓ Added aliases to $SHELL_RC"
        info "Run 'source $SHELL_RC' to load the aliases"
    fi
}

# Test run
prompt_install_options
install_command
