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
        "host_name": config.get("config", "host_name", fallback=None),
        "log_dir": config.get("config", "log_dir", fallback=None),
        "password": config.get("config", "password", fallback=""),
    }
    logger.debug(f"Config values loaded: {config_dict}")
    return config_dict


def print_launcher_config(cfg: dict, logger: logging.Logger) -> None:
    msg = (
        "BioBeamerLauncher configuration:\n"
        f"  BioBeamer repo URL: {cfg['biobeamer_repo_url']}\n"
        f"  Config file path: {cfg['xml_file_path']}\n"
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
            f"Failed to checkout version {version}: {result.stderr.decode().strip()}"
        )
        return None

    return repo_path


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to launcher.ini config file")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print BioBeamer repo, venv, version, and recommended PyCharm interpreter path, then exit.",
    )
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


def find_uv_executable():
    """
    Find the uv executable to use for venv and pip commands.
    Order:
    1. UV_PATH env var
    2. uv in PATH
    3. scripts/uv relative to project root
    4. scripts/uv.exe (for Windows)
    """
    import shutil

    uv_env = os.environ.get("UV_PATH")
    if uv_env and os.path.isfile(uv_env) and os.access(uv_env, os.X_OK):
        return uv_env
    uv_in_path = shutil.which("uv")
    if uv_in_path:
        return uv_in_path
    # Try bundled scripts/uv
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    uv_script = os.path.join(project_root, "scripts", "uv")
    if os.path.isfile(uv_script) and os.access(uv_script, os.X_OK):
        return uv_script
    uv_script_win = os.path.join(project_root, "scripts", "uv.exe")
    if os.path.isfile(uv_script_win) and os.access(uv_script_win, os.X_OK):
        return uv_script_win
    raise FileNotFoundError(
        "Could not find 'uv' executable. Please ensure it is installed and available in your PATH, or set UV_PATH."
    )


def setup_biobeamer_venv(repo_path, version, logger):
    """
    Set up a virtual environment for the given BioBeamer version and install BioBeamer into it.
    Creates the venv if it doesn't exist, installs BioBeamer from the repo path.
    Returns the path to the venv's bin/Scripts directory.
    """
    cache_dir = get_cache_dir()
    venv_dir = os.path.join(cache_dir, f"BioBeamer-venv-{version}")
    venv_bin = os.path.join(venv_dir, "bin")
    venv_scripts = os.path.join(venv_dir, "Scripts")
    if platform.system() == "Windows":
        venv_python = os.path.join(venv_scripts, "python.exe")
        venv_biobeamer = os.path.join(venv_scripts, "biobeamer.exe")
    else:
        venv_python = os.path.join(venv_bin, "python")
        venv_biobeamer = os.path.join(venv_bin, "biobeamer")
    uv_exe = find_uv_executable()
    if not os.path.exists(venv_biobeamer):
        logger.info(
            f"Creating venv for BioBeamer version {version} at {venv_dir} using uv..."
        )
        # Create venv
        result = subprocess.run(
            [uv_exe, "venv", venv_dir],
            capture_output=True,
        )
        if result.returncode != 0:
            logger.error(f"Failed to create venv: {result.stderr.decode().strip()}")
            return None
        # Install BioBeamer from repo_path
        logger.info(f"Installing BioBeamer into venv from {repo_path}...")
        result = subprocess.run(
            [uv_exe, "pip", "install", "-e", repo_path],
            env={
                **os.environ,
                "VIRTUAL_ENV": venv_dir,
                "PATH": f"{venv_bin if platform.system() != 'Windows' else venv_scripts}:{os.environ.get('PATH','')}",
            },
            capture_output=True,
        )
        if result.returncode != 0:
            logger.error(
                f"Failed to install BioBeamer: {result.stderr.decode().strip()}"
            )
            return None
    else:
        logger.info(
            f"BioBeamer venv for version {version} already exists at {venv_dir}."
        )
    return venv_bin if platform.system() != "Windows" else venv_scripts


def run_biobeamer_process(repo_path, xml_path, cfg, log_dir, logger, version=None):
    # Use venv and run biobeamer entry point
    if version is None:
        logger.error("BioBeamer version not specified for venv setup.")
        return 12
    venv_bin = setup_biobeamer_venv(repo_path, version, logger)
    if not venv_bin:
        return 13
    if platform.system() == "Windows":
        biobeamer_exe = os.path.join(venv_bin, "biobeamer.exe")
    else:
        biobeamer_exe = os.path.join(venv_bin, "biobeamer")
    if not os.path.exists(biobeamer_exe):
        logger.error(f"BioBeamer entry point not found: {biobeamer_exe}")
        return 14
    biobeamer_log_file = os.path.join(
        log_dir, f"biobeamer_subprocess_{cfg['host_name']}.log"
    )
    cmd = [
        biobeamer_exe,
        "--xml",
        xml_path,
        "--hostname",
        cfg["host_name"],
        "--log_dir",
        log_dir,
        "--password",
        cfg["password"],
    ]
    logger.info(f"Running BioBeamer: {' '.join(cmd)}")
    try:
        with open(biobeamer_log_file, "w") as logf:
            result = subprocess.run(
                cmd, stdout=logf, stderr=subprocess.STDOUT, text=True
            )
        logger.info(f"BioBeamer subprocess log written to: {biobeamer_log_file}")
        if result.returncode != 0:
            logger.error(f"BioBeamer exited with code {result.returncode}")
            return result.returncode
        else:
            logger.info(
                f"BioBeamer subprocess finished; see subprocess log for output: {biobeamer_log_file}"
            )
            return 0
    except Exception as e:
        logger.exception(f"Failed to run BioBeamer: {e}")
        return 11  # nonzero error code


