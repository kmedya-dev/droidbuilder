import os
import requests
import tarfile
import shutil
import subprocess
from .cli_logger import logger
from . import config
from . import utils

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
        extracted_path = utils.download_and_extract(python_url, source_dir, f"Python-{version}.tgz")
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
    pypi_url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = requests.get(pypi_url)
        response.raise_for_status()
        package_data = response.json()

        if version is None:
            version = package_data["info"]["version"]
            logger.info(f"  - No version specified for {package_name}. Found latest: {version}")

        release = package_data.get("releases", {}).get(version)
        if not release:
            logger.error(f"Could not find version {version} for {package_name} on PyPI.")
            return None

        # Find the source distribution (tar.gz)
        source_dist = None
        for dist in release:
            if dist["packagetype"] == "sdist":
                source_dist = dist
                break

        if not source_dist:
            logger.error(f"Could not find source distribution (sdist) for {package_name} {version}")
            return None

        download_url = source_dist["url"]
        file_name = source_dist["filename"]
        file_path = os.path.join(download_path, file_name)

        logger.info(f"  - Downloading {download_url} to {file_path}")

        with requests.get(download_url, stream=True) as r:
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



def download_system_package(package_name, download_path="."):
    """
    Downloads a system package using Repology API.
    """
    logger.info(f"  - Downloading system package {package_name}...")
    api_url = f"https://repology.org/api/v1/project/{package_name}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        if not data:
            logger.error(f"No data found for package '{package_name}' on Repology.")
            return None

        # Find latest stable version and its srcurl
        latest_stable = None
        for pkg in data:
            if pkg.get("status") == "newest":
                latest_stable = pkg
                break
        
        if not latest_stable:
            logger.error(f"Could not find a 'newest' stable release for '{package_name}' on Repology.")
            return None

        srcurls = latest_stable.get("srcurls")
        if srcurls:
            url = srcurls[0]
        else:
            homepage = latest_stable.get("homepage")
            if homepage:
                url = homepage
            else:
                logger.error(f"No srcurls or homepage found for '{package_name}'.")
                return None
        
        # Make sure the url is a tarball
        if not (url.endswith(".tar.gz") or url.endswith(".tar.xz")):
            logger.error(f"URL is not a tarball: {url}")
            return None

        filename = os.path.basename(url)
        extract_dir = os.path.join(download_path, "sources", package_name)
        
        logger.info(f"Resolved URL: {url}")
        
        extracted_path = utils.download_and_extract(url, extract_dir, filename)

        logger.info(f"Extracted to: {extracted_path}")
        return extracted_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Repology API for '{package_name}': {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing '{package_name}': {e}")
        return None


