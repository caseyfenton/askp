#!/bin/bash
set -e

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== ASKP Complete Fix Script ===${NC}"
echo -e "${BLUE}Fixing all ASKP CLI installation issues${NC}"

# Step 1: Ensure we have a clean state
echo -e "\n${GREEN}Step 1: Cleaning up existing files and links${NC}"
# Remove any existing symlinks
rm -f ~/.local/bin/askp ~/.local/bin/ask 2>/dev/null || true
rm -f ~/bin/askp ~/bin/ask 2>/dev/null || true
echo "Removed existing symlinks"

# Step 2: Update the Python package
echo -e "\n${GREEN}Step 2: Reinstalling the ASKP package${NC}"
cd "$(dirname "$0")"
if [ -d ~/.askp/env ]; then
  source ~/.askp/env/bin/activate
  pip install --quiet --upgrade -e .
  deactivate
  echo "Updated ASKP package installation"
else
  echo -e "${YELLOW}Creating new virtual environment${NC}"
  mkdir -p ~/.askp
  python3 -m venv ~/.askp/env
  source ~/.askp/env/bin/activate
  pip install --quiet --upgrade pip wheel
  pip install --quiet -e .
  deactivate
  echo "Created new virtual environment and installed ASKP"
fi

# Step 3: Create proper wrapper scripts
echo -e "\n${GREEN}Step 3: Creating wrapper scripts${NC}"
mkdir -p ~/.local/bin

cat > ~/.local/bin/askp << 'SCRIPT'
#!/bin/bash
source ~/.askp/env/bin/activate > /dev/null 2>&1
exec python -m askp.cli "$@"
SCRIPT
chmod +x ~/.local/bin/askp
echo "Created ~/.local/bin/askp"

cat > ~/.local/bin/ask << 'SCRIPT'
#!/bin/bash
source ~/.askp/env/bin/activate > /dev/null 2>&1
exec python -m askp.cli "$@"
SCRIPT
chmod +x ~/.local/bin/ask
echo "Created ~/.local/bin/ask"

# Step 4: Clean up shell configurations
echo -e "\n${GREEN}Step 4: Cleaning up shell configurations${NC}"
for rc_file in ~/.bashrc ~/.bash_profile ~/.zshrc ~/.profile; do
  if [ -f "$rc_file" ]; then
    cp "$rc_file" "$rc_file.bak.$(date +%Y%m%d%H%M%S)"
    sed -i.tmp '/alias ask=.*/d' "$rc_file"
    sed -i.tmp '/alias askp=.*/d' "$rc_file"
    rm -f "$rc_file.tmp"
    echo "Cleaned up aliases in $rc_file"
  fi
done

# Ensure .local/bin is in PATH
if ! grep -q 'PATH="$HOME/.local/bin:$PATH"' ~/.bashrc; then
  echo -e '\n# ASKP PATH setting\nexport PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  echo "Added PATH setting to ~/.bashrc"
fi

if [ -f ~/.zshrc ] && ! grep -q 'PATH="$HOME/.local/bin:$PATH"' ~/.zshrc; then
  echo -e '\n# ASKP PATH setting\nexport PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
  echo "Added PATH setting to ~/.zshrc"
fi

# Step 5: Verify installation
echo -e "\n${GREEN}Step 5: Verifying installation${NC}"
echo "ASKP script location: $(which askp 2>/dev/null || echo 'Not found')"
echo "ASK script location: $(which ask 2>/dev/null || echo 'Not found')"

# Step 6: Instructions
echo -e "\n${YELLOW}Installation complete!${NC}"
echo -e "${GREEN}To use ASKP, please restart your terminal or run:${NC}"
echo '  source ~/.bashrc  # For bash shell'
echo '  source ~/.zshrc   # For zsh shell'

# Step 7: Optional pip package
echo -e "\n${BLUE}=== ADDITIONAL INFORMATION ===${NC}"
echo -e "You asked about a pip package for ASKP. Currently, ASKP is set up for local development."
echo -e "If you want to make it available as a global pip package, you would need to:"
echo -e "1. Upload it to PyPI with: python -m build && python -m twine upload dist/*"
echo -e "2. Then users could install with: pip install askp"
echo -e "3. For now, the current installation approach with the wrapper scripts is recommended"
