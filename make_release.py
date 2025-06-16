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

# Release output (now inside build/)
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
RELEASE_WIN = os.path.join(BUILD_DIR, "release-win")
RELEASE_LINUX = os.path.join(BUILD_DIR, "release-linux")

# Files to include (relative to scripts/)
WIN_FILES = ["uv.exe", "setup.bat", "start.bat"]
LINUX_FILES = ["uv", "setup.sh", "start.sh"]


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
        archive = os.path.join(BUILD_DIR, "BioBeamerLauncher-win.zip")
    else:
        release_dir = RELEASE_LINUX
        files = LINUX_FILES
        archive = os.path.join(BUILD_DIR, "BioBeamerLauncher-linux.tar.gz")

    clean_dir(release_dir)
    copy_files(files, SCRIPTS_DIR, release_dir)
    if os.path.exists(CONFIG_DIR):
        shutil.copytree(CONFIG_DIR, os.path.join(release_dir, "config"))
    if os.path.exists(README):
        shutil.copy(README, os.path.join(release_dir, "ReadMe.md"))
    if os.path.exists(LICENSE):
        shutil.copy(LICENSE, os.path.join(release_dir, "LICENSE"))
    # Set executable permissions for Linux
    if platform == "linux":
        for f in LINUX_FILES:
            set_executable(os.path.join(release_dir, f))
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
