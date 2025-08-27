#!/usr/bin/env bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine if we're in development mode (script in scripts/) or release mode (script in root)
if [ "$(basename "$SCRIPT_DIR")" = "scripts" ]; then
    # Development mode: go to project root (parent of scripts/)
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    cd "$PROJECT_ROOT"
    VENV_PATH="biobeamer-launcher-venv/bin/activate"
    CONFIG_PATH="config/launcher.ini"
else
    # Release mode: stay in script directory (which is the release root)
    cd "$SCRIPT_DIR"
    VENV_PATH="biobeamer-launcher-venv/bin/activate"
    CONFIG_PATH="config/launcher.ini"
    # Set UV_PATH to point to our bundled uv
    export UV_PATH="$SCRIPT_DIR/bin/uv"
fi

source "$VENV_PATH"
biobeamer-launcher --config "$CONFIG_PATH" "$@"

