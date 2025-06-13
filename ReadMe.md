# BioBeamerLauncher

BioBeamerLauncher is a cross-platform launcher for BioBeamer. It fetches a configuration file from a public git repository, determines the correct BioBeamer version to use, and runs BioBeamer with the specified configuration.

---

## Quick Start (Recommended for Most Users)

### 1. Download and Extract
- Download the release package (zip or tar.gz) for your platform.
- Extract it to a folder of your choice.

### 2. Install (One-Time Setup)
- **Windows:** Double-click or run `setup.bat`.
- **Linux/macOS:** Run `bash setup.sh` in a terminal.

This will:
- Set up a Python environment using the included `uv` tool
- Download and install the BioBeamer Launcher from GitHub

### 3. Start the Launcher
- **Windows:** Double-click or run `start.bat`.
- **Linux/macOS:** Run `bash start.sh` in a terminal.

This will:
- Activate the environment
- Start the BioBeamer Launcher using the default configuration (`config/launcher.ini`)

---

## Requirements
- **Git** must be installed and available in your system PATH.
- **Internet access** is required to fetch configuration files and repositories.
- No need to pre-install Python or pip; the setup script will handle this automatically using `uv`.
- **robocopy** (Windows) and/or **scp/ssh** (Linux/Unix) must be installed and available in your system PATH for file transfer operations and integration tests.
- If you want to use **scp** for remote transfers, you must set up passwordless SSH access (e.g., using SSH keys) to the remote host in advance. The target path in the XML config must be in the format `host:/path` (or `user@host:/path` if a username is needed).

---

## Updating
To update to the latest version, simply re-run `setup.bat` or `setup.sh`.

---

## Troubleshooting
- The first run may take a few minutes as dependencies are downloaded.
- Make sure you have an internet connection for the initial setup.
- If you encounter issues, check the log files in the `log/` directory.
- For advanced users, you can activate the environment manually:
  - **Windows:** `call biobeamer-launcher-venv\Scripts\activate.bat`
  - **Linux/macOS:** `source biobeamer-launcher-venv/bin/activate`
- If you need to use a different configuration file, edit `start.sh` or `start.bat` and change the path after `--config`.

---

## Developer & Advanced Usage

### Manual Installation
If you want to install the launcher and its dependencies manually (e.g., for development):

```sh
pip install .
```

To install with optional test dependencies (for running tests):

```sh
pip install .[test]
```

### Testing
To run the test suite, make sure you have installed the test dependencies as above, then run:

```sh
pytest
```

Or, to run a specific test file:

```sh
pytest tests/test_launcher_real_integration.py
```

You can also use unittest if you have tests written for it:

```sh
python -m unittest discover
```

### Directory Structure
- `pyproject.toml` — Project metadata and dependencies
- `src/biobeamer_launcher/launcher.py` — Main launcher script

### Usage (Development)
1. Clone this repository:
   ```sh
   git clone https://github.com/fgcz/BioBeamerLauncher.git
   cd BioBeamerLauncher
   ```
2. Run the launcher:
   ```sh
   python src/biobeamer_launcher/launcher.py
   ```

---

## Workflow
1. User runs the launcher
2. Launcher fetches config from git
3. Launcher ensures correct BioBeamer version is present
4. Launcher runs BioBeamer

---
For more details, see the source code and comments in `src/biobeamer_launcher/launcher.py`.

## License
See LICENSE file for details.
