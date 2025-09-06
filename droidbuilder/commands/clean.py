import click
import shutil
import os
from ..cli_logger import logger

@click.command()
@click.pass_context
def clean(ctx):
    """Remove build, dist, and temp files."""
    for folder in ["build", "dist", ".droidbuilder"]:
        if os.path.exists(folder):
            logger.info(f"Attempting to remove {folder}...")
            try:
                shutil.rmtree(folder)
                logger.success(f"Removed {folder}")
            except OSError as e:
                logger.error(f"Error removing folder {folder}: {e}")
                logger.info("Please check file permissions and ensure the directory is not in use.")
            except Exception as e:
                logger.error(f"An unexpected error occurred while removing {folder}: {e}")
                logger.exception(*sys.exc_info())
