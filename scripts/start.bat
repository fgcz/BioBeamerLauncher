@echo off

REM Get the directory where this script is located (release root)
cd /d "%~dp0"

call biobeamer-launcher-venv\Scripts\activate.bat
biobeamer-launcher --config "config\launcher.ini"


