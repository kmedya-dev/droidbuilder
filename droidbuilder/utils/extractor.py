import os
import zipfile
import tarfile
import shutil
import sys
import contextlib
from ..cli_logger import logger
from ..utils import safe_join

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
            target_path = safe_join(dest_dir, member.filename)
            _log_and_create_dir_for_extraction(member.filename, target_path, member.is_dir(), log_each, verbose)

            if not member.is_dir():
                with open(target_path, "wb") as f:
                    f.write(zip_ref.read(member.filename))

def _safe_extract_tar(tar_path, dest_dir, log_each=True, verbose=False):
    """Safely extract a tar file, preventing path traversal attacks."""
    with tarfile.open(tar_path, 'r:*') as tar_ref:
        for member in tar_ref.getmembers():
            target_path = safe_join(dest_dir, member.name)
            _log_and_create_dir_for_extraction(member.name, target_path, member.isdir(), log_each, verbose)

            if member.isfile():
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


def extract_file(archive_path, dest_dir, verbose=False):
    """Extracts an archive file to a destination directory."""
    logger.step_info(f"Archive:  {os.path.basename(archive_path)}")
    os.makedirs(dest_dir, exist_ok=True)
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

        _move_extracted_files(temp_dir)

        for item in os.listdir(temp_dir):
            shutil.move(os.path.join(temp_dir, item), dest_dir)

        logger.success(f"Successfully extracted to {dest_dir}")
        return dest_dir

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
