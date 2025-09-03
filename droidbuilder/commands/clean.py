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
            try:
                shutil.rmtree(folder)
                logger.info(f"Removed {folder}")
            except OSError as e:
                logger.error(f"Error removing folder {folder}: {e}")
