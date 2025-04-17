# ASKP Windows Quick Start Guide

Having trouble with ASKP on Windows? This guide provides the fastest path to success.

## Prerequisites
- Python 3.8+ and Git installed
- A valid Perplexity API key

## Quick Installation

1. **Open PowerShell as Administrator** and clone the repository:
   ```powershell
   mkdir scripts
   cd scripts
   git clone https://github.com/caseyfenton/askp.git
   cd askp
   ```

2. **Bypass execution policy** for this session only:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

3. **Create and activate virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

4. **Install ASKP**:
   ```powershell
   pip install -e .
   ```

5. **Create a batch file with your API key**:
   ```powershell
   @"
   @echo off
   cd %~dp0
   call venv\Scripts\activate.bat
   set PERPLEXITY_API_KEY=your_api_key_here
   python -m askp %*
   "@ | Out-File -FilePath ..\askp_with_key.bat -Encoding ASCII
   ```
   
   Replace `your_api_key_here` with your actual Perplexity API key.

6. **Use ASKP**:
   ```powershell
   cd ..
   .\askp_with_key.bat "What is quantum computing?"
   ```

## Troubleshooting

### Script Execution Errors
If you see `...cannot be loaded because running scripts is disabled...`:
- Use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` before running commands

### API Authorization Errors
If you see `401 Authorization Required`:
- Verify your API key format (should start with "pplx-")
- Try setting the environment variable directly:
  ```powershell
  $env:PERPLEXITY_API_KEY = "your_api_key_here"
  ```

### File Path Issues
If results aren't found:
- Results are saved in `askp\perplexity_results` directory
- Use full paths when accessing result files

For more detailed instructions, see the full [Windows Installation Guide](windows_install.md).
