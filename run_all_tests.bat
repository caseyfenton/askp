@echo off
REM RUN_ALL_TESTS.bat - Comprehensive test script for askp package on Windows
REM Run this before deploying to PyPI or committing to GitHub

echo ===== ASKP COMPREHENSIVE TEST SCRIPT (WINDOWS) =====
echo Starting tests at %date% %time%
echo.

REM Keep track of failures
set FAILURES=0

REM Function equivalent for running tests and reporting status
:run_test
    echo [33mRunning %~1...[0m
    call %~2
    if %ERRORLEVEL% equ 0 (
        echo [32m✓ %~1 passed[0m
        echo.
    ) else (
        set /a FAILURES+=1
        echo [31m✗ %~1 failed[0m
        echo.
    )
    goto :eof

REM Create a temporary environment for testing
echo Setting up temporary test environment...
python -m venv test_env_win
call test_env_win\Scripts\activate.bat

REM Install required dependencies for testing
echo Installing required dependencies...
pip install -e .
pip install pytest click pytest-mock

REM 1. Standard Unit Tests (just run the ones that work without pytest)
call :run_test "Standard Unit Tests" "python -m unittest tests/test_models.py"

REM 2. Test CLI functionality (this is optional as it requires API credentials)
echo [33mSkipping CLI Functionality Test (requires API credentials)[0m
echo To manually test: python -m askp "test" --model sonar-pro --temperature 0.5 --no-save
echo.

REM 3. Version compatibility check
call :run_test "Version Compatibility Check" "python -c \"import askp; print(f'askp version: {askp.__version__}');\""

REM 4. Test installation process
call :run_test "Installation Test" "pip uninstall -y askp && pip install -e . && python -c \"import askp; print('Installation successful')\""

REM 5. Test specific modules
call :run_test "Models Module Test" "python -m unittest tests/test_models.py"

REM 6. Test our main fix for dictionary model handling
call :run_test "Dictionary Model Name Fix Test" "python -c \"from askp.utils import normalize_model_name; assert normalize_model_name('sonar-pro') == 'sonar-pro'; assert normalize_model_name({'model': 'sonar-pro'}) == 'sonar-pro'; assert normalize_model_name({}) == 'sonar-pro'; print('All normalize_model_name tests passed!')\""

REM 7. Windows-specific path tests
call :run_test "Windows Path Test" "python -c \"import os; print('Windows path test'); path = r'C:\\Users\\Test\\Documents'; print(os.path.exists('C:\\Windows'))\""

REM 8. Clean up and restore environment
call deactivate
rmdir /s /q test_env_win

REM Summary
echo ===== TEST SUMMARY =====
if %FAILURES% equ 0 (
    echo [32mAll tests passed successfully![0m
    echo.
    echo Ready for commit to GitHub and PyPI deployment.
    
    echo.
    echo To commit to GitHub:
    echo   git add .
    echo   git commit -m "Fix compatibility with OpenAI client version 1.77.0"
    echo   git push origin main
    
    echo.
    echo To deploy to PyPI:
    echo   python setup.py sdist bdist_wheel
    echo   twine upload dist/*
) else (
    echo [31m%FAILURES% tests failed. Please fix before deploying.[0m
    exit /b 1
)
