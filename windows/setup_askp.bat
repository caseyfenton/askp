@echo off
setlocal enabledelayedexpansion

:: ASKP Windows Setup Script
:: Handles installation, virtual environment setup, and configuration

echo *************************************
echo * ASKP Windows Setup                *
echo *************************************

:: Set script directory as base path
set "SCRIPT_DIR=%~dp0"
set "ASKP_PARENT=%SCRIPT_DIR%..\scripts"
set "ASKP_DIR=%ASKP_PARENT%\askp"

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8 or higher.
    echo Visit: https://www.python.org/downloads/
    exit /b 1
)

:: Check if Git is installed
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git not found. Please install Git.
    echo Visit: https://git-scm.com/download/win
    exit /b 1
)

:: Create scripts directory if it doesn't exist
if not exist "%ASKP_PARENT%" (
    echo Creating scripts directory...
    mkdir "%ASKP_PARENT%"
)

:: Clone or update repository
if not exist "%ASKP_DIR%" (
    echo Cloning ASKP repository...
    cd "%ASKP_PARENT%"
    git clone https://github.com/caseyfenton/askp.git
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to clone repository.
        exit /b 1
    )
) else (
    echo ASKP repository already exists. Updating...
    cd "%ASKP_DIR%"
    git pull
)

:: Create virtual environment if it doesn't exist
if not exist "%ASKP_DIR%\venv" (
    echo Creating virtual environment...
    cd "%ASKP_DIR%"
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
)

:: Try to activate virtual environment
echo Activating virtual environment...
call "%ASKP_DIR%\venv\Scripts\activate.bat" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARNING] PowerShell script execution might be restricted.
    echo Attempting to bypass for this session...
    
    :: Create and run a temporary PowerShell script to bypass execution policy
    echo Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass > "%TEMP%\bypass_policy.ps1"
    echo . '%ASKP_DIR%\venv\Scripts\Activate.ps1' >> "%TEMP%\bypass_policy.ps1"
    powershell -ExecutionPolicy Bypass -File "%TEMP%\bypass_policy.ps1"
    
    :: Check if bypass worked
    if not defined VIRTUAL_ENV (
        echo [ERROR] Could not activate virtual environment.
        echo.
        echo Please run this in PowerShell as Administrator:
        echo Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
        echo.
        echo Then try running this setup script again.
        exit /b 1
    )
)

:: Install ASKP
echo Installing ASKP...
cd "%ASKP_DIR%"
pip install -e .
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install ASKP.
    exit /b 1
)

:: Configure API key
echo.
echo Setting up Perplexity API key...
echo.
echo Enter your Perplexity API key (should start with 'pplx-'):
echo If you don't have one, visit: https://www.perplexity.ai/settings/api
set /p PERPLEXITY_API_KEY="> "

:: Save API key to .env file
echo PERPLEXITY_API_KEY=%PERPLEXITY_API_KEY%> "%ASKP_DIR%\.env"

:: Also save as a Windows environment variable for the current user
setx PERPLEXITY_API_KEY "%PERPLEXITY_API_KEY%" >nul 2>nul
echo API key saved successfully.

:: Create results directory
if not exist "%ASKP_DIR%\perplexity_results" (
    mkdir "%ASKP_DIR%\perplexity_results"
)

echo.
echo *************************************
echo * ASKP installation complete!       *
echo *************************************
echo.
echo To use ASKP, run: askp.bat "Your question here"
echo.
echo Examples:
echo askp.bat "What is quantum computing?"
echo askp.bat -m "What is Python?" "What is TypeScript?"
echo.

exit /b 0
