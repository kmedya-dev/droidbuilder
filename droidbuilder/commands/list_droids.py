import click
from .. import toolchain
from ..cli_logger import logger

@click.command(name="list-droids")
@click.pass_context
def list_droids(ctx):
    """List all installed droids."""
    logger.info("Listing installed droids...")
    installed_droids = toolchain.list_installed_droids()
    if not installed_droids:
        logger.info("No droids installed yet.")
        return

    logger.info("Installed droids:")
    for droid in installed_droids:
        logger.info(f"  - {droid}")
