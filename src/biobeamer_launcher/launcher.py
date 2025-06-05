import configparser
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import urllib.request
import xml.etree.ElementTree as ET
import lxml.etree as LET
import logging


def get_xml_config_path() -> str:
    """Return the absolute path to the launcher.ini config file (renamed for clarity)."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "launcher.ini",
    )


def read_launcher_config(config_path: str) -> Optional[dict]:
    """Read the launcher.ini file and return config values as a dict, or None if not found."""
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        return None
    config.read(config_path)
    return {
        "biobeamer_repo_url": config.get("config", "biobeamer_repo_url", fallback=None),
        "config_file_path": config.get("config", "config_file_path", fallback=None),
        "xsd_file_path": config.get("config", "xsd_file_path", fallback=None),
        "host_name": config.get("config", "host_name", fallback=None),
    }


def print_launcher_config(cfg: dict):
    print("BioBeamerLauncher configuration:")
    print(f"  BioBeamer repo URL: {cfg['biobeamer_repo_url']}")
    print(f"  Config file path: {cfg['config_file_path']}")
    print(f"  XSD file path: {cfg['xsd_file_path']}")
    print(f"  Host name: {cfg['host_name']}")


def fetch_xml_config(config_file_path: str) -> str:
    """Fetch the XML config file from a local path or URL. Returns the local file path."""
    if config_file_path.startswith(("http://", "https://", "ftp://")):
        # Download to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
            print(f"Downloading XML config from {config_file_path}...")
            urllib.request.urlretrieve(config_file_path, tmp.name)
            print(f"Downloaded XML config to {tmp.name}")
            return tmp.name
    else:
        # Local file path
        if not os.path.exists(config_file_path):
            print(f"Config file not found: {config_file_path}")
            return None
        print(f"Using local XML config: {config_file_path}")
        return config_file_path


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


def fetch_xsd_file(xsd_file_path: str) -> str:
    """Fetch the XSD file from a local path or URL. Returns the local file path."""
    if not xsd_file_path:
        print("No XSD file path provided in config.")
        return None
    if xsd_file_path.startswith(("http://", "https://", "ftp://")):
        # Download to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xsd") as tmp:
            print(f"Downloading XSD from {xsd_file_path}...")
            urllib.request.urlretrieve(xsd_file_path, tmp.name)
            print(f"Downloaded XSD to {tmp.name}")
            return tmp.name
    else:
        # Local file path
        if not os.path.exists(xsd_file_path):
            print(f"XSD file not found: {xsd_file_path}")
            return None
        print(f"Using local XSD: {xsd_file_path}")
        return xsd_file_path


def parse_xml_and_select_host(xml_path: str, host_name: str) -> dict:
    """Parse the XML config and return the host entry as a dict, or None if not found."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for host in root.findall("host"):
            if host.get("name") == host_name:
                print(f"Found host entry: {host_name}")
                return host.attrib
        print(f"Host '{host_name}' not found in XML config.")
        return None
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return None


def validate_xml_with_xsd(xml_path: str, xsd_path: str) -> bool:
    """Validate the XML file against the XSD schema. Returns True if valid, False otherwise."""
    try:
        with open(xsd_path, "rb") as xsd_file:
            xsd_doc = LET.parse(xsd_file)
            schema = LET.XMLSchema(xsd_doc)
        with open(xml_path, "rb") as xml_file:
            xml_doc = LET.parse(xml_file)
        schema.assertValid(xml_doc)
        print("XML validation against XSD succeeded.")
        return True
    except LET.DocumentInvalid as e:
        print(f"XML validation error: {e}")
        return False
    except Exception as e:
        print(f"Error during XML validation: {e}")
        return False


def extract_biobeamer_version(host_entry: dict) -> str:
    """Extract the BioBeamer version from the host entry, if present."""
    return host_entry.get("version")


