import os
import shutil
import zipfile
import tarfile
import stat

# Paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
README = os.path.join(PROJECT_ROOT, "ReadMe.md")
LICENSE = os.path.join(PROJECT_ROOT, "LICENSE")
DEBUGGING = os.path.join(PROJECT_ROOT, "DEBUGGING.md")

# Release output (now inside build/)
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
RELEASE_WIN = os.path.join(BUILD_DIR, "release-win")
RELEASE_LINUX = os.path.join(BUILD_DIR, "release-linux")

# Files to include (relative to scripts/)
WIN_FILES = ["setup.bat", "start.bat"]
LINUX_FILES = ["setup.sh", "start.sh"]

# UV binaries to include
WIN_UV = "uv.exe"
LINUX_UV = "uv"


# Utility functions
def clean_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def copy_files(files, src_dir, dst_dir):
    for f in files:
        shutil.copy(os.path.join(src_dir, f), os.path.join(dst_dir, f))


def make_zip(src_dir, out_file):
    with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, src_dir)
                zf.write(abs_path, rel_path)


def make_tar(src_dir, out_file):
    with tarfile.open(out_file, "w:gz") as tar:
        tar.add(src_dir, arcname=os.path.basename(src_dir))


def set_executable(path):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)


def prepare_release(platform):
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)
    if platform == "win":
        release_dir = RELEASE_WIN
        files = WIN_FILES
        uv_binary = WIN_UV
        archive = os.path.join(BUILD_DIR, "BioBeamerLauncher-win.zip")
    else:
        release_dir = RELEASE_LINUX
        files = LINUX_FILES
        uv_binary = LINUX_UV
        archive = os.path.join(BUILD_DIR, "BioBeamerLauncher-linux.tar.gz")

    clean_dir(release_dir)
    
    # Copy setup/start scripts
    copy_files(files, SCRIPTS_DIR, release_dir)
    
    # Create bin directory and copy uv
    bin_dir = os.path.join(release_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    uv_src = os.path.join(SCRIPTS_DIR, uv_binary)
    uv_dst = os.path.join(bin_dir, uv_binary)
    shutil.copy(uv_src, uv_dst)
    
    # Copy config and docs
    if os.path.exists(CONFIG_DIR):
        shutil.copytree(CONFIG_DIR, os.path.join(release_dir, "config"))
    
    # Create docs directory for documentation
    docs_dir = os.path.join(release_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    if os.path.exists(README):
        shutil.copy(README, os.path.join(docs_dir, "ReadMe.md"))
    if os.path.exists(LICENSE):
        shutil.copy(LICENSE, os.path.join(docs_dir, "LICENSE"))
    if os.path.exists(DEBUGGING):
        shutil.copy(DEBUGGING, os.path.join(docs_dir, "DEBUGGING.md"))
    
    # Create simple INSTALL.txt in root
    install_txt = os.path.join(release_dir, "INSTALL.txt")
    with open(install_txt, 'w') as f:
        f.write("BioBeamer Launcher Installation\n")
        f.write("===============================\n\n")
        if platform == "win":
            f.write("1. Run: setup.bat\n")
            f.write("2. Start: start.bat\n\n")
        else:
            f.write("1. Run: ./setup.sh\n")
            f.write("2. Start: ./start.sh\n\n")
        f.write("For more details, see docs/ReadMe.md\n")
    
    # Set executable permissions for Linux
    if platform == "linux":
        for f in LINUX_FILES:
            set_executable(os.path.join(release_dir, f))
        set_executable(uv_dst)
    
    # Archive
    if platform == "win":
        make_zip(release_dir, archive)
    else:
        make_tar(release_dir, archive)
    print(f"Created {archive}")


if __name__ == "__main__":
    prepare_release("win")
    prepare_release("linux")
    print("Release packages created.")
