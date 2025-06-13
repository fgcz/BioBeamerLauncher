@echo off
setlocal

REM Use bundled uv.exe in the current directory

REM Create virtual environment with uv (downloads Python if needed)
uv.exe venv biobeamer-launcher-venv
if errorlevel 1 (
    echo Failed to create virtual environment with uv.
    exit /b 1
)

REM Activate the environment
call biobeamer-launcher-venv\Scripts\activate.bat

REM Install your launcher and dependencies from GitHub
uv.exe pip install "git+https://github.com/fgcz/BioBeamerLauncher.git"

REM Optionally, force reinstall the CLI tool from GitHub
uv.exe pip install --force-reinstall --no-deps "git+https://github.com/fgcz/BioBeamerLauncher.git"

echo BioBeamer Launcher setup complete.
echo Activate with: call biobeamer-launcher-venv\Scripts\activate.bat
echo Run with: biobeamer-launcher --help

endlocal
