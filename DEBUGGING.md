# BioBeamer Debugging Guide

This guide explains how to debug BioBeamer issues on production machines using the exact same environment where errors occurred.

## Quick Start

### 1. Get Debug Information

Run the launcher with the `--debug` flag on the machine where the error occurred:

```bash
# If config is in default location
python -m biobeamer_launcher.launcher --debug

# If config is in custom location
python -m biobeamer_launcher.launcher --config /path/to/launcher.ini --debug
```

This will:
- ✅ Download/update the BioBeamer repository
- ✅ Create the version-specific virtual environment
- ✅ Install BioBeamer into the venv
- ✅ Print all paths and arguments needed for debugging

### 2. Copy the Output

The debug command will output something like:

```
============================================================
BIOBEAMER DEBUG INFO
============================================================
BioBeamer repo path:     /home/user/.cache/biobeamer_launcher/BioBeamer
BioBeamer venv path:     /home/user/.cache/biobeamer_launcher/BioBeamer-venv-v1.0.0
BioBeamer version:       v1.0.0
Python interpreter:      /home/user/.cache/biobeamer_launcher/BioBeamer-venv-v1.0.0/bin/python
XML config path:         /tmp/tmpXXXXXX.xml
Host name:               production_host

EXACT COMMAND ARGUMENTS (copy-paste ready):
==================================================
--xml "/tmp/tmpXXXXXX.xml" --hostname "production_host" --log_dir "/var/log/biobeamer" --password ""
```

## Debugging Methods

### Method 1: IDE Debugging (Recommended)

#### PyCharm Setup
1. **Open Project**: `File → Open` → Select the **BioBeamer repo path** from debug output
2. **Set Interpreter**: 
   - `File → Settings → Project → Python Interpreter`
   - `Add Interpreter → Existing Environment`
   - Path: Use the **Python interpreter** path from debug output
3. **Create Run Configuration**:
   - `Run → Edit Configurations → Add → Python`
   - **Script path**: Leave blank (uses entry point)
   - **Module name**: `biobeamer`
   - **Parameters**: Copy the **exact command arguments** from debug output
   - **Working directory**: Set to the **BioBeamer repo path**

#### VS Code Setup
1. **Open Folder**: `File → Open Folder` → Select the **BioBeamer repo path**
2. **Select Interpreter**: 
   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Choose: **Python interpreter** path from debug output
3. **Create Launch Configuration** (`.vscode/launch.json`):
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug BioBeamer",
            "type": "python",
            "request": "launch",
            "module": "biobeamer",
            "args": [
                "--xml", "/tmp/tmpXXXXXX.xml",
                "--hostname", "production_host", 
                "--log_dir", "/var/log/biobeamer",
                "--password", ""
            ],
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal"
        }
    ]
}
```

### Method 2: Command Line Debugging

#### Direct Execution
```bash
# Activate the venv
source /path/to/BioBeamer-venv-version/bin/activate

# Run with same arguments (copy from debug output)
biobeamer --xml "/tmp/config.xml" --hostname "host" --log_dir "/logs" --password ""
```

#### Python Debugger (pdb)
```bash
# Activate venv first
source /path/to/BioBeamer-venv-version/bin/activate

# Run with pdb
python -m pdb $(which biobeamer) --xml "/tmp/config.xml" --hostname "host" --log_dir "/logs"
```

#### With Additional Debug Output
```bash
# Enable Python debug logging
export PYTHONPATH="/path/to/BioBeamer"
export BIOBEAMER_DEBUG=1
biobeamer --xml "/tmp/config.xml" --hostname "host" --log_dir "/logs" --password ""
```

## Debugging Workflow

### 1. Reproduce the Error
- Use the exact same arguments from the debug output
- Run in the same environment (same venv, same code version)
- Check if the error reproduces consistently

### 2. Identify the Problem
- Set breakpoints in suspected areas
- Step through the code execution
- Examine variable states at the point of failure
- Check file permissions, network connectivity, etc.

### 3. Common Debugging Points
- **File operations**: Check if source/destination paths exist and are accessible
- **Network operations**: Verify SSH connections, credentials, timeouts
- **Configuration parsing**: Ensure XML config is valid and contains expected values
- **Process execution**: Check if external commands (scp, robocopy) are available

### 4. Log Analysis
- Check the launcher logs for the exact command that was executed
- Review BioBeamer subprocess logs for detailed error messages
- Look for patterns in failed vs successful runs

## Troubleshooting

### Common Issues

#### Config File Not Found
```bash
# Specify config explicitly
python -m biobeamer_launcher.launcher --config /full/path/to/launcher.ini --debug
```

#### Permission Issues
```bash
# Check file permissions
ls -la /path/to/files
# Check directory permissions  
ls -la /path/to/directory/
```

#### Git Repository Issues
```bash
# Clean up corrupted cache
rm -rf ~/.cache/biobeamer_launcher/
# Re-run debug command
```

#### Virtual Environment Issues
```bash
# Remove specific venv
rm -rf ~/.cache/biobeamer_launcher/BioBeamer-venv-version/
# Re-run debug command to recreate
```

### Environment Variables

Useful environment variables for debugging:

```bash
# Override cache directory
export BIOBEAMER_LAUNCHER_CACHE_DIR="/custom/cache/path"

# Override config file
export BIOBEAMER_LAUNCHER_CONFIG="/custom/config.ini"

# Use custom uv executable
export UV_PATH="/custom/path/to/uv"

# Python debug mode
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
```

## Advanced Debugging

### Memory Profiling
```bash
pip install memory-profiler
python -m memory_profiler $(which biobeamer) --xml config.xml --hostname host
```

### Performance Profiling  
```bash
python -m cProfile -o biobeamer.prof $(which biobeamer) --xml config.xml --hostname host
python -c "import pstats; pstats.Stats('biobeamer.prof').sort_stats('cumulative').print_stats()"
```

### Network Debugging
```bash
# Enable SSH debug output
export BIOBEAMER_SSH_DEBUG=1

# Monitor network traffic
sudo tcpdump -i any host target_host

# Test connectivity manually
ssh -v user@target_host
scp -v test_file user@target_host:/tmp/
```

## Support

If you're still having issues:

1. **Collect Information**:
   - Debug output from `--debug` command
   - Full error messages and stack traces
   - Launcher and subprocess log files
   - System information (OS, Python version, etc.)

2. **Create Minimal Reproduction**:
   - Identify the smallest set of files/conditions that trigger the issue
   - Document exact steps to reproduce

3. **Check Recent Changes**:
   - Has the configuration changed recently?
   - Are there new BioBeamer versions being used?
   - Have system dependencies been updated?

Remember: The debug setup gives you the **exact same environment** where the error occurred, making debugging much more reliable than trying to reproduce issues in different environments.
