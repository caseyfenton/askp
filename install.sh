#!/usr/bin/env bash
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

VERSION="2.0.0"
DEFAULT_PREFIX="/usr/local"
ASKP_HOME="${HOME}/.askp"
VENV_DIR="${ASKP_HOME}/env"
BACKUP_DIR="${ASKP_HOME}/backup"
mkdir -p "${ASKP_HOME}" "${BACKUP_DIR}" "${VENV_DIR}"

# Installation flags.
INSTALL_LOCAL_BIN=false
INSTALL_HOME_BIN=false
CREATE_ALIAS=false

# Colors.
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

# Logging.
log() { echo -e "${2:-$NC}$1${NC}"; }
info() { log "$1" "$GREEN"; }
warn() { log "$1" "$YELLOW"; }
error() { log "$1" "$RED"; }
header() { echo -e "\n${BLUE}=== $1 ===${NC}\n"; }

uninstall() {
    header "Uninstalling ASKP"
    for cmd in askp ask; do
        [ -f "${PREFIX}/bin/${cmd}" ] && { rm -f "${PREFIX}/bin/${cmd}"; info "Removed ${cmd}"; }
    done
    if [ -d "${ASKP_HOME}" ]; then
        read -p "Remove configuration directory? [y/N] " -n 1 -r; echo
        [[ $REPLY =~ ^[Yy]$ ]] && { rm -rf "${ASKP_HOME}"; info "Removed configuration"; }
    fi
    info "Uninstall complete!"; exit 0
}

parse_args() {
    PREFIX="${DEFAULT_PREFIX}"; WIZARD=false; NO_SYMLINKS=false; UNINSTALL=false
    while [ $# -gt 0 ]; do
        case "$1" in
            --help|-h) show_help; exit 0 ;;
            --version|-v) echo "ASKP Installer v${VERSION}"; exit 0 ;;
            --prefix) PREFIX="$2"; shift ;;
            --no-symlinks) NO_SYMLINKS=true ;;
            --wizard|-w) WIZARD=true ;;
            --uninstall) UNINSTALL=true ;;
            *) warn "Unknown option: $1"; show_help; exit 1 ;;
        esac
        shift
    done
    [ "${UNINSTALL}" = true ] && uninstall
}

show_help() {
    cat <<EOF
ASKP Installer v${VERSION}

Usage: install.sh [OPTIONS]

  --help, -h         Show this help message.
  --version, -v      Show version information.
  --prefix PATH      Set installation prefix (default: ${DEFAULT_PREFIX}).
  --no-symlinks      Do not create symlinks.
  --wizard, -w       Run installation wizard.
  --uninstall        Uninstall ASKP.
EOF
}

detect_platform() {
    case "$OSTYPE" in
        msys*|win32*|cygwin*) PLATFORM="windows" ;;
        darwin*) PLATFORM="macos" ;;
        linux-gnu*) PLATFORM="linux" ;;
        *) PLATFORM="unknown"; warn "Unknown platform: $OSTYPE" ;;
    esac
    info "${PLATFORM^} system detected"
}
get_platform_paths() {
    if [ "$PLATFORM" = "windows" ]; then
        PYTHON_BIN_PATH="$HOME/AppData/Local/Programs/Python"
        SHELL_PROFILES=("$HOME/.bashrc")
        EXE_EXTENSION=".exe"
    else
        PYTHON_BIN_PATH="/usr/bin:/usr/local/bin:$HOME/.local/bin"
        SHELL_PROFILES=("$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.zshrc" "$HOME/.profile")
        EXE_EXTENSION=""
    fi
}

