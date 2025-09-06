import click
import os
from droidbuilder.cli_logger import logger

@click.command(name="list-files")
@click.pass_context
def list_files(ctx):
    """List files in the project directory."""
    path = ctx.obj["path"]
    abs_path = os.path.abspath(path)
    logger.info(f"Listing files in {abs_path}:")
    try:
        for item in os.listdir(abs_path):
            logger.info(item)
    except FileNotFoundError:
        logger.error(f"Error: Directory not found at {abs_path}. Please ensure the path is correct.")
    except PermissionError:
        logger.error(f"Error: Permission denied to access directory at {abs_path}. Please check your permissions.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while listing files in {abs_path}: {e}")
        logger.exception(*sys.exc_info())
