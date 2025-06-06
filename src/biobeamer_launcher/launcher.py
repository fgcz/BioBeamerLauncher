import argparse
import configparser
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from typing import Optional

import lxml.etree as LET


def get_logger(
    name: str = "biobeamer_launcher",
    level: int = logging.INFO,
    log_dir: Optional[str] = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{name}.log")
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger


def get_xml_config_path() -> str:
    """Return the absolute path to the launcher.ini config file, allowing override by env or CLI."""
    # 1. Check CLI arg (set in main)
    if hasattr(sys, "_launcher_config_override") and sys._launcher_config_override:
        return sys._launcher_config_override
    # 2. Check env var
    env_path = os.environ.get("BIOBEAMER_LAUNCHER_CONFIG")
    if env_path:
        return env_path
    # 3. Default: look in <project-root>/config/launcher.ini, where project root is two levels above this file
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "config", "launcher.ini")


def read_launcher_config(config_path: str, logger: logging.Logger) -> Optional[dict]:
    """Read the launcher.ini file and return config values as a dict, or None if not found."""
    logger.debug(f"Attempting to read launcher config from: {config_path}")
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        return None
    config.read(config_path)
    logger.info(f"Successfully read config file: {config_path}")
    config_dict = {
        "biobeamer_repo_url": config.get("config", "biobeamer_repo_url", fallback=None),
        "xml_file_path": config.get("config", "xml_file_path", fallback=None),
        "xsd_file_path": config.get("config", "xsd_file_path", fallback=None),
        "host_name": config.get("config", "host_name", fallback=None),
        "log_dir": config.get("config", "log_dir", fallback=None),
    }
    logger.debug(f"Config values loaded: {config_dict}")
    return config_dict


def print_launcher_config(cfg: dict, logger: logging.Logger) -> None:
    msg = (
        "BioBeamerLauncher configuration:\n"
        f"  BioBeamer repo URL: {cfg['biobeamer_repo_url']}\n"
        f"  Config file path: {cfg['xml_file_path']}\n"
        f"  XSD file path: {cfg['xsd_file_path']}\n"
        f"  Host name: {cfg['host_name']}"
    )
    logger.info(msg)


def fetch_xml_config(xml_file_path: str, logger: logging.Logger) -> Optional[str]:
    """Fetch the XML config file from a local path or URL. Returns the local file path or None on failure. Caches remote XML in cache dir."""
    cache_dir = get_cache_dir()
    os.makedirs(cache_dir, exist_ok=True)
    cache_xml_path = os.path.join(cache_dir, "BioBeamerConfig.xml")
    if xml_file_path.startswith(("http://", "https://", "ftp://")):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
                logger.info(f"Downloading XML config from {xml_file_path}...")
                urllib.request.urlretrieve(xml_file_path, tmp.name)
                logger.info(f"Downloaded XML config to {tmp.name}")
                # Save a persistent copy in the cache
                shutil.copy(tmp.name, cache_xml_path)
                logger.info(f"Cached XML config at {cache_xml_path}")
                return tmp.name
        except Exception as e:
            logger.warning(f"Failed to fetch remote XML: {e}. Trying cached copy...")
            if os.path.exists(cache_xml_path):
                logger.info(f"Using cached XML config: {cache_xml_path}")
                return cache_xml_path
            else:
                logger.error("No cached XML config available.")
                return None
    else:
        # Local file path
        if os.path.exists(xml_file_path):
            logger.info(f"Using local XML config: {xml_file_path}")
            return xml_file_path
        else:
            logger.error(f"Local XML config not found: {xml_file_path}")
            return None


def get_cache_dir() -> str:
    """Return a platform-independent cache directory for the config repo, honoring BIOBEAMER_LAUNCHER_CACHE_DIR env var if set."""
    env_cache_dir = os.environ.get("BIOBEAMER_LAUNCHER_CACHE_DIR")
    if env_cache_dir:
        return env_cache_dir
    try:
        from platformdirs import user_cache_dir

        return user_cache_dir("biobeamer_launcher", "BioBeamer")
    except ImportError:
        # Fallback: ~/.cache/biobeamer_launcher (Linux), %LOCALAPPDATA%\biobeamer_launcher (Windows)
        if platform.system() == "Windows":
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                return os.path.join(
                    local_appdata, "biobeamer_launcher", "BioBeamerConfig"
                )
            else:
                return os.path.expanduser(r"~\\biobeamer_launcher\\BioBeamerConfig")
        else:
            return os.path.expanduser("~/.cache/biobeamer_launcher/BioBeamerConfig")


