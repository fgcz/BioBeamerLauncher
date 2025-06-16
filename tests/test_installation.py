import os
import subprocess
import shutil
import sys
import pytest
import platform

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
VENV_DIR = os.path.join(PROJECT_ROOT, "biobeamer-launcher-venv")
VENV_BIN = os.path.join(VENV_DIR, "bin")
VENV_SCRIPTS = os.path.join(VENV_DIR, "Scripts")
LAUNCHER_EXE = os.path.join(VENV_BIN, "biobeamer-launcher")
LAUNCHER_EXE_WIN = os.path.join(VENV_SCRIPTS, "biobeamer-launcher.exe")
SETUP_SCRIPT = os.path.join(SCRIPTS_DIR, "setup.sh")
SETUP_BAT = os.path.join(SCRIPTS_DIR, "setup.bat")


@pytest.mark.order(1)
def test_setup_script_runs():
    if platform.system() == "Windows":
        pytest.skip("Skipping setup.sh test on Windows")
    # Remove venv if it exists
    if os.path.exists(VENV_DIR):
        shutil.rmtree(VENV_DIR)
    assert os.path.exists(SETUP_SCRIPT), f"Setup script not found: {SETUP_SCRIPT}"
    # Run the setup script
    result = subprocess.run(["bash", SETUP_SCRIPT], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0, f"setup.sh failed: {result.stderr}"
    assert os.path.isdir(VENV_DIR), "Virtual environment was not created."


@pytest.mark.order(2)
def test_biobeamer_launcher_installed():
    if platform.system() == "Windows":
        pytest.skip("Skipping Linux launcher test on Windows")
    assert os.path.isdir(VENV_BIN), f"Venv bin dir not found: {VENV_BIN}"
    launcher_path = LAUNCHER_EXE
    assert os.path.isfile(
        launcher_path
    ), f"biobeamer-launcher not found in venv: {launcher_path}"
    result = subprocess.run([launcher_path, "--help"], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0, "biobeamer-launcher --help failed"
    assert (
        "usage" in result.stdout.lower() or "usage" in result.stderr.lower()
    ), "Help output not found"


@pytest.mark.order(3)
def test_setup_bat_runs():
    if platform.system() != "Windows":
        pytest.skip("setup.bat test only runs on Windows")
    # Remove venv if it exists
    if os.path.exists(VENV_DIR):
        shutil.rmtree(VENV_DIR)
    assert os.path.exists(SETUP_BAT), f"Setup.bat not found: {SETUP_BAT}"
    result = subprocess.run(
        ["cmd.exe", "/c", SETUP_BAT], capture_output=True, text=True
    )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0, f"setup.bat failed: {result.stderr}"
    assert os.path.isdir(VENV_DIR), "Virtual environment was not created by setup.bat."


@pytest.mark.order(4)
def test_biobeamer_launcher_installed_win():
    if platform.system() != "Windows":
        pytest.skip("Windows launcher test only runs on Windows")
    assert os.path.isdir(VENV_SCRIPTS), f"Venv Scripts dir not found: {VENV_SCRIPTS}"
    launcher_path = LAUNCHER_EXE_WIN
    assert os.path.isfile(
        launcher_path
    ), f"biobeamer-launcher.exe not found in venv: {launcher_path}"
    result = subprocess.run([launcher_path, "--help"], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0, "biobeamer-launcher.exe --help failed"
    assert (
        "usage" in result.stdout.lower() or "usage" in result.stderr.lower()
    ), "Help output not found"


@pytest.mark.order(5)
def test_start_script_runs():
    if platform.system() == "Windows":
        pytest.skip("Skipping start.sh test on Windows")
    assert os.path.isdir(VENV_BIN), "Venv bin dir not found for start.sh test"
    start_script = os.path.join(SCRIPTS_DIR, "start.sh")
    assert os.path.exists(start_script), f"start.sh not found: {start_script}"
    # Run the start.sh script from the project root so config/launcher.ini is found
    result = subprocess.run(
        ["bash", start_script], capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0, f"start.sh failed: {result.stderr}"


@pytest.mark.order(6)
def test_start_bat_runs():
    if platform.system() != "Windows":
        pytest.skip("start.bat test only runs on Windows")
    assert os.path.isdir(VENV_SCRIPTS), "Venv Scripts dir not found for start.bat test"
    start_bat = os.path.join(SCRIPTS_DIR, "start.bat")
    assert os.path.exists(start_bat), f"start.bat not found: {start_bat}"
    # Run the start.bat script from the project root so config\launcher.ini is found
    result = subprocess.run(
        ["cmd.exe", "/c", start_bat], capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0, f"start.bat failed: {result.stderr}"
