import os
import shutil
from ..cli_logger import logger
from ..utils import download, extract_file
from ..constants import MWD



def install(url, dest_dir, filename=None, timeout=60, verbose=False):
    """Download and extract a file to a destination directory."""
    archive_path = download(url, filename, timeout)
    if not archive_path:
        return None

    try:
        return extract_file(archive_path, dest_dir, verbose=verbose)
    finally:
        # Clean up the downloaded file
        if archive_path and os.path.exists(archive_path):
            os.remove(archive_path)
