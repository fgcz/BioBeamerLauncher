@echo off

REM Always run from project root (parent of this script's directory) - same as setup.bat
cd /d "%~dp0\.."

call biobeamer-launcher-venv\Scripts\activate.bat
REM Config is in the release subdirectory
for %%I in ("%~dp0.") do set "RELEASE_DIR=%%~nxI"
biobeamer-launcher --config "%RELEASE_DIR%\config\launcher.ini"


