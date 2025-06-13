#!/usr/bin/env bash
set -e

# Use bundled uv in the current directory

# Create a virtual environment with uv (downloads Python if needed)
./uv venv biobeamer-launcher-venv

# Activate the environment
source biobeamer-launcher-venv/bin/activate

# Install your launcher and dependencies from GitHub
./uv pip install "git+https://github.com/fgcz/BioBeamerLauncher.git"

# Optionally, force reinstall the CLI tool from GitHub
./uv pip install --force-reinstall --no-deps "git+https://github.com/fgcz/BioBeamerLauncher.git"

echo "BioBeamer Launcher setup complete."
echo "Activate with: source biobeamer-launcher-venv/bin/activate"
echo "Run with: biobeamer-launcher --help"
