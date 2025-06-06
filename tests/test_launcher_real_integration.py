import shutil
import subprocess
import sys
from pathlib import Path

import pytest


# Official URLs
XML_URL = "https://github.com/fgcz/BioBeamerConfig/raw/main/xml/BioBeamerTest.xml"
BIOBEAMER_REPO_URL = "https://github.com/fgcz/BioBeamer.git"
BIOBEAMER_BRANCH = "6-project-toml"
XSD_URL = (
    "https://github.com/fgcz/BioBeamerConfig/raw/refs/heads/main/xml/BioBeamer2.xsd"
)

SRC_PATH = Path("/tmp/tmpsykd339y")
TGT_PATH = Path("/tmp/tmphz8a5xe8")


def run_real_launcher_test(
    tmp_path, monkeypatch, host_name, test_file_name, test_file_content
):
    config_dir = tmp_path / "src" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    ini_path = config_dir / "launcher.ini"
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    # Clean up SRC_PATH and TGT_PATH before test
    for p in [SRC_PATH, TGT_PATH]:
        if p.exists() and p.is_dir():
            for f in p.iterdir():
                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    shutil.rmtree(f)
    ini = f"""
[config]
biobeamer_repo_url = {BIOBEAMER_REPO_URL}
xml_file_path = {XML_URL}
xsd_file_path = {XSD_URL}
host_name = {host_name}
log_dir = {log_dir}
"""
    ini_path.write_text(ini)
    src_launcher = (
        Path(__file__).parent.parent / "src" / "biobeamer_launcher" / "launcher.py"
    )
    launcher_dest = tmp_path / "src" / "biobeamer_launcher"
    launcher_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_launcher, launcher_dest / "launcher.py")
    monkeypatch.setenv("BIOBEAMER_LAUNCHER_CACHE_DIR", str(tmp_path / "cache"))
    SRC_PATH.mkdir(parents=True, exist_ok=True)
    TGT_PATH.mkdir(parents=True, exist_ok=True)
    test_file = SRC_PATH / test_file_name
    test_file.write_text(test_file_content)
    proc = subprocess.run(
        [sys.executable, str(launcher_dest / "launcher.py")],
        cwd=tmp_path / "src",
        capture_output=True,
        text=True,
        timeout=300,
    )
    print("STDOUT:\n", proc.stdout)
    print("STDERR:\n", proc.stderr)
    assert proc.returncode == 0, f"BioBeamer exited with code {proc.returncode}"
    copied_file = TGT_PATH / test_file_name
    assert copied_file.exists(), f"Expected file {copied_file} to exist after copy"
    assert copied_file.read_text() == test_file_content, "Copied file content mismatch"
    try:
        test_file.unlink()
    except FileNotFoundError:
        pass
    try:
        copied_file.unlink()
    except FileNotFoundError:
        pass


def is_tool_available(tool_name):
    """Check whether `tool_name` is on PATH and marked as executable."""
    from shutil import which

    return which(tool_name) is not None


@pytest.mark.real_integration
@pytest.mark.skipif(not is_tool_available("scp"), reason="scp not available on system")
def test_launcher_with_real_sources_scp(tmp_path, monkeypatch):
    run_real_launcher_test(
        tmp_path,
        monkeypatch,
        host_name="testhost_real_integration_scp",
        test_file_name="testfile.txt",
        test_file_content="integration test file content",
    )


@pytest.mark.real_integration
@pytest.mark.skipif(
    not is_tool_available("robocopy.exe") and not is_tool_available("robocopy"),
    reason="robocopy not available on system",
)
def test_launcher_with_real_sources_robocopy(tmp_path, monkeypatch):
    run_real_launcher_test(
        tmp_path,
        monkeypatch,
        host_name="testhost_real_integration_robocopy",
        test_file_name="testfile_robocopy.txt",
        test_file_content="integration test file content robocopy",
    )
