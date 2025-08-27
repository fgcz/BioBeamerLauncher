#!/usr/bin/env bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine if we're in development mode (script in scripts/) or release mode (script in root)
if [ "$(basename "$SCRIPT_DIR")" = "scripts" ]; then
    # Development mode: go to project root (parent of scripts/)
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    cd "$PROJECT_ROOT"
    echo "Development mode: Running from project root"
else
    # Release mode: stay in script directory (which is the release root)
    cd "$SCRIPT_DIR"
    echo "Release mode: Running from release directory"
fi


# Detect OS
OS=$(uname -s)

if [ "$OS" = "Darwin" ]; then
    # On macOS: prefer system uv
    if command -v uv >/dev/null 2>&1; then
        UV_CMD="uv"
    else
        echo "Error: 'uv' not found in PATH or ./scripts/uv. Please install uv."
        exit 127
    fi
else
    # On Linux/other: prefer release binary
    if [ -x "./bin/uv" ]; then
        UV_CMD="./bin/uv"
    elif [ -x "./scripts/uv" ]; then
        UV_CMD="./scripts/uv"
    elif command -v uv >/dev/null 2>&1; then
        UV_CMD="uv"
    else
        echo "Error: 'uv' not found in ./bin/uv, ./scripts/uv, or in PATH. Please install uv."
        exit 127
    fi
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
