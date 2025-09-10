import os
import requests
import tarfile
import shutil
from .cli_logger import logger
from . import config
from . import utils
from . import dependencies

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


def download_pypi_package(package_name, download_path="."):
    """
    Downloads a package from PyPI.
    """
    pypi_url = f"https://pypi.org/pypi/{package_name}/json"
    
    try:
        response = requests.get(pypi_url)
        response.raise_for_status()
        package_data = response.json()
        
        latest_version = package_data["info"]["version"]
        logger.info(f"Found latest version of {package_name}: {latest_version}")
        
        release = package_data["releases"][latest_version]
        
        # Find the source distribution (tar.gz)
        source_dist = None
        for dist in release:
            if dist["packagetype"] == "sdist":
                source_dist = dist
                break
        
        if not source_dist:
            logger.error(f"Could not find source distribution for {package_name} {latest_version}")
            return None
            
        download_url = source_dist["url"]
        file_name = source_dist["filename"]
        file_path = os.path.join(download_path, file_name)
        
        logger.info(f"Downloading {download_url} to {file_path}")
        
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        return file_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {package_name}: {e}")
        return None

def download_github_package(repo_name, download_path="."):
    """
    Downloads a package from GitHub.
    """
    github_api_url = f"https://api.github.com/repos/{repo_name}/releases"
    
    try:
        response = requests.get(github_api_url)
        response.raise_for_status()
        releases_data = response.json()
        
        if not releases_data:
            logger.error(f"No releases found for {repo_name}")
            return None

        # Sort releases by published_at date
        releases_data.sort(key=lambda r: r["published_at"], reverse=True)
        latest_release = releases_data[0]
        
        tag_name = latest_release["tag_name"]
        logger.info(f"Found latest release of {repo_name}: {tag_name}")
        
        tarball_url = latest_release["tarball_url"]
        file_name = f"{repo_name.split('/')[-1]}-{tag_name}.tar.gz"
        file_path = os.path.join(download_path, file_name)
        
        logger.info(f"Downloading {tarball_url} to {file_path}")
        
        with requests.get(tarball_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        return file_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {repo_name}: {e}")
        return None
