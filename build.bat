@echo off
rem Build File Comparator as a single-file, windowless Windows executable with PyInstaller.
rem
rem Usage: build.bat [--skip-tests]
rem
rem Runs the unit tests, then builds dist\windows\Comparator.exe.
rem Set PYTHON to choose the interpreter, e.g.  set PYTHON=.venv\Scripts\python.exe
rem On Linux or macOS, use build.sh instead.

setlocal
cd /d "%~dp0"

set RUN_TESTS=1
if /i "%~1"=="--skip-tests" set RUN_TESTS=0
if not "%~1"=="" if "%RUN_TESTS%"=="1" (
    echo Unknown option: %~1 ^(usage: build.bat [--skip-tests]^)
    exit /b 1
)

if not defined PYTHON set PYTHON=python
"%PYTHON%" -c "import sys" >nul 2>&1
if errorlevel 1 (
    echo Python was not found. Install Python 3 or set PYTHON.
    exit /b 1
)
"%PYTHON%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller is not installed for %PYTHON%. Install it with: "%PYTHON%" -m pip install pyinstaller
    exit /b 1
)

if "%RUN_TESTS%"=="1" (
    echo Running tests...
    "%PYTHON%" -m unittest
    if errorlevel 1 (
        echo Tests failed, not building.
        exit /b 1
    )
)

echo Building windows executable...
rem The icon path must be absolute: PyInstaller resolves relative ones against the .spec folder
"%PYTHON%" -m PyInstaller Comparator.py ^
    --onefile ^
    --noconsole ^
    --clean ^
    --noconfirm ^
    --name Comparator ^
    --icon "%~dp0a.ico" ^
    --distpath dist\windows ^
    --workpath build\windows ^
    --specpath build\windows
if errorlevel 1 exit /b 1

echo Built dist\windows\Comparator.exe
