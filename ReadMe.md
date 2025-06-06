# BioBeamerLauncher

BioBeamerLauncher is a cross-platform launcher for BioBeamer. It fetches a configuration file from a public git repository, determines the correct BioBeamer version to use, and runs BioBeamer with the specified configuration.

## Features
- Fetches config file (e.g., XML) from a public git repo
- Reads config to determine BioBeamer version and parameters
- Downloads or updates the specified BioBeamer version
- Launches BioBeamer with the config

## Requirements
- **Git** must be installed and available in your system PATH.
- **Internet access** is required to fetch configuration files and repositories.
- **Python 3.8+** must be installed. You can install all Python dependencies using the provided `pyproject.toml`.
- **robocopy** (Windows) and/or **scp/ssh** (Linux/Unix) must be installed and available in your system PATH for file transfer operations and integration tests.

## Installation
To install the launcher and its dependencies, run:

```sh
pip install .
```

To install with optional test dependencies (for running tests):

```sh
pip install .[test]
```

## Testing
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

## Directory Structure
- `pyproject.toml` — Project metadata and dependencies
- `launcher.py` — Main launcher script

## Usage
1. Clone this repository:
   ```sh
   git clone <this-repo-url>
   cd BioBeamerLauncher
   ```
2. Run the launcher:
   ```sh
   python launcher.py
   ```
   (Or package as an executable for systems without Python.)

## Workflow
1. User runs the launcher
2. Launcher fetches config from git
3. Launcher ensures correct BioBeamer version is present
4. Launcher runs BioBeamer

---
For more details, see the source code and comments in `launcher.py`.