def run_launcher(cfg: dict, logger: logging.Logger, log_dir) -> int:
    print_launcher_config(cfg, logger=logger)
    xml_path = fetch_and_log_xml_config(cfg, logger)
    if not xml_path:
        return 20
    host_entry = select_host_entry(xml_path, cfg, logger)
    if not host_entry:
        return 23
    version = extract_and_log_version(host_entry, logger)
    if not version:
        return 24
    repo_path = prepare_biobeamer_repo(cfg, version, logger)
    if not repo_path:
        return 25
    return run_biobeamer_process(
        repo_path, xml_path, cfg, log_dir, logger, version=version
    )


def print_debug_info(cfg, logger):
    """
    Print BioBeamer repo path, venv path, version, and recommended PyCharm interpreter path.
    Actually sets up the repo and venv to ensure the paths are valid.
    """
    xml_path = fetch_xml_config(cfg["xml_file_path"], logger=logger)
    if not xml_path:
        logger.error("Could not fetch XML config file.")
        print("ERROR: Could not fetch XML config file.")
        return 1
    host_entry = parse_xml_and_select_host(xml_path, cfg["host_name"], logger=logger)
    if not host_entry:
        logger.error("Could not find host entry in XML.")
        print("ERROR: Could not find host entry in XML.")
        return 2
    version = extract_biobeamer_version(host_entry, logger=logger)
    if not version:
        logger.error("No BioBeamer version specified in host entry.")
        print("ERROR: No BioBeamer version specified in host entry.")
        return 3
    
    # Actually set up the repo and venv to ensure paths are valid
    repo_path = prepare_biobeamer_repo(cfg, version, logger)
    if not repo_path:
        logger.error("Failed to prepare BioBeamer repo.")
        print("ERROR: Failed to prepare BioBeamer repo.")
        return 4
    
    venv_bin = setup_biobeamer_venv(repo_path, version, logger)
    if not venv_bin:
        logger.error("Failed to set up BioBeamer venv.")
        print("ERROR: Failed to set up BioBeamer venv.")
        return 5
    
    cache_dir = get_cache_dir()
    venv_dir = os.path.join(cache_dir, f"BioBeamer-venv-{version}")
    if platform.system() == "Windows":
        python_path = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        python_path = os.path.join(venv_dir, "bin", "python")
    
    # Generate the exact biobeamer command arguments
    biobeamer_args = [
        "--xml", xml_path,
        "--hostname", cfg["host_name"],
        "--log_dir", cfg.get("log_dir", get_cache_dir()),
        "--password", cfg["password"]
    ]
    
    print("\n" + "="*60)
    print("BIOBEAMER DEBUG INFO")
    print("="*60)
    print(f"BioBeamer repo path:     {repo_path}")
    print(f"BioBeamer venv path:     {venv_dir}")
    print(f"BioBeamer version:       {version}")
    print(f"Python interpreter:      {python_path}")
    print(f"XML config path:         {xml_path}")
    print(f"Host name:               {cfg['host_name']}")
    print()
    print("EXACT COMMAND ARGUMENTS (copy-paste ready):")
    print("=" * 50)
    args_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in biobeamer_args)
    print(f"{args_str}")
    print()
    print("DEBUGGING SETUP:")
    print("=" * 20)
    print("1. IDE Setup:")
    print(f"   - Open project: {repo_path}")
    print(f"   - Set interpreter: {python_path}")
    print()
    print("2. Run Configuration:")
    print("   - Script: biobeamer (entry point)")
    print("   - Arguments: (copy from above)")
    print()
    print("3. Command Line Debug:")
    print(f"   source {venv_dir}/bin/activate")
    print(f"   biobeamer {args_str}")
    print()
    print("See DEBUGGING.md for detailed instructions.")
    print("="*60)
    return 0


def main() -> None:
    """Main entry point for BioBeamerLauncher."""
    args = parse_args()
    # Load config first, using a temporary logger (stderr only)
    temp_logger = get_logger("biobeamer_launcher_temp", logging.INFO, log_dir=None)
    cfg = load_config(args, temp_logger)
    if not cfg:
        temp_logger.error("Could not read launcher config.")
        sys.exit(30)
    log_dir = cfg["log_dir"] if cfg and cfg.get("log_dir") else get_cache_dir()
    # Now set up the real logger in the correct log_dir
    logger = setup_logger(log_dir)
    if getattr(args, "debug", False):
        exit_code = print_debug_info(cfg, logger)
        sys.exit(exit_code)
    exit_code = run_launcher(cfg, logger, log_dir)
    sys.exit(exit_code)


if __name__ == "__main__":

    main()
