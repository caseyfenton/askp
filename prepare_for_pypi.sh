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
VERSION="2.1.0"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ASKP_ENV="${HOME}/.askp/env"

header "ASKP PyPI Preparation Script"
echo "This script will prepare the ASKP package for PyPI deployment"

# Ensure we're using the correct Python environment
if [ -d "${ASKP_ENV}" ]; then
    info "Using ASKP virtual environment at ${ASKP_ENV}"
    source "${ASKP_ENV}/bin/activate"
else
    warn "ASKP virtual environment not found at ${ASKP_ENV}"
    warn "Using system Python instead"
fi

# Check for required tools
header "Checking for required tools"
for cmd in python3 pip; do
    if ! command -v $cmd &> /dev/null; then
        error "Required command '$cmd' not found. Please install it first."
        exit 1
    fi
done

# Check for twine and install if needed
if ! command -v twine &> /dev/null; then
    info "Installing twine..."
    python3 -m pip install twine
fi

if ! command -v build &> /dev/null; then
    info "Installing build..."
    python3 -m pip install build
fi

info "All required tools are installed"

# Clean up previous builds
header "Cleaning up previous builds"
rm -rf build/ dist/ *.egg-info/
info "Cleaned up previous builds"

# Install development dependencies
header "Installing development dependencies"
python3 -m pip install --upgrade pip wheel setuptools twine build
info "Installed development dependencies"

# Run tests
header "Running tests"
if [ -d "tests" ]; then
    info "Installing pytest..."
    python3 -m pip install pytest
    python3 -m pytest -xvs tests/
else
    warn "No tests directory found, skipping tests"
fi

# Build the package
header "Building the package"
python3 -m build
info "Built the package"

# Verify the package
header "Verifying the package"
python3 -m twine check dist/*
info "Package verification complete"

header "PyPI Preparation Complete!"
echo "To upload to PyPI Test:"
echo "  python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*"
echo
echo "To upload to PyPI:"
echo "  python3 -m twine upload dist/*"
echo
echo "To install from PyPI Test:"
echo "  pip install --index-url https://test.pypi.org/simple/ askp"
echo
echo "To install from PyPI:"
echo "  pip install askp"
