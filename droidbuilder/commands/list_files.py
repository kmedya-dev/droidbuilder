import click
import os
from droidbuilder.cli_logger import logger

@click.command(name="list-files")
@click.pass_context
def list_files(ctx):
    """List files in the project directory."""
    path = ctx.obj["path"]
    logger.info(f"Listing files in {os.path.abspath(path)}:")
    try:
        for item in os.listdir(path):
            logger.info(item)
    except FileNotFoundError:
        logger.error(f"Error: Directory not found at {os.path.abspath(path)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
