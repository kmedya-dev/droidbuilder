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

def is_within_directory(directory, target):
    """
    Check if a target path is safely within a given directory.
    This is a security measure to prevent path traversal attacks.
    """
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    prefix = os.path.commonprefix([abs_directory, abs_target])
    return prefix == abs_directory

# -------------------- Helpers: safe paths & extraction --------------------

def _safe_join(directory, filename):
    """Safely join paths, preventing path traversal attacks."""
    target_path = os.path.join(directory, filename)
    if not is_within_directory(directory, target_path):
        raise PermissionError(f"Path traversal attempt detected: {filename}")
    return target_path

def _safe_extract_zip(archive_path, extract_to, log_each=True, verbose=False):
    """Safely extract a zip file, preventing zip slip attacks."""
    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            target_path = _safe_join(extract_to, member.filename)
            if member.is_dir():
                os.makedirs(target_path, exist_ok=True)
            else:
                if log_each and verbose:
                    logger.step_info(f"Extracting {member.filename}")
                zip_ref.extract(member, path=extract_to)

def _safe_extract_tar(archive_path, extract_to, log_each=True, verbose=False):
    """Safely extract a tar file, preventing path traversal attacks."""
    with tarfile.open(archive_path, 'r:*') as tar_ref:
        for member in tar_ref.getmembers():
            target_path = _safe_join(extract_to, member.name)
            if member.isdir():
                os.makedirs(target_path, exist_ok=True)
            else:
                if log_each and verbose:
                    logger.step_info(f"Extracting {member.name}")
                tar_ref.extract(member, path=extract_to)

def _move_extracted_files(extract_to):
    """Move extracted files, normalizing the directory structure."""
    extracted_items = os.listdir(extract_to)
    if len(extracted_items) == 1:
        inner_dir = os.path.join(extract_to, extracted_items[0])
        if os.path.isdir(inner_dir):
            # Move contents of the single inner directory to the parent
            for item in os.listdir(inner_dir):
                shutil.move(os.path.join(inner_dir, item), extract_to)
            os.rmdir(inner_dir)
            return True
    return False

def extract(archive_path, extract_to, verbose=False):
    """Extracts an archive file to a destination directory."""
    os.makedirs(extract_to, exist_ok=True)
    logger.step_info(f"Extracting {os.path.basename(archive_path)} to {extract_to}")

    if archive_path.endswith('.zip'):
        _safe_extract_zip(archive_path, extract_to, verbose=verbose)
    elif archive_path.endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar.xz', '.txz')):
        _safe_extract_tar(archive_path, extract_to, verbose=verbose)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")

    if _move_extracted_files(extract_to):
        logger.step_info("Normalized directory structure.")

    logger.success(f"Successfully extracted to {extract_to}")
    return extract_to

# -------------------- Download & Extract --------------------

def download_and_extract(url, dest_dir, filename=None, timeout=60, verbose=False):
    """Download and extract a file to a destination directory."""
    if not filename:
        filename = url.split('/')[-1]

    download_path = os.path.join(dest_dir, filename)
    os.makedirs(dest_dir, exist_ok=True)

    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(download_path, 'wb') as f:
                chunks = logger.progress(
                    r.iter_content(chunk_size=1024 * 256),  # 256KB chunks
                    description=f"Downloading {filename}",
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                )
                for chunk in chunks:
                    f.write(chunk)

        logger.step_info(f"Archive:  {filename}")
        extract(download_path, dest_dir, verbose=verbose)

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        sys.exit(1)
    finally:
        if os.path.exists(download_path):
            os.remove(download_path)