def fetch_xsd_file(xsd_file_path: str, logger: logging.Logger) -> Optional[str]:
    """Fetch the XSD file from a local path or URL. Returns the local file path or None on failure."""
    if not xsd_file_path:
        logger.error("No XSD file path provided in config.")
        return None
    if xsd_file_path.startswith(("http://", "https://", "ftp://")):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xsd") as tmp:
            logger.info(f"Downloading XSD from {xsd_file_path}...")
            urllib.request.urlretrieve(xsd_file_path, tmp.name)
            logger.info(f"Downloaded XSD to {tmp.name}")
            return tmp.name
    else:
        if not os.path.exists(xsd_file_path):
            logger.error(f"XSD file not found: {xsd_file_path}")
            return None
        logger.info(f"Using local XSD: {xsd_file_path}")
        return xsd_file_path


def parse_xml_and_select_host(
    xml_path: str, host_name: str, logger: logging.Logger
) -> Optional[dict]:
    """Parse the XML config and return the host entry as a dict, or None if not found. Logs available host names if not found."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        found_hosts = []
        # Try direct children first
        for host in root.findall("host"):
            found_hosts.append(host.get("name"))
            if host.get("name") == host_name:
                logger.info(f"Found host entry: {host_name}")
                return host.attrib
        # Fallback: search at any depth
        for host in root.findall(".//host"):
            if host.get("name") not in found_hosts:
                found_hosts.append(host.get("name"))
            if host.get("name") == host_name:
                logger.info(f"Found host entry (nested): {host_name}")
                return host.attrib
        logger.error(
            f"Host '{host_name}' not found in XML config. Available hosts: {found_hosts}"
        )
        return None
    except Exception as e:
        logger.error(f"Error parsing XML: {e}")
        return None


def validate_xml_with_xsd(xml_path: str, xsd_path: str, logger: logging.Logger) -> bool:
    """Validate the XML file against the XSD schema. Returns True if valid, False otherwise."""
    try:
        with open(xsd_path, "rb") as xsd_file:
            xsd_doc = LET.parse(xsd_file)
            schema = LET.XMLSchema(xsd_doc)
        with open(xml_path, "rb") as xml_file:
            xml_doc = LET.parse(xml_file)
        schema.assertValid(xml_doc)
        logger.info("XML validation against XSD succeeded.")
        return True
    except LET.DocumentInvalid as e:
        logger.error(f"XML validation error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during XML validation: {e}")
        return False


def extract_biobeamer_version(
    host_entry: dict, logger: logging.Logger
) -> Optional[str]:
    """Extract the BioBeamer version from the host entry, if present."""
    version = host_entry.get("version")
    if version:
        logger.info(f"Extracted BioBeamer version: {version}")
    else:
        logger.error("No BioBeamer version found in host entry.")
    return version


def fetch_or_update_biobeamer_repo(
    repo_url: str, version: str, cache_dir: str, logger: logging.Logger
) -> Optional[str]:
    """Clone or update the BioBeamer repo and checkout the specified version (tag or branch). Returns the repo path or None on failure."""
    if not repo_url or not version:
        logger.error("BioBeamer repo URL or version not specified.")
        return None
    repo_path = os.path.join(cache_dir, "BioBeamer")
    if not os.path.exists(repo_path):
        logger.info(f"Cloning BioBeamer repo from {repo_url} to {repo_path}...")
        result = subprocess.run(
            ["git", "clone", repo_url, repo_path], capture_output=True
        )
        if result.returncode != 0:
            logger.error(
                f"Failed to clone BioBeamer repo: {result.stderr.decode().strip()}"
            )
            return None
    else:
        logger.info(f"Updating existing BioBeamer repo at {repo_path}...")
        result = subprocess.run(
            ["git", "-C", repo_path, "fetch", "--all"], capture_output=True
        )
        if result.returncode != 0:
            logger.error(f"Failed to fetch updates: {result.stderr.decode().strip()}")
            return None
    # Try to checkout the version as a tag or branch
    logger.info(f"Checking out BioBeamer version: {version}")
    result = subprocess.run(
        ["git", "-C", repo_path, "checkout", version], capture_output=True
    )
    if result.returncode != 0:
        logger.error(
            f"Failed to checkout version '{version}': {result.stderr.decode().strip()}"
        )
        return None
    logger.info(f"BioBeamer repo ready at: {repo_path} (version: {version})")
    return repo_path


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to launcher.ini config file")
    args, unknown = parser.parse_known_args()
    return args


def setup_logger(log_dir: str) -> logging.Logger:
    """Set up and return a logger."""
    return get_logger("biobeamer_launcher", logging.INFO, log_dir=log_dir)


def load_config(args, logger: logging.Logger) -> Optional[dict]:
    """Load the launcher config, possibly using CLI override."""
    if args.config:
        sys._launcher_config_override = args.config
    xml_config_path = get_xml_config_path()
    cfg = read_launcher_config(xml_config_path, logger=logger)
    return cfg


def fetch_and_log_xml_config(cfg, logger):
    xml_path = fetch_xml_config(cfg["xml_file_path"], logger=logger)
    if not xml_path:
        logger.error("Could not fetch XML config file.")
        return None
    logger.info(f"XML config file path: {xml_path}")
    return xml_path


def fetch_and_log_xsd_file(cfg, logger):
    xsd_path = fetch_xsd_file(cfg["xsd_file_path"], logger=logger)
    if not xsd_path:
        logger.error("Could not fetch XSD file.")
        return None
    logger.info(f"XSD file path: {xsd_path}")
    return xsd_path


def validate_xml_config(xml_path, xsd_path, logger):
    if not validate_xml_with_xsd(xml_path, xsd_path, logger=logger):
        logger.error("XML validation failed. Exiting.")
        return False
    logger.info("XML validation succeeded.")
    return True


def select_host_entry(xml_path, cfg, logger):
    host_entry = parse_xml_and_select_host(xml_path, cfg["host_name"], logger=logger)
    if not host_entry:
        logger.error("Could not find host entry in XML.")
        return None
    logger.info(f"Selected host entry: {host_entry}")
    return host_entry


def extract_and_log_version(host_entry, logger):
    version = extract_biobeamer_version(host_entry, logger=logger)
    if version:
        logger.info(f"BioBeamer version specified in host entry: {version}")
    else:
        logger.error("No BioBeamer version specified in host entry.")
    return version


def prepare_biobeamer_repo(cfg, version, logger):
    cache_dir = get_cache_dir()
    repo_path = fetch_or_update_biobeamer_repo(
        cfg["biobeamer_repo_url"], version, cache_dir, logger=logger
    )
    if not repo_path:
        logger.error("Failed to prepare BioBeamer repo.")
        return None
    return repo_path


def run_biobeamer_process(repo_path, xml_path, xsd_path, cfg, log_dir, logger):
    biobeamer_script = os.path.join(repo_path, "src", "biobeamer2.py")
    if not os.path.exists(biobeamer_script):
        logger.error(f"BioBeamer script not found: {biobeamer_script}")
        return 10  # nonzero error code
    biobeamer_log_file = os.path.join(log_dir, f"biobeamer_{cfg['host_name']}.log")
    cmd = [
        sys.executable,
        biobeamer_script,
        "--xml",
        xml_path,
        "--xsd",
        xsd_path,
        "--hostname",
        cfg["host_name"],
        "--log_dir",
        log_dir,
    ]
    logger.info(f"Running BioBeamer: {' '.join(cmd)}")
    try:
        with open(biobeamer_log_file, "w") as logf:
            result = subprocess.run(
                cmd, stdout=logf, stderr=subprocess.STDOUT, text=True
            )
        logger.info(f"BioBeamer log written to: {biobeamer_log_file}")
        if result.returncode != 0:
            logger.error(f"BioBeamer exited with code {result.returncode}")
            return result.returncode
        else:
            logger.info("BioBeamer finished successfully.")
            return 0
    except Exception as e:
        logger.exception(f"Failed to run BioBeamer: {e}")
        return 11  # nonzero error code


def run_launcher(cfg: dict, logger: logging.Logger, log_dir) -> int:
    print_launcher_config(cfg, logger=logger)
    xml_path = fetch_and_log_xml_config(cfg, logger)
    if not xml_path:
        return 20
    xsd_path = fetch_and_log_xsd_file(cfg, logger)
    if not xsd_path:
        return 21
    if not validate_xml_config(xml_path, xsd_path, logger):
        return 22
    host_entry = select_host_entry(xml_path, cfg, logger)
    if not host_entry:
        return 23
    version = extract_and_log_version(host_entry, logger)
    if not version:
        return 24
    repo_path = prepare_biobeamer_repo(cfg, version, logger)
    if not repo_path:
        return 25
    return run_biobeamer_process(repo_path, xml_path, xsd_path, cfg, log_dir, logger)


def main() -> None:
    """Main entry point for BioBeamerLauncher."""
    args = parse_args()
    default_log_dir = get_cache_dir()
    logger = setup_logger(default_log_dir)
    cfg = load_config(args, logger)
    log_dir = cfg["log_dir"] if cfg and cfg.get("log_dir") else get_cache_dir()
    # If log_dir from config is different, re-initialize logger
    if log_dir != default_log_dir:
        logger = setup_logger(log_dir)
    if not cfg:
        logger.error("Could not read launcher config.")
        sys.exit(30)
    exit_code = run_launcher(cfg, logger, log_dir)
    sys.exit(exit_code)


if __name__ == "__main__":

    main()
