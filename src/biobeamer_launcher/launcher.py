import configparser
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional
import urllib.request
import xml.etree.ElementTree as ET
import lxml.etree as LET
import logging
import argparse


def get_logger(name="biobeamer_launcher", level=logging.INFO):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
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


def read_launcher_config(config_path: str, logger=None) -> Optional[dict]:
    """Read the launcher.ini file and return config values as a dict, or None if not found."""
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        if logger:
            logger.error(f"Config file not found: {config_path}")
        else:
            print(f"Config file not found: {config_path}")
        return None
    config.read(config_path)
    return {
        "biobeamer_repo_url": config.get("config", "biobeamer_repo_url", fallback=None),
        "xml_file_path": config.get("config", "xml_file_path", fallback=None),
        "xsd_file_path": config.get("config", "xsd_file_path", fallback=None),
        "host_name": config.get("config", "host_name", fallback=None),
        "log_dir": config.get("config", "log_dir", fallback=None),
    }


def print_launcher_config(cfg: dict, logger=None):
    msg = (
        "BioBeamerLauncher configuration:\n"
        f"  BioBeamer repo URL: {cfg['biobeamer_repo_url']}\n"
        f"  Config file path: {cfg['xml_file_path']}\n"
        f"  XSD file path: {cfg['xsd_file_path']}\n"
        f"  Host name: {cfg['host_name']}"
    )
    if logger:
        logger.info(msg)
    else:
        print(msg)


def fetch_xml_config(xml_file_path: str, logger=None) -> str:
    """Fetch the XML config file from a local path or URL. Returns the local file path. Caches remote XML in cache dir."""
    cache_dir = get_cache_dir()
    os.makedirs(cache_dir, exist_ok=True)
    cache_xml_path = os.path.join(cache_dir, "BioBeamerConfig.xml")
    if xml_file_path.startswith(("http://", "https://", "ftp://")):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
                if logger:
                    logger.info(f"Downloading XML config from {xml_file_path}...")
                else:
                    print(f"Downloading XML config from {xml_file_path}...")
                urllib.request.urlretrieve(xml_file_path, tmp.name)
                if logger:
                    logger.info(f"Downloaded XML config to {tmp.name}")
                else:
                    print(f"Downloaded XML config to {tmp.name}")
                # Save a persistent copy in the cache
                shutil.copy(tmp.name, cache_xml_path)
                if logger:
                    logger.info(f"Cached XML config at {cache_xml_path}")
                else:
                    print(f"Cached XML config at {cache_xml_path}")
                return tmp.name
        except Exception as e:
            if logger:
                logger.warning(
                    f"Failed to fetch remote XML: {e}. Trying cached copy..."
                )
            else:
                print(f"Failed to fetch remote XML: {e}. Trying cached copy...")
            if os.path.exists(cache_xml_path):
                if logger:
                    logger.info(f"Using cached XML config: {cache_xml_path}")
                else:
                    print(f"Using cached XML config: {cache_xml_path}")
                return cache_xml_path
            else:
                if logger:
                    logger.error("No cached XML config available.")
                else:
                    print("No cached XML config available.")
                return None
    else:
        if not os.path.exists(xml_file_path):
            if logger:
                logger.error(f"Config file not found: {xml_file_path}")
            else:
                print(f"Config file not found: {xml_file_path}")
            # Try cache as fallback
            if os.path.exists(cache_xml_path):
                if logger:
                    logger.info(f"Using cached XML config: {cache_xml_path}")
                else:
                    print(f"Using cached XML config: {cache_xml_path}")
                return cache_xml_path
            return None
        if logger:
            logger.info(f"Using local XML config: {xml_file_path}")
        else:
            print(f"Using local XML config: {xml_file_path}")
        # Optionally update cache with local file
        shutil.copy(xml_file_path, cache_xml_path)
        return xml_file_path


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


def fetch_xsd_file(xsd_file_path: str, logger=None) -> str:
    """Fetch the XSD file from a local path or URL. Returns the local file path."""
    if not xsd_file_path:
        if logger:
            logger.error("No XSD file path provided in config.")
        else:
            print("No XSD file path provided in config.")
        return None
    if xsd_file_path.startswith(("http://", "https://", "ftp://")):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xsd") as tmp:
            if logger:
                logger.info(f"Downloading XSD from {xsd_file_path}...")
            else:
                print(f"Downloading XSD from {xsd_file_path}...")
            urllib.request.urlretrieve(xsd_file_path, tmp.name)
            if logger:
                logger.info(f"Downloaded XSD to {tmp.name}")
            else:
                print(f"Downloaded XSD to {tmp.name}")
            return tmp.name
    else:
        if not os.path.exists(xsd_file_path):
            if logger:
                logger.error(f"XSD file not found: {xsd_file_path}")
            else:
                print(f"XSD file not found: {xsd_file_path}")
            return None
        if logger:
            logger.info(f"Using local XSD: {xsd_file_path}")
        else:
            print(f"Using local XSD: {xsd_file_path}")
        return xsd_file_path


