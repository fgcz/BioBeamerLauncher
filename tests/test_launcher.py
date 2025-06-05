import os
import pytest
import importlib.util
from io import StringIO
import sys
import shutil
import tempfile
from pathlib import Path
import logging


# Test fixtures for shared config and XML/XSD content
INI_MINIMAL = """[config]
biobeamer_repo_url = https://example.com/repo.git
config_file_path = configs/BioBeamerTest.xml
xsd_file_path = configs/BioBeamer2.xsd
host_name = testhost
"""

XML_MINIMAL = (
    """<BioBeamerHosts><host name=\"testhost\" version=\"v1.0.0\"/></BioBeamerHosts>"""
)

XSD_MINIMAL = """<xs:schema attributeFormDefault=\"unqualified\" elementFormDefault=\"qualified\" xmlns:xs=\"http://www.w3.org/2001/XMLSchema\">
  <xs:element name=\"BioBeamerHosts\">
    <xs:complexType>
      <xs:sequence>
        <xs:element name=\"host\" maxOccurs=\"unbounded\" minOccurs=\"0\">
          <xs:complexType>
            <xs:sequence/>
            <xs:attribute type=\"xs:string\" name=\"name\" use=\"optional\"/>
            <xs:attribute type=\"xs:string\" name=\"version\" use=\"optional\"/>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>"""


def create_temp_launcher_env(
    tmp_path,
    ini_content,
    xml_content=None,
    xsd_content=None,
    create_repo=False,
    tag_name="v1.0.0",
):
    """
    Helper to set up a temp launcher environment with config, optional XML/XSD, and optional git repo.
    Returns a dict with paths and objects for use in tests.
    """
    config_dir = tmp_path / "src" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    ini_path = config_dir / "launcher.ini"
    ini_path.write_text(ini_content)

    xml_path = xsd_path = repo_path = None
    if xml_content:
        xml_dir = tmp_path / "xml"
        xml_dir.mkdir(exist_ok=True)
        xml_path = xml_dir / "BioBeamerTest.xml"
        xml_path.write_text(xml_content)
    if xsd_content:
        xsd_dir = tmp_path / "xml"
        xsd_dir.mkdir(exist_ok=True)
        xsd_path = xsd_dir / "BioBeamer2.xsd"
        xsd_path.write_text(xsd_content)
    if create_repo:
        repo_dir = tmp_path / "biobeamer_repo"
        repo_dir.mkdir(exist_ok=True)
        repo_path = repo_dir / "BioBeamer"
        repo_path.mkdir(exist_ok=True)
        (repo_path / "README.md").write_text("# Dummy BioBeamer repo")
        import subprocess

        subprocess.run(["git", "init", "--initial-branch=main"], cwd=repo_path)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=repo_path
        )
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path)
        subprocess.run(["git", "add", "README.md"], cwd=repo_path)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo_path)
        subprocess.run(["git", "tag", tag_name], cwd=repo_path)
    src_dir = tmp_path / "src" / "biobeamer_launcher"
    src_dir.mkdir(parents=True, exist_ok=True)
    orig_launcher = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../src/biobeamer_launcher/launcher.py")
    )
    shutil.copy(orig_launcher, src_dir / "launcher.py")
    return {
        "config_dir": config_dir,
        "ini_path": ini_path,
        "xml_path": xml_path,
        "xsd_path": xsd_path,
        "repo_path": repo_path,
        "src_dir": src_dir,
    }


@pytest.fixture
def minimal_xml():
    return XML_MINIMAL


@pytest.fixture
def minimal_xsd():
    return XSD_MINIMAL


@pytest.fixture(autouse=True)
def set_biobeamer_cache_env(tmp_path, monkeypatch):
    cache_dir = str(tmp_path / "cache")
    monkeypatch.setenv("BIOBEAMER_LAUNCHER_CACHE_DIR", cache_dir)
    return cache_dir


def test_launcher_ini_read(monkeypatch, tmp_path):
    env = create_temp_launcher_env(tmp_path, INI_MINIMAL)
    monkeypatch.chdir(tmp_path / "src")
    spec = importlib.util.spec_from_file_location(
        "launcher", str(env["src_dir"] / "launcher.py")
    )
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    captured = StringIO()
    sys.stdout = captured
    launcher.main()
    sys.stdout = sys.__stdout__
    output = captured.getvalue()
    assert "BioBeamer repo URL: https://example.com/repo.git" in output
    assert "Config file path: configs/BioBeamerTest.xml" in output
    assert "Host name: testhost" in output
    shutil.rmtree(tmp_path)


def test_launcher_logging_and_config(monkeypatch, tmp_path):
    env = create_temp_launcher_env(tmp_path, INI_MINIMAL)
    monkeypatch.chdir(tmp_path / "src")
    spec = importlib.util.spec_from_file_location(
        "launcher", str(env["src_dir"] / "launcher.py")
    )
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    logger = launcher.setup_logging()
    log_stream = StringIO()
    for handler in logger.handlers:
        logger.removeHandler(handler)
    stream_handler = logging.StreamHandler(log_stream)
    logger.addHandler(stream_handler)
    sys_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        launcher.main()
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = sys_stdout
    logs = log_stream.getvalue()
    assert "BioBeamer repo URL" in output
    assert "config_file_path" in output or "Config file path" in output
    assert "host_name" in output or "Host name" in output
    assert (
        "Could not fetch XML config file." in logs
        or "Could not fetch XML config file." in output
    )
    shutil.rmtree(tmp_path)


def test_xml_validation_and_repo_checkout(
    monkeypatch, tmp_path, minimal_xml, minimal_xsd
):
    ini_content = f"""[config]
biobeamer_repo_url = file://{tmp_path}/biobeamer_repo/BioBeamer
config_file_path = {tmp_path}/xml/BioBeamerTest.xml
xsd_file_path = {tmp_path}/xml/BioBeamer2.xsd
host_name = testhost
"""
    env = create_temp_launcher_env(
        tmp_path,
        ini_content,
        xml_content=minimal_xml,
        xsd_content=minimal_xsd,
        create_repo=True,
        tag_name="v1.0.0",
    )
    monkeypatch.chdir(tmp_path / "src")
    spec = importlib.util.spec_from_file_location(
        "launcher", str(env["src_dir"] / "launcher.py")
    )
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    logger = launcher.setup_logging()
    log_stream = StringIO()
    for handler in logger.handlers:
        logger.removeHandler(handler)
    stream_handler = logging.StreamHandler(log_stream)
    logger.addHandler(stream_handler)
    sys_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        launcher.main()
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = sys_stdout
    logs = log_stream.getvalue()
    assert "XML validation succeeded." in logs
    assert "BioBeamer repo ready at" in logs
    assert "v1.0.0" in logs
    assert "Selected host entry" in logs
    assert "testhost" in logs
    shutil.rmtree(tmp_path)
