@echo off

REM Get the directory where this script is located (release root)
cd /d "%~dp0"

REM Set UV_PATH to point to our bundled uv.exe
set "UV_PATH=%~dp0bin\uv.exe"

call biobeamer-launcher-venv\Scripts\activate.bat
biobeamer-launcher --config "config\launcher.ini"


