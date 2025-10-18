import os
import requests
import tarfile
import shutil
import subprocess
from . import config
from .cli_logger import logger
from .utils import download_and_extract, resolve_runtime_package

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")
DOWNLOAD_DIR = os.path.join(INSTALL_DIR, "downloads")


def download_python_source(version, verbose=False):
    """
    Downloads the Python source code for a given version.
    """
    logger.info(f"  - Downloading Python source code version {version}...")

    # If the version is a minor version, ask the user to specify the full version
    if len(version.split('.')) == 2:
        logger.error(f"Error: Please specify the full Python version in your droidbuilder.toml, e.g., {version}.0")
        return False

    python_url = f"https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    source_dir = os.path.join(INSTALL_DIR, "python-source")

    # Clean up previous source
    if os.path.exists(source_dir):
        try:
            shutil.rmtree(source_dir)
        except OSError as e:
            logger.error(f"Error cleaning up previous Python source directory {source_dir}: {e}")
            return False
    try:
        os.makedirs(source_dir)
    except OSError as e:
        logger.error(f"Error creating Python source directory {source_dir}: {e}")
        return False

    try:
        # Use download_and_extract from file_manager
        extracted_path = download_and_extract(python_url, source_dir, f"Python-{version}.tgz", verbose=verbose)
    except Exception as e:
        logger.error(f"Error downloading and extracting Python source: {e}")
        return False

    logger.info(f"  - Python source downloaded to {source_dir}")
    return source_dir


def download_and_extract_pypi_package(packages, download_path=DOWNLOAD_DIR, verbose=False):
    """
    Downloads and extracts a package from PyPI, respecting the specified version.
    """
    if "==" in packages:
        name, version = packages.split("==", 1)
    else:
        name, version = packages, None

    logger.info(f"  - Processing Python package: {name}{'==' + version if version else ' (latest)'}")
    
    try:
        url, resolved_version = resolve_runtime_package(name, version)
        if not url:
            return None

        file_name = os.path.basename(url)
        base_filename, _ = os.path.splitext(file_name)
        if base_filename.endswith(".tar"): # Handle .tar.gz, .tar.bz2, etc.
            base_filename, _ = os.path.splitext(base_filename)

        extract_dir = os.path.join(download_path, "sources", base_filename)

        # Use download_and_extract from file_manager
        extracted_path = download_and_extract(url, extract_dir, file_name, verbose=verbose)
        
        return extracted_path

    except Exception as e:
        logger.error(f"An unexpected error occurred while downloading and extracting {name}: {e}")
        return None


def download_buildtime_package(buildtime_package, download_path=DOWNLOAD_DIR, package_name=None, verbose=False):
    """
    Downloads a buildtime package from a direct URL.
    """
    logger.info(f"  - Downloading buildtime package from URL: {buildtime_package}...")

    filename = os.path.basename(buildtime_package)
    base_filename = filename
    known_extensions = [".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".zip"]
    for ext in known_extensions:
        if base_filename.endswith(ext):
            base_filename = base_filename[:-len(ext)]
            break
    else:
        base_filename, _ = os.path.splitext(base_filename)
    
    # Use provided package_name for extraction directory if available, otherwise use derived base_filename
    final_extract_name = package_name if package_name else base_filename
    extract_dir = os.path.join(download_path, "sources", final_extract_name)

    extracted_path = download_and_extract(buildtime_package, extract_dir, filename, verbose=verbose)

    return extracted_path


def download_from_url(url, download_path=DOWNLOAD_DIR, package_name=None, verbose=False):
    """
    Downloads a file from a direct URL and extracts it.
    """
    logger.info(f"  - Downloading from URL: {url}...")

    filename = os.path.basename(url)
    base_filename = filename
    known_extensions = [".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".zip"]
    for ext in known_extensions:
        if base_filename.endswith(ext):
            base_filename = base_filename[:-len(ext)]
            break
    else:
        base_filename, _ = os.path.splitext(base_filename)
    
    # Use provided package_name for extraction directory if available, otherwise use derived base_filename
    final_extract_name = package_name if package_name else base_filename
    extract_dir = os.path.join(download_path, "sources", final_extract_name)

    extracted_path = download_and_extract(url, extract_dir, filename, verbose=verbose)

    return extracted_path
