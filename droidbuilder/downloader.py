import os
import requests
import tarfile
import shutil
import subprocess
from .cli_logger import logger
from . import config
from .utils.file_manager import download_and_extract
from .utils.python_package import resolve_python_package

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")


def download_python_source(version):
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
        extracted_path = download_and_extract(python_url, source_dir, f"Python-{version}.tgz")
    except Exception as e:
        logger.error(f"Error downloading and extracting Python source: {e}")
        return False

    # The archive extracts to a directory like 'Python-3.9.13'. We want to move the contents up.
    extracted_dir = os.path.join(source_dir, f"Python-{version}")
    if os.path.isdir(extracted_dir):
        try:
            # Move contents up
            for item in os.listdir(extracted_dir):
                shutil.move(os.path.join(extracted_dir, item), source_dir)
            os.rmdir(extracted_dir)
        except (shutil.Error, OSError) as e:
            logger.error(f"Error moving or cleaning up Python source files: {e}")
            return False

    # Verify that configure script exists
    if not os.path.exists(os.path.join(source_dir, "configure")):
        logger.error("Error: 'configure' script not found in Python source. The download or extraction might have failed.")
        return False

    logger.info(f"  - Python source downloaded to {source_dir}")
    return source_dir


def download_pypi_package(req, download_path="."):
    """
    Downloads a package from PyPI, respecting the specified version.
    """
    if "==" in req:
        package_name, version = req.split("==", 1)
    else:
        package_name = req
        version = None

    logger.info(f"  - Processing Python package: {package_name}{'==' + version if version else ' (latest)'}")
    
    try: # Added try block
        url, resolved_version = resolve_python_package(package_name, version)
        if not url:
            return None

        file_name = os.path.basename(url)
        file_path = os.path.join(download_path, file_name)

        logger.info(f"  - Downloading {url} to {file_path}")

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return file_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {package_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while downloading {package_name}: {e}")
        return None


def download_system_package(url, download_path="."):
    """
    Downloads a system package from a direct URL.
    """
    logger.info(f"  - Downloading system package from URL: {url}...")
    
    filename = os.path.basename(url)
    extract_dir = os.path.join(download_path, "sources", filename.split('.')[0]) # Use filename for extract dir
    
    extracted_path = download_and_extract(url, extract_dir, filename)

    logger.info(f"Extracted to: {extracted_path}")
    return extracted_path


def download_from_url(url, download_path="."):
    """
    Downloads a file from a direct URL and extracts it.
    """
    logger.info(f"  - Downloading from URL: {url}...")
    
    filename = os.path.basename(url)
    extract_dir = os.path.join(download_path, "sources", filename.split('.')[0])

    extracted_path = download_and_extract(url, extract_dir, filename)
    
    return extracted_path