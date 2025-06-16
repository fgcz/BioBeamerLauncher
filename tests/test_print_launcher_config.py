import os
import tempfile
import shutil
import importlib.util
from io import StringIO
import sys
import pytest


def test_print_launcher_config_prints_expected(monkeypatch, tmp_path):
    # Prepare a minimal config dict
    cfg = {
        "biobeamer_repo_url": "https://example.com/repo.git",
        "xml_file_path": "configs/BioBeamerTest.xml",
        "xsd_file_path": "configs/BioBeamer2.xsd",
        "host_name": "testhost",
    }
    # Import the launcher module from the real source
    src_dir = os.path.join(os.path.dirname(__file__), "..", "src", "biobeamer_launcher")
    launcher_path = os.path.abspath(os.path.join(src_dir, "launcher.py"))
    spec = importlib.util.spec_from_file_location("launcher", launcher_path)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    logger = launcher.get_logger("test_logger")
    # Capture log output
    import logging
    from io import StringIO

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger.addHandler(handler)
    launcher.print_launcher_config(cfg, logger=logger)
    logger.removeHandler(handler)
    output = log_stream.getvalue()
    assert "BioBeamerLauncher configuration:" in output
    assert "BioBeamer repo URL: https://example.com/repo.git" in output
    assert "Config file path: configs/BioBeamerTest.xml" in output
    assert "Host name: testhost" in output
