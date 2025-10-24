import os
import requests
import zipfile
import tarfile
import shutil
import sys
import contextlib
import subprocess
import hashlib
from ..cli_logger import logger

# -------------------- Hashing Utilities --------------------

def hash_file(file_path, algorithm='sha256'):
    """Compute the hash of a file."""
    h = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def verify_hash(file_path, expected_hash, algorithm='sha256'):
    """Verify the hash of a file."""
    return hash_file(file_path, algorithm) == expected_hash

# -------------------- Path Helpers --------------------

def _safe_join(base, *paths):
    """Safely join paths, preventing path traversal attacks."""
    path = os.path.realpath(os.path.join(base, *paths))
    base = os.path.realpath(base)
    if os.path.commonprefix((path, base)) != base:
        raise PermissionError("Path traversal attempt detected")
    return path

def _log_and_create_dir_for_extraction(name, target_path, is_dir, log_each, verbose):
    """Helper to log extraction progress and create directories."""
    if is_dir:
        if log_each:
            logger.step_info(f"creating: {name}", indent=3, overwrite=True, verbose=verbose)
        os.makedirs(target_path, exist_ok=True)
    else:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        if log_each:
            if os.path.exists(target_path):
                logger.step_info(f" replace: {name}", indent=2, overwrite=True, verbose=verbose)
            else:
                logger.step_info(f"extracting: {name}", indent=2, overwrite=True, verbose=verbose)

def _safe_extract_zip(zip_path, dest_dir, log_each=True, verbose=False):
    """Safely extract a zip file, preventing zip slip attacks."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            target_path = _safe_join(dest_dir, member.filename)
            _log_and_create_dir_for_extraction(member.filename, target_path, member.is_dir(), log_each, verbose)

            if not member.is_dir():
                # Extract the file
                with open(target_path, "wb") as f:
                    f.write(zip_ref.read(member.filename))

def _safe_extract_tar(tar_path, dest_dir, log_each=True, verbose=False):
    """Safely extract a tar file, preventing path traversal attacks."""
    with tarfile.open(tar_path, 'r:*') as tar_ref:
        for member in tar_ref.getmembers():
            target_path = _safe_join(dest_dir, member.name)
            _log_and_create_dir_for_extraction(member.name, target_path, member.isdir(), log_each, verbose)

            if member.isfile():
                # Extract the file
                with tar_ref.extractfile(member) as source_file:
                    with open(target_path, "wb") as dest_file:
                        shutil.copyfileobj(source_file, dest_file)


def _move_extracted_files(dest_dir):
    """Move extracted files, normalizing the directory structure."""
    extracted_items = os.listdir(dest_dir)
    if len(extracted_items) == 1:
        inner_dir = os.path.join(dest_dir, extracted_items[0])
        if os.path.isdir(inner_dir):
            for item in os.listdir(inner_dir):
                shutil.move(os.path.join(inner_dir, item), dest_dir)
            os.rmdir(inner_dir)


def extract(archive_path, dest_dir, verbose=False):
    """Extracts an archive file to a destination directory."""
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(archive_path)
    temp_dir = dest_dir + ".tmp"

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    try:
        if archive_path.endswith('.zip'):
            _safe_extract_zip(archive_path, temp_dir, verbose=verbose)
        elif archive_path.endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar.xz', '.txz')):
            _safe_extract_tar(archive_path, temp_dir, verbose=verbose)
        else:
            raise ValueError(f"Unsupported archive format: {archive_path}")

        _move_extracted_files(temp_dir) # Move from temp_dir to dest_dir if single top-level dir

        # Move all contents from temp_dir to dest_dir
        for item in os.listdir(temp_dir):
            shutil.move(os.path.join(temp_dir, item), dest_dir)

        logger.success(f"Successfully extracted to {dest_dir}")
        with contextlib.suppress(OSError):
            os.remove(archive_path) # Remove archive after successful extraction
        return dest_dir # Return the destination directory on success

    except (zipfile.BadZipFile, tarfile.TarError, IOError) as e:
        logger.error(f"Error during extraction: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during extraction: {e}")
        logger.exception(*sys.exc_info())
        return None
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


# -------------------- Download & Extract --------------------

def download_and_extract(url, dest_dir, filename=None, timeout=60, verbose=False):
    """Download and extract a file to a destination directory."""
    # Create a temporary directory for the download
    download_dir = dest_dir + ".download.tmp"

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
                    r.iter_content(chunk_size=1024 * 256),  # 256KB chunks
                    description=f"Downloading {filename}",
                    total=total_size,
                    unit="b",
                )
                for chunk in chunks:
                    if chunk:  # keep-alive chunks may be empty
                        f.write(chunk)

        logger.step_info(f"Archive:  {filename}")
        extract(download_path, dest_dir, verbose=verbose)
        shutil.rmtree(download_dir) # Clean up download directory after successful extraction
        return dest_dir # Return the destination directory on success
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading the file: {e}")
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir) # Clean up download directory on download error
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.exception(*sys.exc_info())
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir) # Clean up download directory on extraction error
        return None
