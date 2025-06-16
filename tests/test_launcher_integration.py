import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest
from conftest import make_dummy_biobeamer2_py, make_dummy_pyproject_toml


@pytest.mark.integration
def test_launcher_runs_biobeamer_and_copies_file(tmp_path, monkeypatch):
    # Setup directories
    # Place config in <project-root>/config/launcher.ini, where project root is two levels above launcher.py
    # This matches the default logic in get_xml_config_path()
    config_dir = tmp_path / "src" / "config"
    config_dir.mkdir(parents=True)
    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()
    repo_dir = tmp_path / "biobeamer_repo" / "BioBeamer" / "src"
    repo_dir.mkdir(parents=True)
    # Write dummy biobeamer2.py
    biobeamer2_py = repo_dir / "biobeamer2.py"
    make_dummy_biobeamer2_py(biobeamer2_py, variant="integration")
    # Git init and tag
    repo_root = repo_dir.parent
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=repo_root)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root)
    # Add minimal pyproject.toml so uv/pip can install the dummy package
    make_dummy_pyproject_toml(repo_root / "pyproject.toml")
    subprocess.run(["git", "add", "pyproject.toml"], cwd=repo_root)
    subprocess.run(["git", "add", "src/biobeamer2.py"], cwd=repo_root)
    subprocess.run(
        ["git", "commit", "-m", "add dummy biobeamer2.py and pyproject.toml"],
        cwd=repo_root,
    )
    subprocess.run(["git", "tag", "v1.0.0"], cwd=repo_root)
    # Write XML, XSD, input.txt
    xml_path = xml_dir / "BioBeamerTest.xml"
    xml_path.write_text(
        '<BioBeamerHosts><host name="testhost" version="v1.0.0"/></BioBeamerHosts>'
    )
    xsd_path = xml_dir / "BioBeamer2.xsd"
    xsd_path.write_text(
        '<xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified" xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="BioBeamerHosts"><xs:complexType><xs:sequence><xs:element name="host" maxOccurs="unbounded" minOccurs="0"><xs:complexType><xs:sequence/><xs:attribute type="xs:string" name="name" use="optional"/><xs:attribute type="xs:string" name="version" use="optional"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>'
    )
    (xml_dir / "input.txt").write_text("testdata")
    # Write launcher.ini with absolute paths
    ini = f"""[config]\nbiobeamer_repo_url = file://{repo_root}\nxml_file_path = {xml_path.resolve()}\nxsd_file_path = {xsd_path.resolve()}\nhost_name = testhost\n"""
    ini_path = config_dir / "launcher.ini"
    ini_path.write_text(ini)
    # Copy launcher.py into place
    # Place launcher.py at tmp_path/src/biobeamer_launcher/launcher.py so project root is tmp_path
    src_launcher = (
        Path(__file__).parent.parent / "src" / "biobeamer_launcher" / "launcher.py"
    )
    launcher_dest = tmp_path / "src" / "biobeamer_launcher"
    launcher_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_launcher, launcher_dest / "launcher.py")
    # Set env for cache dir
    monkeypatch.setenv("BIOBEAMER_LAUNCHER_CACHE_DIR", str(tmp_path / "cache"))
    # Run launcher with no --config argument, so it uses the default config path logic
    proc = subprocess.run(
        [sys.executable, str(launcher_dest / "launcher.py")],
        cwd=tmp_path / "src",
        capture_output=True,
        text=True,
    )
    # Check output.txt was created
    output_txt = xml_dir / "output.txt"
    if not output_txt.exists():
        # Print log file for debugging
        log_dir = tmp_path / "cache"
        log_file = log_dir / "biobeamer_testhost.log"
        launcher_log_file = log_dir / "biobeamer_launcher.log"
        # Print all files in log_dir for debugging
        print(
            "Log dir contents:",
            list(log_dir.iterdir()) if log_dir.exists() else "(not found)",
        )
        if log_file.exists():
            print("=== biobeamer_testhost.log ===")
            print(log_file.read_text())
        else:
            print("Log file not found:", log_file)
        if launcher_log_file.exists():
            print("=== biobeamer_launcher.log ===")
            print(launcher_log_file.read_text())
        else:
            print("Launcher log file not found:", launcher_log_file)
        print("STDOUT:\n", proc.stdout)
        print("STDERR:\n", proc.stderr)
    assert output_txt.exists(), "output.txt should be created by dummy biobeamer2.py"
    assert output_txt.read_text() == "testdata"
    # Check logs for copy message
    log_dir = tmp_path / "cache"
    log_file = log_dir / "biobeamer_testhost.log"
    assert "Copied" in log_file.read_text()
    # Add a comment to clarify why this works
    # The launcher will look for config at <project-root>/config/launcher.ini, which is tmp_path/src/config/launcher.ini
    # because launcher.py is at tmp_path/src/biobeamer_launcher/launcher.py
