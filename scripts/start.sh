#!/usr/bin/env bash
set -e

# Get the directory where this script is located (release root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set UV_PATH to point to our bundled uv
export UV_PATH="$SCRIPT_DIR/bin/uv"

source biobeamer-launcher-venv/bin/activate
biobeamer-launcher --config "config/launcher.ini"

