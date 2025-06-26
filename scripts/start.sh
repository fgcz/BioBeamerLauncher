#!/usr/bin/env bash
set -e

# Get the directory where this script is located (release root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source biobeamer-launcher-venv/bin/activate
biobeamer-launcher --config "config/launcher.ini"

