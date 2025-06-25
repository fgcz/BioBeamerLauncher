@echo off

REM Always run from project root (parent of this script's directory) - same as setup.bat
cd /d "%~dp0\.."

call biobeamer-launcher-venv\Scripts\activate.bat
biobeamer-launcher --config config\launcher.ini


