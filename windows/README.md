# ASKP Windows Helper Scripts

This directory contains specialized batch files to make ASKP installation and usage more reliable on Windows systems.

## Files

- **setup_askp.bat** - One-step installation and configuration script that:
  - Checks prerequisites (Python, Git)
  - Clones the ASKP repository
  - Creates and activates virtual environment
  - Handles PowerShell execution policy issues
  - Installs ASKP and dependencies
  - Configures your Perplexity API key

- **askp.bat** - Enhanced launcher that:
  - Automatically detects and uses your API key
  - Handles common errors with helpful messages
  - Makes it easy to find your results
  - Bypasses typical Windows permission issues

## Quick Start

1. **First-time setup**: 
   ```
   .\windows\setup_askp.bat
   ```

2. **Usage**:
   ```
   .\windows\askp.bat "Your question here"
   ```

## Troubleshooting

- If you encounter execution policy errors, run PowerShell as Administrator and execute:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```

- If your API key isn't working, you can update it by either:
  - Editing the `.env` file in the askp directory
  - Running setup_askp.bat again
  - Setting it directly: `set PERPLEXITY_API_KEY=your-key-here`
