import os
import requests
import tarfile
import shutil
import subprocess
from .cli_logger import logger
from . import config
from . import utils
from . import dependencies

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")

# This maps a dependency name to its GitHub owner/repo.
REPO_MAPPING = {
    "openssl": "openssl/openssl",
    "xz": "tukaani-project/xz",
}


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


def _get_tarball_url(release, owner, repo, tag_name):
    """
    Finds the tarball URL from a release's assets or falls back to the
    auto-generated source archive.
    """
    for asset in release.get("assets", []):
        if asset["name"].endswith(".tar.gz"):
            logger.info(f"  - Found release asset: {asset['name']}")
            return asset["browser_download_url"]

    fallback_url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{tag_name}.tar.gz"
    logger.info(f"  - No .tar.gz asset found, falling back to source archive: {fallback_url}")
    return fallback_url


def _get_latest_release_tag(owner, repo):
    """Fetches the latest release to get its tag_name."""
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    logger.info(f"  - Fetching latest release from {url}")
    response = requests.get(url)
    response.raise_for_status()
    release = response.json()
    logger.info(f"  - Found latest tag: {release['tag_name']}")
    return release["tag_name"], release


def _find_release_tag_by_version(owner, repo, version):
    """Scans all releases to find a tag that ends with the given version."""
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    logger.info(f"  - Fetching all releases from {url} to find version '{version}'")
    response = requests.get(url)
    response.raise_for_status()
    releases = response.json()

    for release in releases:
        tag_name = release["tag_name"]
        if tag_name.endswith(version):
            logger.info(f"  - Found matching tag '{tag_name}' for version '{version}'")
            return tag_name, release

    raise ValueError(f"Version '{version}' not found for '{owner}/{repo}'")


def download_system_package(name, version, download_path="."):
    """Downloads a system package from GitHub."""
    logger.info(f"  - Downloading system package {name}{'==' + version if version else ' (latest)'}...")

    try:
        owner, repo = REPO_MAPPING[name].split("/")
        release_info = None
        tag_name = None

        if version:
            tag_name, release_info = _find_release_tag_by_version(owner, repo, version)
        else:
            tag_name, release_info = _get_latest_release_tag(owner, repo)

        if not tag_name:
            logger.error(f"Error: Could not resolve a tag for {name}")
            return None

        url = _get_tarball_url(release_info, owner, repo, tag_name)

        # Use a descriptive filename
        filename = f"{name}-{version or 'latest'}.tar.gz"

        extracted_path = utils.download_and_extract(url, download_path, filename)
        return extracted_path

    except KeyError:
        logger.error(f"Error: No repository mapping found for '{name}'.")
        return None
    except (requests.HTTPError, ValueError) as e:
        logger.error(f"Error: Failed to process {name}. Details: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing {name}. Details: {e}")
        return None
