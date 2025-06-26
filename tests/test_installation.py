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
    # Run the setup script from the project root so venv is created in the right place
    result = subprocess.run(
        ["bash", SETUP_SCRIPT], capture_output=True, text=True, cwd=PROJECT_ROOT
    )
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
    
    # Test the actual release package, not the development script
    build_dir = os.path.join(PROJECT_ROOT, "build")
    release_dir = os.path.join(build_dir, "release-linux")
    start_script = os.path.join(release_dir, "start.sh")
    setup_script = os.path.join(release_dir, "setup.sh")
    
    # Create release package if it doesn't exist
    if not os.path.exists(start_script):
        # Run make_release.py to create the release package
        make_release_script = os.path.join(PROJECT_ROOT, "make_release.py")
        result = subprocess.run(
            [sys.executable, make_release_script], 
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        assert result.returncode == 0, f"Failed to create release package: {result.stderr}"
    
    assert os.path.exists(start_script), f"start.sh not found in release package: {start_script}"
    assert os.path.exists(setup_script), f"setup.sh not found in release package: {setup_script}"
    
    # First run setup.sh in the release directory to create the virtual environment
    release_venv = os.path.join(release_dir, "biobeamer-launcher-venv")
    if os.path.exists(release_venv):
        shutil.rmtree(release_venv)
    
    setup_result = subprocess.run(
        ["bash", setup_script], capture_output=True, text=True, cwd=release_dir
    )
    print("Setup output:", setup_result.stdout)
    print("Setup errors:", setup_result.stderr)
    assert setup_result.returncode == 0, f"Release setup.sh failed: {setup_result.stderr}"
    assert os.path.isdir(release_venv), "Release virtual environment was not created."
    
    # Now test that start.sh works (but expect it to fail gracefully since we don't have a config server)
    result = subprocess.run(
        ["bash", start_script], capture_output=True, text=True, cwd=release_dir, timeout=10
    )
    print("Start output:", result.stdout)
    print("Start errors:", result.stderr)
    # start.sh might fail due to missing config server, but it should at least try to run
    # We just check that the venv activation worked (no "No such file or directory" error)
    assert "No such file or directory" not in result.stderr, f"start.sh failed to find venv: {result.stderr}"
    
    # Additional check: Verify that when BioBeamer is eventually installed, the entry point is created
    # This tests our fix for the "BioBeamer entry point not found" issue
    assert "BioBeamer entry point not found" not in result.stderr, f"BioBeamer entry point not created properly: {result.stderr}"


@pytest.mark.order(6)
def test_start_bat_runs():
    if platform.system() != "Windows":
        pytest.skip("start.bat test only runs on Windows")
    assert os.path.isdir(VENV_SCRIPTS), "Venv Scripts dir not found for start.bat test"
    
    # Test the actual release package, not the development script
    build_dir = os.path.join(PROJECT_ROOT, "build")
    release_dir = os.path.join(build_dir, "release-win")
    start_bat = os.path.join(release_dir, "start.bat")
    setup_bat = os.path.join(release_dir, "setup.bat")
    
    # Create release package if it doesn't exist
    if not os.path.exists(start_bat):
        # Run make_release.py to create the release package
        make_release_script = os.path.join(PROJECT_ROOT, "make_release.py")
        result = subprocess.run(
            [sys.executable, make_release_script], 
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        assert result.returncode == 0, f"Failed to create release package: {result.stderr}"
    
    assert os.path.exists(start_bat), f"start.bat not found in release package: {start_bat}"
    assert os.path.exists(setup_bat), f"setup.bat not found in release package: {setup_bat}"
    
    # First run setup.bat in the release directory to create the virtual environment
    release_venv = os.path.join(release_dir, "biobeamer-launcher-venv")
    if os.path.exists(release_venv):
        shutil.rmtree(release_venv)
    
    setup_result = subprocess.run(
        ["cmd.exe", "/c", setup_bat], capture_output=True, text=True, cwd=release_dir
    )
    print("Setup output:", setup_result.stdout)
    print("Setup errors:", setup_result.stderr)
    assert setup_result.returncode == 0, f"Release setup.bat failed: {setup_result.stderr}"
    assert os.path.isdir(release_venv), "Release virtual environment was not created."
    
    # Now test that start.bat works (but expect it to fail gracefully since we don't have a config server)
    result = subprocess.run(
        ["cmd.exe", "/c", start_bat], capture_output=True, text=True, cwd=release_dir, timeout=10
    )
    print("Start output:", result.stdout)
    print("Start errors:", result.stderr)
    # start.bat might fail due to missing config server, but it should at least try to run
    # We just check that the venv activation worked (no "The system cannot find the path" error)
    assert "The system cannot find the path" not in result.stderr, f"start.bat failed to find venv: {result.stderr}"
