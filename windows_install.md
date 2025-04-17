# ASKP Installation Guide for Windows

This guide will help you install ASKP (Ask Perplexity) on Windows systems.

## Prerequisites

- Python 3.8 or higher
- Git

## Installation Steps

### 1. Create Installation Directory

```powershell
# Create a scripts directory (if it doesn't exist)
mkdir scripts
cd scripts
```

### 2. Clone the Repository

```powershell
git clone https://github.com/caseyfenton/askp.git
cd askp
```

### 3. Create Virtual Environment

```powershell
python -m venv venv
```

### 4. Address PowerShell Execution Policy

Windows PowerShell has security restrictions that prevent scripts from running by default. You have two options:

#### Option A: Temporarily bypass the execution policy (recommended for most users)
Run this command in PowerShell (must be run as Administrator):
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

#### Option B: Change execution policy permanently
Run this command in PowerShell (must be run as Administrator):
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 5. Activate Virtual Environment

After addressing the execution policy:
```powershell
.\venv\Scripts\Activate.ps1
```

Alternatively, if you're using Command Prompt:
```cmd
.\venv\Scripts\activate.bat
```

### 6. Install ASKP

```powershell
pip install -e .
```

### 7. Configure API Key

There are two ways to set up your Perplexity API key:

#### Option A: Create a direct environment variable (Recommended)

In PowerShell, set the environment variable directly:
```powershell
$env:PERPLEXITY_API_KEY = "your_api_key_here"
```

This approach has been shown to work more reliably on Windows systems than the `.env` file approach.

#### Option B: Create a `.env` file

If you prefer using the `.env` file approach (though it may not work in all Windows configurations):
```powershell
# Using PowerShell
"PERPLEXITY_API_KEY=your_api_key_here" | Out-File .env -Encoding utf8

# Or using Command Prompt
echo PERPLEXITY_API_KEY=your_api_key_here > .env
```

Replace `your_api_key_here` with your actual Perplexity API key.

### 8. Create Convenience Scripts

Create two batch files for easier use:

#### Basic batch file
```powershell
# Using PowerShell
@"
@echo off
cd %~dp0
call venv\Scripts\activate.bat
python -m askp %*
"@ | Out-File -FilePath ..\ask.bat -Encoding ASCII
```

#### Recommended batch file with API key included
```powershell
# Using PowerShell
@"
@echo off
cd %~dp0
call venv\Scripts\activate.bat
set PERPLEXITY_API_KEY=your_api_key_here
python -m askp %*
"@ | Out-File -FilePath ..\askp_with_key.bat -Encoding ASCII
```

Make sure to replace `your_api_key_here` with your actual Perplexity API key in the second batch file.

## Usage

To use ASKP:

```
cd scripts
.\askp_with_key.bat "Your question here"
```

For example:
```
.\askp_with_key.bat "What is quantum computing?"
```

### Alternative usage (requires setting environment variable first)

```powershell
$env:PERPLEXITY_API_KEY = "your_api_key_here"
.\ask.bat "Your question here"
```

## Troubleshooting

### Unable to Run Scripts
If you see errors about scripts being disabled, follow the instructions in Step 4 to address PowerShell execution policy.

### API Key Errors
If you see `401 Authorization Required` errors:
1. Make sure you've created the `.env` file correctly
2. Verify your API key is valid
3. Ensure the key is entered correctly without extra spaces or quotes

### Path Issues
If you get errors about files not found:
1. Make sure you're in the correct directory
2. Use absolute paths if necessary
3. Double-check that all installation steps were completed successfully
