import click
import importlib.metadata
from ..cli_logger import logger

@click.command()
def version():
    """Print the version of the DroidBuilder tool."""
    try:
        ver = importlib.metadata.version("droidbuilder")
        logger.info(f"DroidBuilder version {ver}")
    except importlib.metadata.PackageNotFoundError:
        logger.error("Error: Could not determine the version of DroidBuilder.")
