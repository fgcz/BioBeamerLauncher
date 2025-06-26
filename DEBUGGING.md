# BioBeamer Debugging Guide

## Quick Start

1. **Get debug info**: `python -m biobeamer_launcher.launcher --debug`
2. **Copy the paths and arguments** from the output
3. **Open the BioBeamer repo path** in your IDE
4. **Set the venv Python interpreter** from the debug output
5. **Debug using one of the methods below**

## PyCharm Debugging (Easiest)

1. **Open Project**: Select the **BioBeamer repo path** from debug output
2. **Set Interpreter**: `File → Settings → Project → Python Interpreter → Add Interpreter → Existing Environment` → Use **Python interpreter path** from debug output
3. **Quick Debug**:
   - Right-click `src/biobeamer/__main__.py` → "Debug '__main__'"
   - Edit the auto-created run configuration to add your **command arguments** from debug output
   - Set breakpoints in `src/biobeamer/` files and debug normally

## VS Code Debugging

1. **Open Folder**: Select the **BioBeamer repo path**
2. **Select Interpreter**: `Ctrl+Shift+P` → "Python: Select Interpreter" → Choose the **Python interpreter path** from debug output
3. **Create `.vscode/launch.json`**:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug BioBeamer",
            "type": "python",
            "request": "launch",
            "module": "biobeamer",
            "args": ["--xml", "/tmp/config.xml", "--hostname", "host", "--log_dir", "log"],
            "cwd": "${workspaceFolder}",
            "env": {"PYTHONPATH": "${workspaceFolder}/src"}
        }
    ]
}
```

## Command Line Debugging

```bash
# Activate the venv and run directly
source /path/to/BioBeamer-venv-version/bin/activate
biobeamer --xml "/tmp/config.xml" --hostname "host" --log_dir "/logs"

# Or with Python debugger
python -m pdb $(which biobeamer) --xml "/tmp/config.xml" --hostname "host"
```

## Troubleshooting

**Import Errors**: Right-click `src` folder → "Mark Directory as" → "Sources Root" in PyCharm

**Missing __main__.py**: Create `/path/to/BioBeamer/src/biobeamer/__main__.py`:
```python
from biobeamer.cli import main
if __name__ == "__main__":
    main()
```

**Cache Issues**: `rm -rf ~/.cache/biobeamer_launcher/` and re-run debug command

## Debug Startup Scripts

The existing startup scripts now support passing arguments directly:

**Windows:**
```bat
start.bat --debug
```

**Linux/macOS:**
```bash
./start.sh --debug
```

This will run the launcher with the `--debug` flag, which will:
- Set up the BioBeamer environment 
- Print all the debug information you need
- Not actually run BioBeamer, just show the paths and arguments for IDE debugging
