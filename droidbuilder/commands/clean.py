import click
import shutil
import os
import sys
import glob
from ..cli_logger import logger

@click.command()
@click.pass_context
def clean(ctx):
    """Remove build artifacts and cache files."""
    logger.info("Cleaning build artifacts, temporary files, and cache...")

    dir_patterns = [
        "build",
        "dist",
        ".droidbuilder",
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