import sys
import shutil
from pathlib import Path
import re
import pytest


def test_launcher_log_files(tmp_path, monkeypatch):
    """
    Integration test: Check that all expected log files are created in the correct log directory.
    """
    # Setup test file and config
    test_file_name = "testfile_log_check.txt"
    test_file_content = "log check content"
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    src_path = Path("/tmp/tmpsykd339y")
    tgt_path = Path("/tmp/tmphz8a5xe8")
    src_path.mkdir(parents=True, exist_ok=True)
    tgt_path.mkdir(parents=True, exist_ok=True)
    (src_path / test_file_name).write_text(test_file_content)

    # Write a minimal launcher.ini
    config_dir = tmp_path / "src" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    ini_path = config_dir / "launcher.ini"
    ini = f"""
[config]
biobeamer_repo_url = https://github.com/fgcz/BioBeamer.git
xml_file_path = https://github.com/fgcz/BioBeamerConfig/raw/main/xml/BioBeamerTest.xml
xsd_file_path = https://github.com/fgcz/BioBeamerConfig/raw/refs/heads/main/xml/BioBeamer2.xsd
host_name = testhost_log_check
log_dir = {log_dir}
"""
    ini_path.write_text(ini)

    # Copy launcher.py to temp src
    import os

    launcher_src = (
        Path(__file__).parent.parent / "src" / "biobeamer_launcher" / "launcher.py"
    )
    launcher_dest = tmp_path / "src" / "biobeamer_launcher"
    launcher_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(launcher_src, launcher_dest / "launcher.py")

    monkeypatch.setenv("BIOBEAMER_LAUNCHER_CACHE_DIR", str(tmp_path / "cache"))

    # Run the launcher
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(launcher_dest / "launcher.py")],
        cwd=tmp_path / "src",
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, f"Launcher failed: {proc.stdout}\n{proc.stderr}"

    # Check for expected logs
    logs = list(log_dir.glob("*"))
    log_names = [f.name for f in logs]
    # Launcher log
    assert any(
        "biobeamer_launcher" in n and n.endswith(".log") for n in log_names
    ), f"Launcher log missing in {log_names}"
    # Tool log (robocopy or scp)
    assert any(
        ("robocopy" in n or "scp" in n) and n.endswith(".log") for n in log_names
    ), f"Tool log missing in {log_names}"
    # BioBeamer log with date and time eg: biobeamer_20250610_101537.log
    assert any(
        re.match(r"biobeamer_\d{8}_\d{6}\.log$", n) for n in log_names
    ), f"BioBeamer log missing in {log_names}"
    # biobeamer subprocess log
    assert any(
        "biobeamer_subprocess" in n and n.endswith(".log") for n in log_names
    ), f"Subprocess log missing in {log_names}"
    # Copied files log
    assert any(
        "copied_files" in n and n.endswith(".txt") for n in log_names
    ), f"Copied files log missing in {log_names}"