def parse_xml_and_select_host(xml_path: str, host_name: str, logger=None) -> dict:
    """Parse the XML config and return the host entry as a dict, or None if not found. Logs available host names if not found."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        found_hosts = []
        # Try direct children first
        for host in root.findall("host"):
            found_hosts.append(host.get("name"))
            if host.get("name") == host_name:
                if logger:
                    logger.info(f"Found host entry: {host_name}")
                else:
                    print(f"Found host entry: {host_name}")
                return host.attrib
        # Fallback: search at any depth
        for host in root.findall(".//host"):
            if host.get("name") not in found_hosts:
                found_hosts.append(host.get("name"))
            if host.get("name") == host_name:
                if logger:
                    logger.info(f"Found host entry (nested): {host_name}")
                else:
                    print(f"Found host entry (nested): {host_name}")
                return host.attrib
        if logger:
            logger.error(
                f"Host '{host_name}' not found in XML config. Available hosts: {found_hosts}"
            )
        else:
            print(
                f"Host '{host_name}' not found in XML config. Available hosts: {found_hosts}"
            )
        return None
    except Exception as e:
        if logger:
            logger.error(f"Error parsing XML: {e}")
        else:
            print(f"Error parsing XML: {e}")
        return None


def validate_xml_with_xsd(xml_path: str, xsd_path: str, logger=None) -> bool:
    """Validate the XML file against the XSD schema. Returns True if valid, False otherwise."""
    try:
        with open(xsd_path, "rb") as xsd_file:
            xsd_doc = LET.parse(xsd_file)
            schema = LET.XMLSchema(xsd_doc)
        with open(xml_path, "rb") as xml_file:
            xml_doc = LET.parse(xml_file)
        schema.assertValid(xml_doc)
        if logger:
            logger.info("XML validation against XSD succeeded.")
        else:
            print("XML validation against XSD succeeded.")
        return True
    except LET.DocumentInvalid as e:
        if logger:
            logger.error(f"XML validation error: {e}")
        else:
            print(f"XML validation error: {e}")
        return False
    except Exception as e:
        if logger:
            logger.error(f"Error during XML validation: {e}")
        else:
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


def setup_logging(log_dir=None):
    """Set up logging to both console and a file in the specified log_dir."""
    if log_dir is None:
        log_dir = get_cache_dir()
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "biobeamer_launcher.log")
    logger = logging.getLogger("biobeamer_launcher")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    # Remove existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to launcher.ini config file")
    args, unknown = parser.parse_known_args()
    if args.config:
        sys._launcher_config_override = args.config
    xml_config_path = get_xml_config_path()
    # Read config first to get log_dir
    cfg = read_launcher_config(xml_config_path)
    log_dir = cfg["log_dir"] if cfg and cfg.get("log_dir") else get_cache_dir()
    logger = setup_logging(log_dir)
    try:
        if not cfg:
            logger.error("Could not read launcher config.")
            return
        print_launcher_config(cfg)

        # Step 1: Fetch the XML config file (local or remote)
        xml_path = fetch_xml_config(cfg["xml_file_path"], logger=logger)
        if not xml_path:
            logger.error("Could not fetch XML config file.")
            return
        logger.info(f"XML config file path: {xml_path}")

        # Step 2: Fetch XSD file (local or remote)
        xsd_path = fetch_xsd_file(cfg["xsd_file_path"], logger=logger)
        if not xsd_path:
            logger.error("Could not fetch XSD file.")
            return
        logger.info(f"XSD file path: {xsd_path}")

        # Step 3: Validate XML against XSD
        if not validate_xml_with_xsd(xml_path, xsd_path, logger=logger):
            logger.error("XML validation failed. Exiting.")
            return
        logger.info("XML validation succeeded.")

        # Step 4: Parse XML and select host
        host_entry = parse_xml_and_select_host(
            xml_path, cfg["host_name"], logger=logger
        )
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
        # Step 7: Run BioBeamer2 main script with appropriate arguments
        biobeamer_script = os.path.join(repo_path, "src", "biobeamer2.py")
        if not os.path.exists(biobeamer_script):
            logger.error(f"BioBeamer script not found: {biobeamer_script}")
            return
        # Set up log file for subprocess in log_dir
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
            else:
                logger.info("BioBeamer finished successfully.")
        except Exception as e:
            logger.exception(f"Failed to run BioBeamer: {e}")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")


if __name__ == "__main__":

    main()
