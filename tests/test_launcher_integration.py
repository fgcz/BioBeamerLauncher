import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest


def make_dummy_biobeamer2_py(path):
    # This dummy script copies a file from input to output, simulating BioBeamer work
    script = """import argparse, shutil, os
parser = argparse.ArgumentParser()
parser.add_argument('--xml')
parser.add_argument('--xsd')
parser.add_argument('--hostname')
parser.add_argument('--log_dir')  # Accept and ignore log_dir
args = parser.parse_args()
# Simulate work: copy a file named 'input.txt' to 'output.txt' in the same dir as xml
src = os.path.join(os.path.dirname(args.xml), 'input.txt')
dst = os.path.join(os.path.dirname(args.xml), 'output.txt')
if os.path.exists(src):
    shutil.copyfile(src, dst)
    print(f'Copied {src} to {dst}')
else:
    print('No input.txt found, nothing copied')
"""
    with open(path, "w") as f:
        f.write(script)


@pytest.mark.integration
def test_launcher_runs_biobeamer_and_copies_file(tmp_path, monkeypatch):
    # Setup directories
    config_dir = tmp_path / "src" / "config"
    config_dir.mkdir(parents=True)
    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()
    repo_dir = tmp_path / "biobeamer_repo" / "BioBeamer" / "src"
    repo_dir.mkdir(parents=True)
    # Write dummy biobeamer2.py
    biobeamer2_py = repo_dir / "biobeamer2.py"
    make_dummy_biobeamer2_py(biobeamer2_py)
    # Git init and tag
    repo_root = repo_dir.parent
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=repo_root)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root)
    subprocess.run(["git", "add", "src/biobeamer2.py"], cwd=repo_root)
    subprocess.run(["git", "commit", "-m", "add dummy biobeamer2.py"], cwd=repo_root)
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
    src_launcher = (
        Path(__file__).parent.parent / "src" / "biobeamer_launcher" / "launcher.py"
    )
    launcher_dest = tmp_path / "src" / "biobeamer_launcher"
    launcher_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_launcher, launcher_dest / "launcher.py")
    # Set env for cache dir
    monkeypatch.setenv("BIOBEAMER_LAUNCHER_CACHE_DIR", str(tmp_path / "cache"))
    # Run launcher with --config argument
    proc = subprocess.run(
        [sys.executable, str(launcher_dest / "launcher.py"), "--config", str(ini_path)],
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
        if log_file.exists():
            print("=== biobeamer_testhost.log ===")
            print(log_file.read_text())
        else:
            print("Log file not found:", log_file)
    assert output_txt.exists(), "output.txt should be created by dummy biobeamer2.py"
    assert output_txt.read_text() == "testdata"
    # Check logs for copy message
    log_dir = tmp_path / "cache"
    log_file = log_dir / "biobeamer_testhost.log"
    assert "Copied" in log_file.read_text()