def fetch_or_update_biobeamer_repo(
    repo_url: str, version: str, cache_dir: str, logger: logging.Logger = None
) -> Optional[str]:
    """Clone or update the BioBeamer repo and checkout the specified version (tag or branch). Returns the repo path or None on failure."""
    log = logger.info if logger else print
    log_err = logger.error if logger else print
    if not repo_url or not version:
        log_err("BioBeamer repo URL or version not specified.")
        return None
    repo_path = os.path.join(cache_dir, "BioBeamer")
    if not os.path.exists(repo_path):
        log(f"Cloning BioBeamer repo from {repo_url} to {repo_path}...")
        result = subprocess.run(
            ["git", "clone", repo_url, repo_path], capture_output=True
        )
        if result.returncode != 0:
            log_err(f"Failed to clone BioBeamer repo: {result.stderr.decode().strip()}")
            return None
    else:
        log(f"Updating existing BioBeamer repo at {repo_path}...")
        result = subprocess.run(
            ["git", "-C", repo_path, "fetch", "--all"], capture_output=True
        )
        if result.returncode != 0:
            log_err(f"Failed to fetch updates: {result.stderr.decode().strip()}")
            return None
    # Try to checkout the version as a tag or branch
    log(f"Checking out BioBeamer version: {version}")
    result = subprocess.run(
        ["git", "-C", repo_path, "checkout", version], capture_output=True
    )
    if result.returncode != 0:
        log_err(
            f"Failed to checkout version '{version}': {result.stderr.decode().strip()}"
        )
        return None
    log(f"BioBeamer repo ready at: {repo_path} (version: {version})")
    return repo_path


def setup_logging():
    """Set up logging to both console and a file in the cache dir."""
    cache_dir = get_cache_dir()
    os.makedirs(cache_dir, exist_ok=True)
    log_file = os.path.join(cache_dir, "biobeamer_launcher.log")
    logger = logging.getLogger("biobeamer_launcher")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def main():
    logger = setup_logging()
    try:
        xml_config_path = get_xml_config_path()
        cfg = read_launcher_config(xml_config_path)
        if not cfg:
            logger.error("Could not read launcher config.")
            return
        print_launcher_config(cfg)

        # Step 1: Fetch the XML config file (local or remote)
        xml_path = fetch_xml_config(cfg["config_file_path"])
        if not xml_path:
            logger.error("Could not fetch XML config file.")
            return
        logger.info(f"XML config file path: {xml_path}")

        # Step 2: Fetch XSD file (local or remote)
        xsd_path = fetch_xsd_file(cfg["xsd_file_path"])
        if not xsd_path:
            logger.error("Could not fetch XSD file.")
            return
        logger.info(f"XSD file path: {xsd_path}")

        # Step 3: Validate XML against XSD
        if not validate_xml_with_xsd(xml_path, xsd_path):
            logger.error("XML validation failed. Exiting.")
            return
        logger.info("XML validation succeeded.")

        # Step 4: Parse XML and select host
        host_entry = parse_xml_and_select_host(xml_path, cfg["host_name"])
        if not host_entry:
            logger.error("Could not find host entry in XML.")
            return
        logger.info(f"Selected host entry: {host_entry}")

        # Step 5: Extract BioBeamer version
        version = extract_biobeamer_version(host_entry)
        if version:
            logger.info(f"BioBeamer version specified in host entry: {version}")
        else:
            logger.error("No BioBeamer version specified in host entry.")
            return
        # Step 6: Fetch or update BioBeamer repo and checkout version
        cache_dir = get_cache_dir()
        repo_path = fetch_or_update_biobeamer_repo(
            cfg["biobeamer_repo_url"], version, cache_dir, logger=logger
        )
        if not repo_path:
            logger.error("Failed to prepare BioBeamer repo.")
            return
        # logger.info(f"BioBeamer repo ready at: {repo_path}")  # Already logged in function
        # Next: run BioBeamer from repo_path
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")


if __name__ == "__main__":
    main()
