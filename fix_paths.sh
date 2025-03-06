#!/bin/bash
set -e

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}ASKP Path Fix Utility${NC}"
echo "========================================"
echo "Fixing paths and ensuring correct execution of ASKP CLI"

# 1. Remove duplicate and old paths
echo -e "\n${GREEN}Cleaning up existing paths...${NC}"
rm -f /Users/casey/.local/bin/askp /Users/casey/.local/bin/ask 2>/dev/null || true
rm -f /Users/casey/bin/askp /Users/casey/bin/ask 2>/dev/null || true

# 2. Create correct symlinks for the new paths
echo -e "\n${GREEN}Creating correct symlinks...${NC}"
ln -sf /Users/casey/.askp/env/bin/askp /Users/casey/.local/bin/askp
ln -sf /Users/casey/.askp/env/bin/ask /Users/casey/.local/bin/ask
echo "Created symlinks in ~/.local/bin"

# 3. Update the PATH priority in shell configuration
echo -e "\n${GREEN}Checking shell configuration...${NC}"
for rc_file in ~/.bashrc ~/.bash_profile ~/.zshrc; do
  if [ -f "$rc_file" ]; then
    if ! grep -q "export PATH=\"\$HOME/.local/bin:\$PATH\"" "$rc_file"; then
      echo -e "\n# ASKP PATH Priority\nexport PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$rc_file"
      echo "Updated PATH in $rc_file"
    else
      echo "PATH already correctly configured in $rc_file"
    fi
  fi
done

# 4. Verify installation
echo -e "\n${GREEN}Verifying installation...${NC}"
echo "Installed ASKP at: $(which askp 2>/dev/null || echo 'Not found')"
echo "Installed ASK at: $(which ask 2>/dev/null || echo 'Not found')"

echo -e "\n${YELLOW}IMPORTANT:${NC} Please restart your shell or run 'source ~/.bashrc' (or your shell's rc file)"
echo "Then try running 'askp' or 'ask' again"
