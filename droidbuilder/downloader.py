import os
import requests
import tarfile
import shutil
import subprocess
from . import config
from .cli_logger import logger
from .utils import download_and_extract, resolve_runtime_package, resolve_buildtime_package

DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder", "downloads")

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

        try:

            source_dir = os.path.join(DOWNLOAD_DIR, "python-source")

            extract_path = download_and_extract(python_url, source_dir, verbose=verbose)

            return os.path.join(extract_path, f"Python-{version}")

        except Exception as e:

            logger.error(f"Error downloading Python-{version}: {e}")

            return None

def download_runtime_package(name, version, verbose=False):
    """
    Downloads and extracts a package from PyPI, respecting the specified version.
    """
    logger.info(f"  - Processing Python package: {name}{'==' + version if version else ' (latest)'}")
    """package_spec = f"{name}=={version}" if version else name
    url, resolved_version = resolve_runtime_package(package_spec)"""

    if not url:
        logger.error(f"Could not resolve runtime package {name}")
        return None

    try:
        source_dir = os.path.join(DOWNLOAD_DIR, "runtime_packages_src", name)

        # Extract the downloaded file
        extract_path = download_and_extract(url, source_dir, verbose=verbose)
        return extract_path

    except Exception as e:
        logger.error(f"Error downloading runtime package {name}: {e}")
        return None


def download_buildtime_package(name, version, dependency_mapping, verbose=False):
    """
    Downloads a buildtime package from a direct URL.
    """
    logger.info(f"  - Downloading buildtime package {name} from URL: {url}...")
    """package_spec = f"{name}=={version}" if version else name
    resolved_info = resolve_buildtime_package(package_spec, dependency_mapping)"""

    if not resolved_info or name not in resolved_info:
        logger.error(f"Could not resolve buildtime package {name}")
        return None

    """url = resolved_info[name]["url"]"""

    try:
        source_dir = os.path.join(DOWNLOAD_DIR, "buildtime_packages_src", name)

        # Extract the downloaded file
        extract_path = download_and_extract(url, source_dir, verbose=verbose)
        return extract_path

    except Exception as e:
        logger.error(f"Error downloading buildtime package {name}: {e}")
        return None

def download_from_url(url, package_name=None, verbose=False):
    """
    Downloads a file from a direct URL and extracts it.
    """
    logger.info(f"  - Downloading from URL: {url}...")

    base_filename = url.split('/')[-1].split('.')[0]
    # Use provided package_name for extraction directory if available, otherwise use derived base_filename
    final_extract_name = package_name if package_name else base_filename
    source_dir = os.path.join(DOWNLOAD_DIR, "sources", final_extract_name)

    download_and_extract(url, source_dir, verbose=verbose)
    return source_dir

