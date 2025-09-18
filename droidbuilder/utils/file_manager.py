import os
import requests
import zipfile
import tarfile
import shutil
import sys
import contextlib
import subprocess
from ..cli_logger import logger

# -------------------- Helpers: safe paths & extraction --------------------

def _safe_join(base, *paths):
    """Safely join paths, preventing path traversal attacks."""
    base = os.path.abspath(base)
    final = os.path.abspath(os.path.join(base, *paths))
    if not final.startswith(base + os.sep) and final != base:
        raise IOError(f"Unsafe path detected: {final}")
    return final

def _safe_extract_zip(zip_ref: zipfile.ZipFile, dest_dir: str, log_each=True):
    """Safely extract a zip file, preventing zip slip attacks."""
    for member in zip_ref.infolist():
        # protect against zip slip
        target_path = _safe_join(dest_dir, member.filename)
        # logging like unzip
        if member.is_dir():
            if log_each:
                logger.step_info(f"creating: {member.filename}", indent=3)
            os.makedirs(target_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            if log_each:
                if os.path.exists(target_path):
                    logger.step_info(f" replace: {member.filename}", indent=2)
                else:
                    logger.step_info(f"extracting: {member.filename}", indent=2)
            with zip_ref.open(member, 'r') as src, open(target_path, 'wb') as out:
                shutil.copyfileobj(src, out)
            # Preserve file permissions
            mode = member.external_attr >> 16
            if mode:
                os.chmod(target_path, mode)

def _safe_extract_tar(tar_ref: tarfile.TarFile, dest_dir: str, log_each=True):
    """Safely extract a tar file, preventing path traversal attacks."""
    for member in tar_ref.getmembers():
        # deny absolute or parent traversal
        member_path = _safe_join(dest_dir, member.name)
        if member.isdir():
            if log_each:
                logger.step_info(f"creating: {member.name}", indent=3)
            os.makedirs(member_path, exist_ok=True)
            continue
        # ensure parent exists
        os.makedirs(os.path.dirname(member_path), exist_ok=True)
        if log_each:
            if os.path.exists(member_path):
                logger.step_info(f" replace: {member.name}", indent=2)
            else:
                logger.step_info(f"extracting: {member.name}", indent=2)
        src = tar_ref.extractfile(member)
        if src is None:
            # could be special file; skip silently
            continue
        with src as src_file: # Use a different variable name to avoid confusion
            with open(member_path, "wb") as out:
                shutil.copyfileobj(src_file, out)
            # Preserve file permissions
            if member.mode:
                os.chmod(member_path, member.mode)


def extract(filepath, dest_dir):
    """Extracts an archive file to a destination directory."""
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(filepath)

    try:
        if tarfile.is_tarfile(filepath):
            with tarfile.open(filepath, 'r:*') as tar:
                tar.extractall(path=dest_dir)
        elif zipfile.is_zipfile(filepath):
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(dest_dir)
        elif filename.endswith('.bz2'): # Added this condition
            with tarfile.open(filepath, 'r:bz2') as tar: # Try to open as bz2 compressed tar
                tar.extractall(path=dest_dir)
        else:
            logger.warning(f"Unsupported archive type for {filename}. Skipping extraction.")
            return None

        # Remove archive after successful extraction
        try:
            os.remove(filepath)
        except OSError:
            pass

        logger.success(f"Successfully extracted to {dest_dir}")
        return dest_dir

    except (zipfile.BadZipFile, tarfile.TarError, IOError) as e:
        logger.error(f"Error during extraction: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during extraction: {e}")
        logger.exception(*sys.exc_info())
        return None

# -------------------- Download & Extract --------------------

def download_and_extract(url, dest_dir, filename=None, timeout=60):
    """Download and extract a file to a destination directory."""
    os.makedirs(dest_dir, exist_ok=True)
    if filename is None:
        filename = url.split('/')[-1]
    filepath = os.path.join(dest_dir, filename)

    temp_filepath = filepath + ".tmp"

    try:
        # Ensure the directory for the temp file exists
        os.makedirs(os.path.dirname(temp_filepath), exist_ok=True) # Added this line

        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))

            with open(temp_filepath, 'wb') as f:
                chunks = logger.progress(
                    r.iter_content(chunk_size=1024 * 256),  # 256KB chunks
                    description=f"Downloading {filename}",
                    total=total_size,
                    unit="b"
                )
                for chunk in chunks:
                    if chunk:  # keep-alive chunks may be empty
                        f.write(chunk)

        # Atomic rename
        os.replace(temp_filepath, filepath)

        logger.step_info(f"Archive:  {filename}")

        return extract(filepath, dest_dir)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading the file: {e}")
        # cleanup temp
        with contextlib.suppress(Exception):
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.exception(*sys.exc_info())
        return None