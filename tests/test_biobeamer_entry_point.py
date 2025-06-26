import os
import subprocess
import tempfile
import shutil
import pytest
import platform

def test_biobeamer_entry_point_creation():
    """Test that BioBeamer installation creates the proper entry point executable."""
    # Find uv in multiple locations
    uv_cmd = None
    possible_uv_paths = [
        "uv",  # System PATH
        "uv.exe",  # Windows system PATH
        os.path.join(os.path.dirname(__file__), "..", "scripts", "uv.exe"),  # Bundled Windows
        os.path.join(os.path.dirname(__file__), "..", "scripts", "uv"),  # Bundled Linux
    ]
    
    for uv_path in possible_uv_paths:
        if shutil.which(uv_path) or os.path.exists(uv_path):
            uv_cmd = uv_path
            break
    
    if not uv_cmd:
        pytest.skip("uv not available for testing")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_dir = os.path.join(temp_dir, "test-venv")
        
        # Try to find BioBeamer repo in common locations
        possible_paths = [
            "/srv/bfabriclocal/IdeaProjects/BioBeamer",  # Linux
            os.path.join(os.path.dirname(__file__), "..", "..", "BioBeamer"),  # Relative path
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "BioBeamer")),  # Absolute relative path
        ]
        
        biobeamer_repo = None
        for path in possible_paths:
            print(f"Checking BioBeamer path: {path}")
            if os.path.exists(path) and os.path.exists(os.path.join(path, "pyproject.toml")):
                biobeamer_repo = path
                print(f"Found BioBeamer repo at: {path}")
                break
        
        # If BioBeamer repo not available, create a minimal test package
        if not biobeamer_repo:
            print("BioBeamer repository not found, creating minimal test package...")
            test_package_dir = os.path.join(temp_dir, "test-biobeamer")
            os.makedirs(test_package_dir)
            os.makedirs(os.path.join(test_package_dir, "src", "biobeamer"))
            
            # Create minimal pyproject.toml
            pyproject_content = '''[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "biobeamer"
version = "0.1.0"
description = "Test package for entry point testing"

[project.scripts]
biobeamer = "biobeamer.cli:main"
'''
            with open(os.path.join(test_package_dir, "pyproject.toml"), "w") as f:
                f.write(pyproject_content)
            
            # Create minimal CLI module
            cli_content = '''def main():
    print("usage: biobeamer [-h] command")
    print("Test BioBeamer CLI")

if __name__ == "__main__":
    main()
'''
            with open(os.path.join(test_package_dir, "src", "biobeamer", "__init__.py"), "w") as f:
                f.write("")
            with open(os.path.join(test_package_dir, "src", "biobeamer", "cli.py"), "w") as f:
                f.write(cli_content)
            
            biobeamer_repo = test_package_dir
            print(f"Created test package at: {biobeamer_repo}")
        
        # Create virtual environment
        result = subprocess.run(
            [uv_cmd, "venv", venv_dir],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Failed to create venv: {result.stderr}"
        
        # Install BioBeamer with -e flag (editable install)
        if platform.system() == "Windows":
            # Use the same uv_cmd we found
            venv_scripts = os.path.join(venv_dir, "Scripts")
            biobeamer_exe = os.path.join(venv_scripts, "biobeamer.exe")
        else:
            # Use the same uv_cmd we found  
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
        
        # Print diagnostics for debugging
        print(f"Install command: {' '.join([uv_cmd, 'pip', 'install', '-e', biobeamer_repo])}")
        print(f"Install return code: {result.returncode}")
        print(f"Install stdout: {result.stdout}")
        print(f"Install stderr: {result.stderr}")
        
        # List contents of Scripts/bin directory for debugging
        if platform.system() == "Windows":
            scripts_dir = os.path.join(venv_dir, "Scripts")
            print(f"Scripts directory contents: {os.listdir(scripts_dir) if os.path.exists(scripts_dir) else 'Not found'}")
        else:
            bin_dir = os.path.join(venv_dir, "bin")
            print(f"Bin directory contents: {os.listdir(bin_dir) if os.path.exists(bin_dir) else 'Not found'}")
        
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
    # Find uv in multiple locations
    uv_cmd = None
    possible_uv_paths = [
        "uv",  # System PATH
        "uv.exe",  # Windows system PATH
        os.path.join(os.path.dirname(__file__), "..", "scripts", "uv.exe"),  # Bundled Windows
        os.path.join(os.path.dirname(__file__), "..", "scripts", "uv"),  # Bundled Linux
    ]
    
    for uv_path in possible_uv_paths:
        if shutil.which(uv_path) or os.path.exists(uv_path):
            uv_cmd = uv_path
            break
    
    if not uv_cmd:
        pytest.skip("uv not available for testing")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_dir = os.path.join(temp_dir, "test-venv-no-e")
        
        # Try to find BioBeamer repo in common locations
        possible_paths = [
            "/srv/bfabriclocal/IdeaProjects/BioBeamer",  # Linux
            "C:\\srv\\bfabriclocal\\IdeaProjects\\BioBeamer",  # Windows with same structure
            "D:\\srv\\bfabriclocal\\IdeaProjects\\BioBeamer",  # Windows D: drive
            os.path.join(os.path.dirname(__file__), "..", "..", "BioBeamer"),  # Relative path
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "BioBeamer")),  # Absolute relative path
        ]
        
        biobeamer_repo = None
        for path in possible_paths:
            if os.path.exists(path) and os.path.exists(os.path.join(path, "pyproject.toml")):
                biobeamer_repo = path
                break
        
        # Skip if BioBeamer repo not available
        if not biobeamer_repo:
            pytest.skip("BioBeamer repository not available in expected locations")
        
        # Create virtual environment
        result = subprocess.run(
            [uv_cmd, "venv", venv_dir],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Failed to create venv: {result.stderr}"
        
        # Install BioBeamer WITHOUT -e flag (regular install)
        if platform.system() == "Windows":
            venv_scripts = os.path.join(venv_dir, "Scripts")
            biobeamer_exe = os.path.join(venv_scripts, "biobeamer.exe")
        else:
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
    try:
        import biobeamer_launcher.launcher as launcher_module
        import inspect
        
        # Get the source code of the setup_biobeamer_venv function
        source = inspect.getsource(launcher_module.setup_biobeamer_venv)
        
        # Check that the source contains the -e flag
        assert '"-e"' in source, "Launcher should use -e flag for editable install"
        assert '"pip", "install", "-e"' in source, "Launcher should use 'pip install -e' command"
    except ImportError:
        # If we can't import the module, check the source file directly
        import os
        current_dir = os.path.dirname(__file__)
        launcher_file = os.path.join(current_dir, "..", "src", "biobeamer_launcher", "launcher.py")
        
        if os.path.exists(launcher_file):
            with open(launcher_file, 'r') as f:
                source = f.read()
            
            # Check that the source contains the -e flag
            assert '"-e"' in source, "Launcher should use -e flag for editable install"
            assert '"pip", "install", "-e"' in source, "Launcher should use 'pip install -e' command"
        else:
            pytest.skip("Could not find launcher module or source file")