check_system() {
    detect_platform; get_platform_paths
    if [ "$PLATFORM" = "windows" ]; then
        command -v python >/dev/null 2>&1 && PYTHON_CMD="python" || { error "Python 3 required"; show_manual_instructions; exit 1; }
        python --version 2>&1 | grep -q "3\." || { error "Python 3 required"; exit 1; }
    else
        if command -v python3 >/dev/null 2>&1; then
            PYTHON_CMD="python3"
        elif command -v python >/dev/null 2>&1 && python --version 2>&1 | grep -q "3\."; then
            PYTHON_CMD="python"
        else
            error "Python 3 required"; show_manual_instructions; exit 1
        fi
    fi
    info "Python 3 found: ${PYTHON_CMD}"
    [ "$PLATFORM" != "windows" ] && { [ "${PREFIX}" = "${DEFAULT_PREFIX}" ] && [ ! -w "${PREFIX}/bin" ] && { warn "No write permission for ${PREFIX}/bin"; exit 1; }; }
}

show_manual_instructions() {
    header "Manual Installation Instructions"
    if [ "$PLATFORM" = "windows" ]; then
        echo "1. Create virtual environment: python -m venv %USERPROFILE%\\.askp\\env"
        echo "2. Activate: %USERPROFILE%\\.askp\\env\\Scripts\\activate"
        echo "3. Install: pip install -e ${SCRIPT_DIR}"
        echo "4. Create a batch file for askp."
    else
        echo "1. Create virtual environment: python3 -m venv ~/.askp/env"
        echo "2. Activate: source ~/.askp/env/bin/activate"
        echo "3. Install: pip install -e ${SCRIPT_DIR}"
        echo "4. Create a shell script in ~/bin or ~/.local/bin."
    fi
}

