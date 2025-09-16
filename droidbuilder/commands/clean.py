import click
import shutil
import os
import sys
import glob
from ..import config
from ..cli_logger import logger
from ..builder import BUILD_DIR, INSTALL_DIR
from .. import downloader
from ..downloader import DOWNLOAD_DIR

EXCLUDE_PREFIXES = {"android-sdk", "gradle-", "jdk-"} #skip those, because those are handled by "droidbuilder/commands/uninstall.py"

@click.command()
@click.pass_context
def clean(ctx):
    """Remove build artifacts and cache files."""
    logger.info("Cleaning build artifacts, temporary files, and cache...")

    dir_patterns = [
        "build",
        "dist",
	".droidbuilder/**",
        BUILD_DIR + "/**", # Add the global build directory	
        DOWNLOAD_DIR + "/**", # Add the global download directory
        ".pytest_cache",
        ".ruff_cache",
        "**/*.egg-info",
        "**/__pycache__",
        "htmlcov",
        ".tox",
        ".mypy_cache",
        "**/.gradle",
        "captures",
        "gen",
        "out",
        "obj",
    ]

    file_patterns = [
        "**/*.pyc", "**/*.pyo", "**/*.pyd",
        "**/*.so",
        "**/*.log",
        ".coverage",
        "**/*.cover",
        "**/*.apk",
        "**/*.aab",
        "**/.DS_Store",
        "**/Thumbs.db",
        "**/desktop.ini",
        "**/*~",
        "**/*.swp",
    ]

    items_removed = 0

    for pattern in dir_patterns:
        for path in glob.glob(pattern, recursive=True):
            if os.path.isdir(path):
                # Check if the directory is in the EXCLUDE_DIRS list
                if any(os.path.basename(path).startswith(prefix) for prefix in EXCLUDE_PREFIXES):
                    logger.info(f"Skipping excluded directory: {path}")
                    continue

                logger.info(f"Attempting to remove directory {path}...")
                try:
                    shutil.rmtree(path)
                    logger.success(f"Removed directory {path}")
                    items_removed += 1
                except OSError as e:
                    logger.error(f"Error removing directory {path}: {e}")
                    # logger.info("Please check file permissions and ensure the directory is not in use.")
                except Exception as e:
                    logger.error(f"An unexpected error occurred while removing {path}: {e}")
                    logger.exception(*sys.exc_info())

    # New loop to clean contents of INSTALL_DIR, respecting EXCLUDE_DIRS
    if os.path.exists(INSTALL_DIR) and os.path.isdir(INSTALL_DIR):
        for item in os.listdir(INSTALL_DIR):
            path = os.path.join(INSTALL_DIR, item)
            if os.path.isdir(path):
                # logger.debug(f"Checking path for exclusion: {path}, basename: {os.path.basename(path)}")
                if any(os.path.basename(path).startswith(prefix) for prefix in EXCLUDE_PREFIXES):
                    # logger.info(f"Skipping excluded directory: {path}")
                    continue

                logger.info(f"Attempting to remove directory {path}...")
                try:
                    shutil.rmtree(path)
                    logger.success(f"Removed directory {path}")
                    items_removed += 1
                except OSError as e:
                    logger.error(f"Error removing directory {path}: {e}")
                    logger.info("Please check file permissions and ensure the directory is not in use.")
                except Exception as e:
                    logger.error(f"An unexpected error occurred while removing {path}: {e}")
                    logger.exception(*sys.exc_info())

    for pattern in file_patterns:
        for path in glob.glob(pattern, recursive=True):
            if os.path.isfile(path):
                logger.info(f"Attempting to remove file {path}...")
                try:
                    os.remove(path)
                    logger.success(f"Removed file {path}")
                    items_removed += 1
                except OSError as e:
                    logger.error(f"Error removing file {path}: {e}")
                    logger.info("Please check file permissions and ensure the file is not in use.")
                except Exception as e:
                    logger.error(f"An unexpected error occurred while removing {path}: {e}")
                    logger.exception(*sys.exc_info())

    if items_removed > 0:
        logger.success(f"Cleaning complete. Removed {items_removed} items.")
    else:
        logger.info("Project is already clean.")
