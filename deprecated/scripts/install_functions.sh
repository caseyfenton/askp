#!/bin/bash

prompt_install_options() {
    if [ "${WIZARD}" = true ]; then
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
    else
        # Default to ~/.local/bin in non-interactive mode
        INSTALL_LOCAL_BIN=true
    fi
}

install_user_command() {
    local wrapper_path="$SCRIPT_DIR/scripts/system_wrapper"
    local install_dir
    local cmd_name
    
    if [ "${INSTALL_LOCAL_BIN}" = true ]; then
        install_dir="$HOME/.local/bin"
        mkdir -p "$install_dir"
        cmd_name="$install_dir/askp"
        cp "$wrapper_path" "$cmd_name"
        chmod +x "$cmd_name"
        ln -sf "$cmd_name" "$install_dir/ask"
        ln -sf "$cmd_name" "$install_dir/askp"
        info "✓ Installed to ~/.local/bin"
        
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
        cp "$wrapper_path" "$cmd_name"
        chmod +x "$cmd_name"
        ln -sf "$cmd_name" "$install_dir/ask"
        ln -sf "$cmd_name" "$install_dir/askp"
        info "✓ Installed to ~/bin"
        
        if [[ ":$PATH:" != *":$install_dir:"* ]]; then
            echo 'export PATH="$PATH:$HOME/bin"' >> "$HOME/.profile"
            info "Added ~/bin to PATH in ~/.profile"
            info "Run 'source ~/.profile' to update your PATH"
        fi
    fi
    
    if [ "${CREATE_ALIAS}" = true ]; then
        echo "alias askp='$wrapper_path'" >> "$SHELL_RC"
        echo "alias ask='$wrapper_path'" >> "$SHELL_RC"
        echo "alias askp='$wrapper_path'" >> "$SHELL_RC"
        info "✓ Added aliases to $SHELL_RC"
        info "Run 'source $SHELL_RC' to load the aliases"
    fi
}
