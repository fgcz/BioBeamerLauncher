import os
import importlib.util
import tempfile
import shutil
from pathlib import Path
import logging
import pytest


def import_launcher():
    launcher_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "src", "biobeamer_launcher", "launcher.py"
        )
    )
    spec = importlib.util.spec_from_file_location("launcher", launcher_path)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    return launcher


def test_read_launcher_config(tmp_path):
    launcher = import_launcher()
    logger = launcher.get_logger("test_logger")
    ini_content = """[config]\nbiobeamer_repo_url = https://example.com/repo.git\nxml_file_path = /tmp/config.xml\nxsd_file_path = /tmp/config.xsd\nhost_name = testhost\n"""
    ini_path = tmp_path / "launcher.ini"
    ini_path.write_text(ini_content)
    cfg = launcher.read_launcher_config(str(ini_path), logger=logger)
    assert cfg["biobeamer_repo_url"] == "https://example.com/repo.git"
    assert cfg["xml_file_path"] == "/tmp/config.xml"
    assert cfg["xsd_file_path"] == "/tmp/config.xsd"
    assert cfg["host_name"] == "testhost"


def test_print_launcher_config(caplog):
    launcher = import_launcher()
    logger = launcher.get_logger("test_logger")
    cfg = {
        "biobeamer_repo_url": "https://example.com/repo.git",
        "xml_file_path": "/tmp/config.xml",
        "xsd_file_path": "/tmp/config.xsd",
        "host_name": "testhost",
    }
    with caplog.at_level("INFO", logger="test_logger"):
        launcher.print_launcher_config(cfg, logger=logger)
    out = caplog.text
    assert "BioBeamerLauncher configuration:" in out
    assert "BioBeamer repo URL: https://example.com/repo.git" in out
    assert "Config file path: /tmp/config.xml" in out
    assert "XSD file path: /tmp/config.xsd" in out
    assert "Host name: testhost" in out


def test_fetch_xml_config_local(tmp_path, caplog):
    launcher = import_launcher()
    logger = launcher.get_logger("test_logger")
    xml_path = tmp_path / "test.xml"
    xml_path.write_text("<root/>")
    with caplog.at_level("INFO", logger="test_logger"):
        result = launcher.fetch_xml_config(str(xml_path), logger=logger)
    assert result == str(xml_path)
    assert "Using local XML config" in caplog.text


def test_fetch_xml_config_remote(monkeypatch, tmp_path, caplog):
    launcher = import_launcher()
    logger = launcher.get_logger("test_logger")

    # Patch urllib.request.urlretrieve to simulate download
    def fake_urlretrieve(url, filename):
        Path(filename).write_text("<root/>")
        return (filename, None)

    monkeypatch.setattr(launcher.urllib.request, "urlretrieve", fake_urlretrieve)
    url = "http://example.com/test.xml"
    with caplog.at_level("INFO", logger="test_logger"):
        result = launcher.fetch_xml_config(url, logger=logger)
    assert os.path.exists(result)
    assert Path(result).read_text() == "<root/>"
    assert "Downloading XML config from http://example.com/test.xml" in caplog.text
    os.remove(result)


def test_get_cache_dir_env(monkeypatch, tmp_path):
    launcher = import_launcher()
    monkeypatch.setenv("BIOBEAMER_LAUNCHER_CACHE_DIR", str(tmp_path / "cache"))
    assert launcher.get_cache_dir() == str(tmp_path / "cache")


def test_fetch_xsd_file_local(tmp_path, caplog):
    launcher = import_launcher()
    logger = launcher.get_logger("test_logger")
    xsd_path = tmp_path / "test.xsd"
    xsd_path.write_text("<xsd/>")
    with caplog.at_level("INFO", logger="test_logger"):
        result = launcher.fetch_xsd_file(str(xsd_path), logger=logger)
    assert result == str(xsd_path)
    assert "Using local XSD" in caplog.text


def test_fetch_xsd_file_remote(monkeypatch, tmp_path, caplog):
    launcher = import_launcher()
    logger = launcher.get_logger("test_logger")

    def fake_urlretrieve(url, filename):
        Path(filename).write_text("<xsd/>")
        return (filename, None)

    monkeypatch.setattr(launcher.urllib.request, "urlretrieve", fake_urlretrieve)
    url = "http://example.com/test.xsd"
    with caplog.at_level("INFO", logger="test_logger"):
        result = launcher.fetch_xsd_file(url, logger=logger)
    assert os.path.exists(result)
    assert Path(result).read_text() == "<xsd/>"
    assert "Downloading XSD from http://example.com/test.xsd" in caplog.text
    os.remove(result)


def test_parse_xml_and_select_host(tmp_path, caplog):
    launcher = import_launcher()
    logger = launcher.get_logger("test_logger")
    xml_path = tmp_path / "test.xml"
    xml_path.write_text(
        '<BioBeamerHosts><host name="foo" version="1.2.3"/></BioBeamerHosts>'
    )
    with caplog.at_level("INFO", logger="test_logger"):
        result = launcher.parse_xml_and_select_host(str(xml_path), "foo", logger=logger)
    assert result["name"] == "foo"
    assert result["version"] == "1.2.3"
    assert "Found host entry: foo" in caplog.text
    with caplog.at_level("ERROR", logger="test_logger"):
        assert (
            launcher.parse_xml_and_select_host(str(xml_path), "bar", logger=logger)
            is None
        )
        assert "Host 'bar' not found in XML config." in caplog.text


def test_validate_xml_with_xsd(tmp_path, caplog):
    launcher = import_launcher()
    logger = launcher.get_logger("test_logger")
    xml_path = tmp_path / "test.xml"
    xsd_path = tmp_path / "test.xsd"
    xml_path.write_text(
        '<BioBeamerHosts><host name="foo" version="1.2.3"/></BioBeamerHosts>'
    )
    xsd_path.write_text(
        '<xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified" xmlns:xs="http://www.w3.org/2001/XMLSchema">\n'
        '<xs:element name="BioBeamerHosts">\n'
        "  <xs:complexType>\n"
        "    <xs:sequence>\n"
        '      <xs:element name="host" maxOccurs="unbounded" minOccurs="0">\n'
        "        <xs:complexType>\n"
        "          <xs:sequence/>\n"
        '          <xs:attribute type="xs:string" name="name" use="optional"/>\n'
        '          <xs:attribute type="xs:string" name="version" use="optional"/>\n'
        "        </xs:complexType>\n"
        "      </xs:element>\n"
        "    </xs:sequence>\n"
        "  </xs:complexType>\n"
        "</xs:element>\n"
        "</xs:schema>"
    )
    with caplog.at_level("INFO", logger="test_logger"):
        assert launcher.validate_xml_with_xsd(
            str(xml_path), str(xsd_path), logger=logger
        )
    assert "XML validation against XSD succeeded." in caplog.text


def test_extract_biobeamer_version():
    launcher = import_launcher()
    logger = launcher.get_logger("test_logger")
    host_entry = {"name": "foo", "version": "1.2.3"}
    assert launcher.extract_biobeamer_version(host_entry, logger=logger) == "1.2.3"
