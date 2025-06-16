#!/usr/bin/env bash
set -e

# Always run from project root (parent of this script's directory)
cd "$(dirname "$0")/.."

# Find uv: prefer ./uv if executable, else use uv from PATH
if [ -x "./scripts/uv" ]; then
    UV_CMD="./scripts/uv"
elif command -v uv >/dev/null 2>&1; then
    UV_CMD="uv"
else
    echo "Error: 'uv' not found in ./scripts/uv or in PATH. Please install uv."
    exit 127
fi

# Create a virtual environment with uv (downloads Python if needed)
$UV_CMD venv biobeamer-launcher-venv

# Activate the environment
source biobeamer-launcher-venv/bin/activate

# Install your launcher and dependencies from GitHub
$UV_CMD pip install "git+https://github.com/fgcz/BioBeamerLauncher.git"

# Optionally, force reinstall the CLI tool from GitHub
$UV_CMD pip install --force-reinstall --no-deps "git+https://github.com/fgcz/BioBeamerLauncher.git"

echo "BioBeamer Launcher setup complete."
echo "Activate with: source biobeamer-launcher-venv/bin/activate"
echo "Run with: biobeamer-launcher --help"
