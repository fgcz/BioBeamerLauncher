import shutil
import subprocess
import sys
import os
from pathlib import Path

import pytest


# Official URLs

XML_URL = (
    "https://github.com/fgcz/BioBeamerConfig/raw/refs/heads/main/xml/BioBeamerTest.xml"
)
BIOBEAMER_REPO_URL = "https://github.com/fgcz/BioBeamer.git"
BIOBEAMER_BRANCH = "6-project-toml"
XSD_URL = (
    "https://github.com/fgcz/BioBeamerConfig/raw/refs/heads/main/xml/BioBeamer2.xsd"
)

SRC_PATH = Path("/tmp/tmpsykd339y")
TGT_PATH = Path("/tmp/tmphz8a5xe8")


@pytest.fixture
def remote_biobeamer_target_dir(request):
    """Setup and cleanup only the remote BioBeamer target directory via SSH, with error checking."""
    remote_host = getattr(request, "param", None) or "130.60.81.105"
    remote_user = "bfabriclocal"
    remote_tgt = "/tmp/biobeamer_tgt"
    # Run mkdir -p and check for errors
    mkdir_cmd = f"ssh {remote_user}@{remote_host} 'mkdir -p {remote_tgt}'"
    mkdir_proc = subprocess.run(
        mkdir_cmd, shell=True, capture_output=True, text=True, env=os.environ.copy()
    )
    if mkdir_proc.returncode != 0:
        print(f"[remote_biobeamer_target_dir] mkdir failed: {mkdir_proc.stderr}")
        raise RuntimeError(f"Failed to create remote directory: {remote_tgt}")
    # Run chmod and check for errors
    chmod_cmd = f"ssh {remote_user}@{remote_host} 'chmod 777 {remote_tgt}'"
    chmod_proc = subprocess.run(
        chmod_cmd, shell=True, capture_output=True, text=True, env=os.environ.copy()
    )
    if chmod_proc.returncode != 0:
        print(f"[remote_biobeamer_target_dir] chmod failed: {chmod_proc.stderr}")
        raise RuntimeError(f"Failed to chmod remote directory: {remote_tgt}")
    yield remote_tgt, remote_user, remote_host
    cleanup_cmd = f"ssh {remote_user}@{remote_host} 'rm -rf {remote_tgt}/*'"
    subprocess.run(cleanup_cmd, shell=True, env=os.environ.copy())


def run_real_launcher_test(
    tmp_path,
    monkeypatch,
    host_name,
    test_file_name,
    test_file_content,
    src_path=None,
    tgt_path=None,
    check_target=True,
    remote_fixture=None,
):
    config_dir = tmp_path / "src" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    ini_path = config_dir / "launcher.ini"
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    # Clean up SRC_PATH and TGT_PATH before test
    if src_path is None:
        src_path = SRC_PATH
    if tgt_path is None:
        tgt_path = TGT_PATH
    for p in [src_path, tgt_path]:
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
    src_path.mkdir(parents=True, exist_ok=True)
    if check_target:
        tgt_path.mkdir(parents=True, exist_ok=True)
    test_file = src_path / test_file_name
    test_file.write_text(test_file_content)
    proc = subprocess.run(
        [sys.executable, str(launcher_dest / "launcher.py")],
        cwd=tmp_path / "src",
        capture_output=True,
        text=True,
        timeout=300,
        env=os.environ.copy(),
    )
    print("STDOUT:\n", proc.stdout)
    print("STDERR:\n", proc.stderr)
    if proc.returncode != 0:
        print("About to raise RuntimeError due to non-zero exit code")
        raise RuntimeError(
            f"BioBeamer exited with code {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    print("This should never print after raise!")
    if check_target:
        # Check remote target file existence and content
        if host_name == "testhost_real_remote_scp":
            remote_tgt, remote_user, remote_host = (
                remote_fixture
                if remote_fixture
                else ("/tmp/biobeamer_tgt", "bfabriclocal", "130.60.81.105")
            )
            remote_file = f"{remote_tgt}/{test_file_name}"
            check_cmd = f"ssh {remote_user}@{remote_host} 'test -f {remote_file} && cat {remote_file}'"
            result = subprocess.run(
                check_cmd,
                shell=True,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )
            assert (
                result.returncode == 0
            ), f"Expected remote file {remote_file} to exist after copy"
            assert (
                result.stdout.strip() == test_file_content
            ), "Remote copied file content mismatch"
        else:
            copied_file = tgt_path / test_file_name
            assert (
                copied_file.exists()
            ), f"Expected file {copied_file} to exist after copy"
            assert (
                copied_file.read_text() == test_file_content
            ), "Copied file content mismatch"
    try:
        test_file.unlink()
    except FileNotFoundError:
        pass
    if check_target and not (host_name == "testhost_real_remote_scp"):
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


@pytest.mark.real_integration
@pytest.mark.skipif(not is_tool_available("scp"), reason="scp not available on system")
def test_launcher_with_real_remote_scp(
    tmp_path, monkeypatch, remote_biobeamer_target_dir
):
    run_real_launcher_test(
        tmp_path,
        monkeypatch,
        host_name="testhost_real_remote_scp",
        test_file_name="testfile_remote.txt",
        test_file_content="integration test file content remote scp",
        # Use a local temp dir for the source, matching the XML config
        src_path=Path("/tmp/tmpsykd339y"),
        tgt_path=None,
        check_target=True,
        remote_fixture=remote_biobeamer_target_dir,
    )
