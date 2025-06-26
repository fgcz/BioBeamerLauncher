#!/usr/bin/env bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Always run from project root (parent of script directory) - same as setup.sh
cd "$(dirname "$SCRIPT_DIR")"

source biobeamer-launcher-venv/bin/activate
# Config is in the release subdirectory
RELEASE_DIR=$(basename "$SCRIPT_DIR")
biobeamer-launcher --config "$RELEASE_DIR/config/launcher.ini"

