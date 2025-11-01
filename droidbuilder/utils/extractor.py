import os
import zipfile
import tarfile
import shutil
import sys
import contextlib
import tempfile
from ..cli_logger import logger
from ..utils import move_files, safe_join


def _safe_extract_zip(zip_path, dest_dir, verbose=False):
    """Safely extract a zip file, preventing zip slip attacks."""
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        for member in zipf.infolist():
            extracted_path = safe_join(dest_dir, member.filename)
            if member.is_dir():
                logger.extraction(member.filename, indent=2, action="creating", verbose=verbose)
                os.makedirs(extracted_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(extracted_path), exist_ok=True)
                if os.path.exists(extracted_path):
                    logger.extraction(member.filename, indent=2, action="replace", verbose=verbose)
                else:
                    logger.extraction(member.filename, indent=2, action="extracting", verbose=verbose)
                zipf.extract(member, dest_dir)

def _safe_extract_tar(tar_path, dest_dir, verbose=False):
    """Safely extract a tar file, preventing path traversal attacks."""
    with tarfile.open(tar_path, 'r:*') as tarf:
        for member in tarf.getmembers():
            extracted_path = safe_join(dest_dir, member.name)
            if member.isdir():
                logger.extraction(member.name, indent=2, action="creating", verbose=verbose)
                os.makedirs(extracted_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(extracted_path), exist_ok=True)
                if os.path.exists(extracted_path):
                    logger.extraction(member.name, indent=2, action="replace", verbose=verbose)
                else:
                    logger.extraction(member.name, indent=2, action="extracting", verbose=verbose)
                tarf.extract(member, dest_dir)

def extract_file(archive_path, dest_dir, verbose=False):
    """Extracts an archive file to a destination directory."""
    logger.step_info(f"Archive:  {os.path.basename(archive_path)}")
    os.makedirs(dest_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            if zipfile.is_zipfile(archive_path):
                _safe_extract_zip(archive_path, temp_dir, verbose)
            elif tarfile.is_tarfile(archive_path):
                _safe_extract_tar(archive_path, temp_dir, verbose)
            else:
                logger.error(f"Unknown archive type for {archive_path}")
                return None

            # Move files from temp_dir to dest_dir and normalize structure
            move_files(temp_dir, dest_dir)

            logger.success(f"Successfully extracted to {dest_dir}")
            return dest_dir

        except (zipfile.BadZipFile, tarfile.TarError, IOError) as e:
            logger.error(f"Error during extraction: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during extraction: {e}")
            logger.exception(*sys.exc_info())
            return None

