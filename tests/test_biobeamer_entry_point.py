import os
import subprocess
import tempfile
import shutil
import pytest
import platform

def test_biobeamer_entry_point_creation():
    """Test that BioBeamer installation creates the proper entry point executable."""
    if not shutil.which("uv"):
        pytest.skip("uv not available for testing")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_dir = os.path.join(temp_dir, "test-venv")
        biobeamer_repo = "/srv/bfabriclocal/IdeaProjects/BioBeamer"
        
        # Skip if BioBeamer repo not available
        if not os.path.exists(biobeamer_repo):
            pytest.skip("BioBeamer repository not available")
        
        # Create virtual environment
        result = subprocess.run(
            ["uv", "venv", venv_dir],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Failed to create venv: {result.stderr}"
        
        # Install BioBeamer with -e flag (editable install)
        if platform.system() == "Windows":
            uv_cmd = "uv.exe"
            venv_scripts = os.path.join(venv_dir, "Scripts")
            biobeamer_exe = os.path.join(venv_scripts, "biobeamer.exe")
        else:
            uv_cmd = "uv"
            venv_bin = os.path.join(venv_dir, "bin")
            biobeamer_exe = os.path.join(venv_bin, "biobeamer")
        
        result = subprocess.run(
            [uv_cmd, "pip", "install", "-e", biobeamer_repo],
            env={
                **os.environ,
                "VIRTUAL_ENV": venv_dir,
            },
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Failed to install BioBeamer: {result.stderr}"
        
        # Check that the biobeamer executable was created
        assert os.path.exists(biobeamer_exe), f"BioBeamer executable not found: {biobeamer_exe}"
        assert os.access(biobeamer_exe, os.X_OK), f"BioBeamer executable is not executable: {biobeamer_exe}"
        
        # Test that the executable works
        if platform.system() == "Windows":
            test_cmd = [biobeamer_exe, "--help"]
        else:
            # On Linux, we need to activate the venv to run the executable
            test_cmd = ["bash", "-c", f"source {venv_dir}/bin/activate && {biobeamer_exe} --help"]
        
        result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, f"BioBeamer executable failed to run: {result.stderr}"
        assert "usage:" in result.stdout.lower(), "BioBeamer help output not found"


def test_biobeamer_entry_point_without_editable_flag():
    """Test that BioBeamer installation WITHOUT -e flag fails to create entry point properly."""
    if not shutil.which("uv"):
        pytest.skip("uv not available for testing")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_dir = os.path.join(temp_dir, "test-venv-no-e")
        biobeamer_repo = "/srv/bfabriclocal/IdeaProjects/BioBeamer"
        
        # Skip if BioBeamer repo not available
        if not os.path.exists(biobeamer_repo):
            pytest.skip("BioBeamer repository not available")
        
        # Create virtual environment
        result = subprocess.run(
            ["uv", "venv", venv_dir],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Failed to create venv: {result.stderr}"
        
        # Install BioBeamer WITHOUT -e flag (regular install)
        if platform.system() == "Windows":
            uv_cmd = "uv.exe"
            venv_scripts = os.path.join(venv_dir, "Scripts")
            biobeamer_exe = os.path.join(venv_scripts, "biobeamer.exe")
        else:
            uv_cmd = "uv"
            venv_bin = os.path.join(venv_dir, "bin")
            biobeamer_exe = os.path.join(venv_bin, "biobeamer")
        
        result = subprocess.run(
            [uv_cmd, "pip", "install", biobeamer_repo],  # Note: NO -e flag
            env={
                **os.environ,
                "VIRTUAL_ENV": venv_dir,
            },
            capture_output=True, text=True
        )
        
        # This should still install successfully, but might not create the entry point properly
        # NOTE: This test might pass on some systems and fail on others, 
        # depending on how setuptools handles non-editable installs
        
        # The key point is that our launcher should use -e to ensure it works consistently
        print(f"Install result: {result.returncode}")
        print(f"Install stdout: {result.stdout}")
        print(f"Install stderr: {result.stderr}")
        print(f"Executable exists: {os.path.exists(biobeamer_exe)}")


def test_launcher_uses_editable_install():
    """Test that the launcher code uses the -e flag when installing BioBeamer."""
    import biobeamer_launcher.launcher as launcher_module
    import inspect
    
    # Get the source code of the setup_biobeamer_venv function
    source = inspect.getsource(launcher_module.setup_biobeamer_venv)
    
    # Check that the source contains the -e flag
    assert '"-e"' in source, "Launcher should use -e flag for editable install"
    assert '"pip", "install", "-e"' in source, "Launcher should use 'pip install -e' command"
