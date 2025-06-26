@echo off
setlocal

REM Get the directory where this script is located (release root)
cd /d "%~dp0"

REM Find uv.exe: prefer .\bin\uv.exe (release), else .\scripts\uv.exe (dev), else uv.exe from PATH
if exist ".\bin\uv.exe" (
    set "UV_CMD=.\bin\uv.exe"
) else if exist ".\scripts\uv.exe" (
    set "UV_CMD=.\scripts\uv.exe"
) else (
    where uv.exe >nul 2>nul
    if %errorlevel%==0 (
        set "UV_CMD=uv.exe"
    ) else (
        echo Error: 'uv.exe' not found in .\bin\uv.exe, .\scripts\uv.exe, or in PATH. Please install uv.
        exit /b 127
    )
)

REM Create virtual environment with uv (downloads Python if needed)
%UV_CMD% venv biobeamer-launcher-venv
if errorlevel 1 (
    echo Failed to create virtual environment with uv.
    exit /b 1
)

REM Activate the environment
call biobeamer-launcher-venv\Scripts\activate.bat

REM Install your launcher and dependencies from GitHub
%UV_CMD% pip install "git+https://github.com/fgcz/BioBeamerLauncher.git"

REM Optionally, force reinstall the CLI tool from GitHub
%UV_CMD% pip install --force-reinstall --no-deps "git+https://github.com/fgcz/BioBeamerLauncher.git"

echo BioBeamer Launcher setup complete.
echo Activate with: call biobeamer-launcher-venv\Scripts\activate.bat
echo Run with: biobeamer-launcher --help

endlocal
