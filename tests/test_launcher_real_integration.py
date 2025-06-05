import sys
import shutil
import subprocess
import tempfile
import os
from pathlib import Path
import configparser
import pytest
import time

# Official URLs
XML_URL = (
    "https://github.com/fgcz/BioBeamerConfig/raw/refs/heads/main/xml/BioBeamerTest.xml"
)
BIOBEAMER_REPO_URL = "https://github.com/fgcz/BioBeamer.git"
BIOBEAMER_BRANCH = "6-project-toml"
XSD_URL = (
    "https://github.com/fgcz/BioBeamerConfig/raw/refs/heads/main/xml/BioBeamer2.xsd"
)
HOST_NAME = "testhost_real_integration"  # You may need to adjust this to a valid host in the XML

SRC_PATH = Path("/tmp/tmpsykd339y")
TGT_PATH = Path("/tmp/tmphz8a5xe8")


@pytest.mark.real_integration
def test_launcher_with_real_sources(tmp_path, monkeypatch):
    # Prepare config directory in the expected location (src/config)
    config_dir = tmp_path / "src" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    ini_path = config_dir / "launcher.ini"
    ini = f"""
[config]
biobeamer_repo_url = {BIOBEAMER_REPO_URL}
config_file_path = {XML_URL}
xsd_file_path = {XSD_URL}
host_name = {HOST_NAME}
"""
    ini_path.write_text(ini)

    # Copy launcher.py into place
    src_launcher = (
        Path(__file__).parent.parent / "src" / "biobeamer_launcher" / "launcher.py"
    )
    launcher_dest = tmp_path / "src" / "biobeamer_launcher"
    launcher_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_launcher, launcher_dest / "launcher.py")

    # Set env for cache dir
    monkeypatch.setenv("BIOBEAMER_LAUNCHER_CACHE_DIR", str(tmp_path / "cache"))

    # --- Setup: create temp file in source dir ---
    SRC_PATH.mkdir(parents=True, exist_ok=True)
    TGT_PATH.mkdir(parents=True, exist_ok=True)
    test_file = SRC_PATH / "testfile.txt"
    test_content = "integration test file content"
    test_file.write_text(test_content)

    # Run launcher
    proc = subprocess.run(
        [sys.executable, str(launcher_dest / "launcher.py")],
        cwd=tmp_path / "src",
        capture_output=True,
        text=True,
        timeout=300,
    )
    print("STDOUT:\n", proc.stdout)
    print("STDERR:\n", proc.stderr)

    # --- Verify file was copied ---
    copied_file = TGT_PATH / "testfile.txt"
    assert copied_file.exists(), f"Expected file {copied_file} to exist after copy"
    assert copied_file.read_text() == test_content, "Copied file content mismatch"

    # --- Cleanup ---
    try:
        test_file.unlink()
    except FileNotFoundError:
        pass
    try:
        copied_file.unlink()
    except FileNotFoundError:
        pass

    # Optionally, check for available hosts in the error message
    # Assert that the process fails and the error message is present
    # assert proc.returncode != 0, "Launcher should fail when host is not found"
