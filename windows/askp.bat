@echo off
setlocal enabledelayedexpansion

:: ASKP Windows Launcher
:: This script handles environment setup and common errors for Windows users

echo *************************************
echo * ASKP - Perplexity Search Utility  *
echo *************************************

:: Set script directory as base path
set "SCRIPT_DIR=%~dp0"
set "ASKP_DIR=%SCRIPT_DIR%..\scripts\askp"
set "RESULTS_DIR=%ASKP_DIR%\perplexity_results"

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8 or higher.
    exit /b 1
)

:: Check for the venv
if not exist "%ASKP_DIR%\venv" (
    echo [ERROR] Virtual environment not found. 
    echo Please run the setup script first: setup_askp.bat
    exit /b 1
)

:: Check for API key
if not defined PERPLEXITY_API_KEY (
    :: Try to read from .env file
    if exist "%ASKP_DIR%\.env" (
        for /f "tokens=1,* delims==" %%a in ('type "%ASKP_DIR%\.env"') do (
            if "%%a" == "PERPLEXITY_API_KEY" (
                set "PERPLEXITY_API_KEY=%%b"
            )
        )
    )
    
    :: If still not defined, prompt user
    if not defined PERPLEXITY_API_KEY (
        echo [WARNING] Perplexity API key not found.
        echo Enter your Perplexity API key (should start with 'pplx-'):
        set /p PERPLEXITY_API_KEY="> "
        
        :: Save to .env file for future use
        echo PERPLEXITY_API_KEY=!PERPLEXITY_API_KEY!> "%ASKP_DIR%\.env"
    )
)

:: Activate virtual environment and run ASKP
call "%ASKP_DIR%\venv\Scripts\activate.bat"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    echo This might be due to PowerShell execution policy restrictions.
    echo.
    echo Try running this in PowerShell as administrator:
    echo Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    exit /b 1
)

:: Run ASKP with all arguments
python -m askp %*
set EXIT_CODE=%ERRORLEVEL%

:: Create helpful message about results
if %EXIT_CODE% equ 0 (
    if exist "%RESULTS_DIR%" (
        echo.
        echo Results saved to: %RESULTS_DIR%
        for /f "delims=" %%i in ('dir /b /od /a-d "%RESULTS_DIR%\*.md" 2^>nul') do set "LATEST_FILE=%%i"
        if defined LATEST_FILE (
            echo Latest result: %LATEST_FILE%
            echo To view: notepad "%RESULTS_DIR%\%LATEST_FILE%"
        )
    )
)

exit /b %EXIT_CODE%
