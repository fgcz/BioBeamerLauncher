#!/usr/bin/env bash
set -e

# Always run from project root (parent of this script's directory) - same as setup.sh
cd "$(dirname "$0")/.."

source biobeamer-launcher-venv/bin/activate
biobeamer-launcher --config config/launcher.ini

