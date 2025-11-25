import os
import requests
import shutil
from ..cli_logger import logger

from ..constants import DOWNLOAD_DIR

def download(url, filename=None, timeout=60):
    """Download a file to a temporary directory and return the path."""
    download_dir = DOWNLOAD_DIR

    if not filename:
        filename = url.split('/')[-1]
    download_path = os.path.join(download_dir, filename)

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(download_path, 'wb') as f:
                chunks = logger.progress(
                    r.iter_content(chunk_size=1024 * 256),
                    description=f"Downloading {filename}",
                    total=total_size,
                    unit="b",
                )
                for chunk in chunks:
                    if chunk:
                        f.write(chunk)
        return download_path
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading the file: {e}")
        if os.path.exists(download_path):
            os.remove(download_path)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during download: {e}")
        if os.path.exists(download_path):
            os.remove(download_path)
        return None
