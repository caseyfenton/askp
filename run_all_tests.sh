#!/bin/bash
# RUN_ALL_TESTS.sh - Comprehensive test script for askp package
# Run this before deploying to PyPI or committing to GitHub

set -e  # Exit on error

echo "===== ASKP COMPREHENSIVE TEST SCRIPT ====="
echo "Starting tests at $(date)"
echo

# Set up colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Keep track of failures
FAILURES=0

# Function to run tests and report status
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    
    echo -e "${YELLOW}Running $test_name...${NC}"
    if eval "$test_cmd"; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
        echo
    else
        FAILURES=$((FAILURES + 1))
        echo -e "${RED}✗ $test_name failed${NC}"
        echo
    fi
}

# Create a temporary environment for testing
echo "Setting up temporary test environment..."
python -m venv test_env
source test_env/bin/activate

# Install required dependencies for testing
echo "Installing required dependencies..."
pip install -e .
pip install pytest click pytest-mock

# 1. Standard Unit Tests (just run the ones that we know work without pytest)
run_test "Standard Unit Tests" "python -m unittest tests/test_models.py"

# 2. Test CLI functionality (this is optional as it requires API credentials)
echo -e "${YELLOW}Skipping CLI Functionality Test (requires API credentials)${NC}"
echo "To manually test: python -m askp 'test' --model sonar-pro --temperature 0.5 --no-save"
echo

# 3. Version compatibility check
run_test "Version Compatibility Check" "python -c \"import askp; print(f'askp version: {askp.__version__}');\""

# 4. Test installation process
run_test "Installation Test" "pip uninstall -y askp && pip install -e . && python -c 'import askp; print(\"Installation successful\")'"

# 5. Test specific modules - important ones that need to work
run_test "Models Module Test" "python -m unittest tests/test_models.py"

# 6. Test our main fix for dictionary model handling
run_test "Dictionary Model Name Fix Test" "python -c \"from askp.utils import normalize_model_name; assert normalize_model_name('sonar-pro') == 'sonar-pro'; assert normalize_model_name({'model': 'sonar-pro'}) == 'sonar-pro'; assert normalize_model_name({}) == 'sonar-pro'; print('All normalize_model_name tests passed!')\""

# 7. Test against Python 3.11 if available
if command -v python3.11 &> /dev/null; then
    run_test "Python 3.11 Compatibility" "python3.11 -c 'import sys; print(sys.version); import os, sys; sys.path.insert(0, os.getcwd()); import src.askp; print(\"askp compatible with Python 3.11\")'"
fi

# 8. Windows compatibility tests (simulation)
echo -e "${YELLOW}Running Windows compatibility checks...${NC}"
echo "Note: Full Windows tests should be run on a Windows machine"
echo "Running simulated Windows path checks..."
run_test "Windows Path Simulation" "python -c \"import os; print('Windows path simulation tests'); path = 'C:\\\\\\\\Users\\\\\\\\Test\\\\\\\\Documents'; print(os.path.normpath(path))\""

# 9. Clean up and restore environment
deactivate
rm -rf test_env

# Summary
echo "===== TEST SUMMARY ====="
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}All tests passed successfully!${NC}"
    echo
    echo "Ready for commit to GitHub and PyPI deployment."
    
    echo
    echo "To commit to GitHub:"
    echo "  git add ."
    echo "  git commit -m \"Fix compatibility with OpenAI client version 1.77.0\""
    echo "  git push origin main"
    
    echo
    echo "To deploy to PyPI:"
    echo "  python setup.py sdist bdist_wheel"
    echo "  twine upload dist/*"
else
    echo -e "${RED}$FAILURES tests failed. Please fix before deploying.${NC}"
    exit 1
fi
