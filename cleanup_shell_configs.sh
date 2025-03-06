#!/bin/bash
set -e

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}ASKP Shell Configuration Cleanup${NC}"
echo "========================================"

# Clean up bashrc
echo -e "\n${GREEN}Cleaning up ~/.bashrc...${NC}"
if [ -f ~/.bashrc ]; then
  # Create backup
  cp ~/.bashrc ~/.bashrc.bak.$(date +%Y%m%d%H%M%S)
  echo "Created backup of ~/.bashrc"
  
  # Remove old aliases
  sed -i.tmp '/alias ask=.*/d' ~/.bashrc
  sed -i.tmp '/alias askp=.*/d' ~/.bashrc
  
  # Remove duplicate PATH entries
  sed -i.tmp '/# ASKD PATH/d' ~/.bashrc
  sed -i.tmp '/# ASKP PATH/d' ~/.bashrc
  sed -i.tmp '/# ASKP PATH Priority/d' ~/.bashrc
  sed -i.tmp '/Added by ASKP complete fix script/d' ~/.bashrc
  sed -i.tmp '/export PATH=".*\.local\/bin.*"/d' ~/.bashrc
  
  # Add correct PATH entry
  echo -e "\n# ASKP Configuration" >> ~/.bashrc
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  
  echo "Cleaned up ~/.bashrc"
  rm -f ~/.bashrc.tmp
fi

# Clean up zshrc
echo -e "\n${GREEN}Cleaning up ~/.zshrc...${NC}"
if [ -f ~/.zshrc ]; then
  # Create backup
  cp ~/.zshrc ~/.zshrc.bak.$(date +%Y%m%d%H%M%S)
  echo "Created backup of ~/.zshrc"
  
  # Remove old aliases
  sed -i.tmp '/alias ask=.*/d' ~/.zshrc
  sed -i.tmp '/alias askp=.*/d' ~/.zshrc
  
  # Remove duplicate PATH entries
  sed -i.tmp '/# ASKD PATH/d' ~/.zshrc
  sed -i.tmp '/# ASKP PATH/d' ~/.zshrc
  sed -i.tmp '/# ASKP PATH Priority/d' ~/.zshrc
  sed -i.tmp '/Added by ASKP complete fix script/d' ~/.zshrc
  sed -i.tmp '/export PATH=".*\.local\/bin.*"/d' ~/.zshrc
  
  # Add correct PATH entry
  echo -e "\n# ASKP Configuration" >> ~/.zshrc
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
  
  echo "Cleaned up ~/.zshrc"
  rm -f ~/.zshrc.tmp
fi

# Check for profile files
echo -e "\n${GREEN}Checking ~/.profile and ~/.bash_profile...${NC}"
for profile in ~/.profile ~/.bash_profile; do
  if [ -f "$profile" ]; then
    cp "$profile" "$profile.bak.$(date +%Y%m%d%H%M%S)"
    echo "Created backup of $profile"
    
    # Remove duplicate PATH entries
    sed -i.tmp '/# ASKD PATH/d' "$profile"
    sed -i.tmp '/# ASKP PATH/d' "$profile"
    sed -i.tmp '/# ASKP PATH Priority/d' "$profile"
    sed -i.tmp '/Added by ASKP complete fix script/d' "$profile"
    sed -i.tmp '/export PATH=".*\.local\/bin.*"/d' "$profile"
    
    echo "Cleaned up $profile"
    rm -f "$profile.tmp"
  fi
done

# Ensure symlinks are correct
echo -e "\n${GREEN}Ensuring correct symlinks...${NC}"
mkdir -p ~/.local/bin
# Remove old symlinks first
rm -f ~/.local/bin/askp ~/.local/bin/ask

# Create new symlinks only if the target exists
if [ -f ~/.askp/env/bin/askp ]; then
  ln -sf ~/.askp/env/bin/askp ~/.local/bin/askp
  echo "Created symlink for askp in ~/.local/bin"
fi

if [ -f ~/.askp/env/bin/ask ]; then
  ln -sf ~/.askp/env/bin/ask ~/.local/bin/ask
  echo "Created symlink for ask in ~/.local/bin"
fi

# Check for old environment
echo -e "\n${GREEN}Checking for old ASKD environment...${NC}"
if [ -d ~/.askd/env/bin ]; then
  echo -e "${YELLOW}Old ASKD environment found at ~/.askd/env${NC}"
  echo "Consider removing it to prevent conflicts:"
  echo "  rm -rf ~/.askd/env"
fi

echo -e "\n${YELLOW}IMPORTANT:${NC} Please restart your shell or run:"
echo "  source ~/.bashrc  # If using bash"
echo "  source ~/.zshrc   # If using zsh"
echo -e "\nThen try running 'askp' or 'ask' again"