check_conflicts() {
    header "Checking for Conflicts"
    local conflicts=()
    for cmd in askp ask; do
        command -v "$cmd" >/dev/null 2>&1 && conflicts+=("$cmd ($(command -v "$cmd"))")
    done
    if [ ${#conflicts[@]} -gt 0 ]; then
        warn "Found existing commands:"; printf '%s\n' "${conflicts[@]}"
        read -p "Remove conflicting commands? [Y/n] " -n 1 -r; echo
        if [[ $REPLY =~ ^[Yy]$ || -z $REPLY ]]; then
            if [ "$PLATFORM" = "windows" ]; then
                for cmd in askp ask; do
                    rm -f "$HOME/AppData/Local/Programs/Python/Scripts/${cmd}${EXE_EXTENSION}"
                done
            else
                for cmd in askp ask; do
                    rm -f ~/.local/bin/$cmd ~/bin/$cmd /usr/local/bin/$cmd /usr/bin/$cmd
                done
            fi
            info "Removed conflicting commands"
        else
            error "Installation may conflict with existing commands"; exit 1
        fi
    fi
}

setup_venv() {
    header "Setting up Virtual Environment"
    [ ! -d "${ASKP_HOME}" ] && mkdir -p "${ASKP_HOME}"
    [ ! -d "${ASKP_HOME}/logs" ] && mkdir -p "${ASKP_HOME}/logs"
    if [ -d "${VENV_DIR}" ]; then
        if { [ "$PLATFORM" = "windows" ] && [ ! -f "${VENV_DIR}/Scripts/activate" ]; } || { [ "$PLATFORM" != "windows" ] && [ ! -f "${VENV_DIR}/bin/activate" ]; }; then
            info "Recreating virtual environment..."; rm -rf "${VENV_DIR}"
        else
            info "Using existing virtual environment"
        fi
    fi
    if [ ! -d "${VENV_DIR}" ]; then
        info "Creating virtual environment at ${VENV_DIR}..."
        ${PYTHON_CMD} -m venv "${VENV_DIR}" || {
            warn "venv module failed; trying virtualenv..."
            command -v virtualenv >/dev/null 2>&1 || ${PYTHON_CMD} -m pip install --user virtualenv
            virtualenv "${VENV_DIR}" || { error "Failed to create venv"; show_manual_instructions; exit 1; }
        }
        info "Virtual environment created"
    fi
    if [ "$PLATFORM" = "windows" ]; then
        [ ! -f "${VENV_DIR}/Scripts/activate" ] && { error "Activation script missing"; show_manual_instructions; exit 1; }
        source "${VENV_DIR}/Scripts/activate"
    else
        [ ! -f "${VENV_DIR}/bin/activate" ] && { error "Activation script missing"; show_manual_instructions; exit 1; }
        source "${VENV_DIR}/bin/activate"
    fi
    [ -z "$VIRTUAL_ENV" ] && { error "Failed to activate virtual environment"; exit 1; }
    info "Virtual environment activated"
    ${PYTHON_CMD} -m pip install --quiet --upgrade pip wheel || warn "pip upgrade failed"
    [ -f "${SCRIPT_DIR}/setup.py" ] && ${PYTHON_CMD} -m pip install --quiet -e "${SCRIPT_DIR}" && info "Installed local package" || { error "Local package installation failed"; exit 1; }
}

update_path() {
    local bin_dir
    if [ "${INSTALL_LOCAL_BIN}" = true ]; then
        bin_dir="${HOME}/.local/bin"
    elif [ "${INSTALL_HOME_BIN}" = true ]; then
        bin_dir="${HOME}/bin"
    else
        return
    fi
    [ ! -d "$bin_dir" ] && { mkdir -p "$bin_dir"; info "Created bin directory: $bin_dir"; }
    local rc_file="${SHELL_RC:-$HOME/.bashrc}"
    if ! grep -q "export PATH=\"$bin_dir:\$PATH\"" "$rc_file" 2>/dev/null; then
        echo -e "\n# ASKP PATH\nexport PATH=\"$bin_dir:\$PATH\"" >> "$rc_file"
        info "Updated PATH in $rc_file"
    fi
}

create_target_directory() {
    header "Creating Target Directory"
    local target_dir
    if [ "${INSTALL_LOCAL_BIN}" = true ]; then
        target_dir="${HOME}/.local/bin"
    elif [ "${INSTALL_HOME_BIN}" = true ]; then
        target_dir="${HOME}/bin"
    else
        target_dir="${PREFIX}/bin"
    fi
    [ ! -d "${target_dir}" ] && { mkdir -p "${target_dir}"; info "Created target directory: ${target_dir}"; }
    [ ! -w "${target_dir}" ] && { error "Target directory ${target_dir} is not writable"; exit 1; }
}

create_cli_script() {
    header "Creating CLI Script"
    local script_content
    if [ "$PLATFORM" = "windows" ]; then
        script_content="@echo off
call \"${VENV_DIR//\//\\}\\Scripts\\activate.bat\"
python -m askp.cli %*"
    else
        script_content="#!/bin/bash
source \"${VENV_DIR}/bin/activate\"
python -m askp.cli \"\$@\""
    fi
    local script_path
    if [ "${INSTALL_LOCAL_BIN}" = true ]; then
        script_path="${HOME}/.local/bin/askp"
    elif [ "${INSTALL_HOME_BIN}" = true ]; then
        script_path="${HOME}/bin/askp"
    else
        script_path="${PREFIX}/bin/askp"
    fi
    echo "$script_content" > "$script_path"
    chmod +x "$script_path"
    if [ "$PLATFORM" = "windows" ] && { [ "${INSTALL_LOCAL_BIN}" = true ] || [ "${INSTALL_HOME_BIN}" = true ]; }; then
        echo "$script_content" > "${script_path}.bat"
        info "Created Windows batch file: ${script_path}.bat"
    fi
    info "Created CLI script: $script_path"
}

link_commands() {
    header "Linking Commands"
    [ "$NO_SYMLINKS" = true ] && { info "Skipping symlinks (--no-symlinks)"; return; }
    local target_dir
    if [ "${INSTALL_LOCAL_BIN}" = true ]; then
        target_dir="${HOME}/.local/bin"; mkdir -p "$target_dir"
    elif [ "${INSTALL_HOME_BIN}" = true ]; then
        target_dir="${HOME}/bin"; mkdir -p "$target_dir"
    elif [ "${CREATE_ALIAS}" = true ]; then
        info "Skipping symlinks (using aliases)"; return
    else
        target_dir="${PREFIX}/bin"
    fi
    if [ "$PLATFORM" = "windows" ]; then
        echo "@echo off
call \"${target_dir}\\askp.bat\" %*" > "${target_dir}/ask.bat"
        info "Created ask.bat"
    else
        ln -sf "${target_dir}/askp" "${target_dir}/ask"
        info "Created symlink: ask -> askp"
    fi
}

create_aliases() {
    header "Creating Shell Aliases"
    [ "$CREATE_ALIAS" = false ] && { info "Skipping aliases"; return; }
    local rc_file="${SHELL_RC:-$HOME/.bashrc}"
    local alias_cmd="alias askp='${SCRIPT_DIR}/scripts/system_wrapper'
alias ask='askp'"
    if ! grep -q "alias askp=" "$rc_file" 2>/dev/null; then
        echo -e "\n# ASKP Aliases\n${alias_cmd}" >> "$rc_file"
        info "Added aliases to $rc_file"
    else
        info "Aliases already exist in $rc_file"
    fi
}

create_config() {
    local config_file="${ASKP_HOME}/config"
    [ ! -f "$config_file" ] && {
        cat > "$config_file" <<EOF
# ASKP Configuration
version=${VERSION}
install_path=${TARGET_DIR}
install_date=$(date)
platform=${PLATFORM}
EOF
        info "Created default configuration"
    }
}

cleanup() {
    header "Cleaning Up"
    [ -d "${TEMP_DIR}" ] && { rm -rf "${TEMP_DIR}"; info "Removed temporary directory"; }
}

verify() {
    header "Verification"
    local cmd_path
    if [ "${INSTALL_LOCAL_BIN}" = true ]; then
        cmd_path="$HOME/.local/bin/askp"
    elif [ "${INSTALL_HOME_BIN}" = true ]; then
        cmd_path="$HOME/bin/askp"
    elif [ "${CREATE_ALIAS}" = true ]; then
        cmd_path="${SCRIPT_DIR}/scripts/system_wrapper"
    else
        cmd_path="${PREFIX}/bin/askp"
    fi
    "$cmd_path" --version &>/dev/null && info "Command verification passed" || warn "Command verification failed"
    [ "$NO_SYMLINKS" = false ] && [ -w "${PREFIX}/bin" ] && {
        for cmd in ask askp; do
            [ -L "${PREFIX}/bin/${cmd}" ] && info "${cmd} symlink verified" || warn "${cmd} symlink missing"
        done
    }
}

print_completion() {
    header "Installation Complete"
    if [ -f "${ASKP_HOME}/.env" ] && grep -q "PERPLEXITY_API_KEY" "${ASKP_HOME}/.env"; then
        echo "ASKP installed with API key configuration."
    else
        echo "ASKP installed without an API key."
        echo "Set it later by adding PERPLEXITY_API_KEY to ${ASKP_HOME}/.env"
    fi
    echo -e "\nTo use ASKP, open a new terminal and run: askp \"your query here\""
    echo "For more info: https://github.com/caseyfenton/askp"
    [ "$PLATFORM" = "windows" ] && echo "On Windows, restart your terminal or command prompt."
}

print_banner() {
    echo -e "${BLUE}"
    echo "    _    ____  _  ______  "
    echo "   / \\  / ___|| |/ /  _ \\ "
    echo "  / _ \\ \\___ \\| ' /| |_) |"
    echo " / ___ \\ ___) | . \\|  __/ "
    echo "/_/   \\_\\____/|_|\\_\\_|    "
    echo -e "${NC}"
    echo "ASKP CLI Installer v${VERSION}"
    echo "---------------------------"
    echo "Advanced search using the Perplexity API."
    echo
}

perform_installation() {
    trap 'error "Installation failed at line $LINENO"; show_manual_instructions; exit 1' ERR
    TEMP_DIR=$(mktemp -d)
    check_system
    check_conflicts
    setup_venv
    create_target_directory
    create_cli_script
    link_commands
    create_aliases
    update_path
    create_config
    trap - ERR
    verify
    cleanup
    print_completion
}

main() {
    print_banner
    parse_args "$@"
    if [ "$WIZARD" = true ]; then
        header "Installation Wizard"
        echo "Welcome to the ASKP installation wizard!"
    fi
    perform_installation
}

main "$@"