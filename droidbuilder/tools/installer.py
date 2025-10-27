import os
import shutil
from ..cli_logger import logger
from ..utils import download, extract_file

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")

def install(url, dest_dir, filename=None, timeout=60, verbose=False):
    """Download and extract a file to a destination directory."""
    download_path = download(url, dest_dir, filename, timeout)
    if not download_path:
        return None

    try:
        result = extract_file(download_path, dest_dir, verbose)
        return result
    finally:
        # Clean up the downloaded file and its temporary directory
        download_dir = os.path.dirname(download_path)
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)
