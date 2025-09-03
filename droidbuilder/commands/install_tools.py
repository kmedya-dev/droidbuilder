import click
from .. import config as config_module
from .. import installer
from ..cli_logger import logger

@click.command()
@click.pass_context
def install_tools(ctx):
    """Install required SDK, NDK, and JDK versions."""
    logger.info("Installing DroidBuilder tools...")
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return
    try:
        installer.setup_tools(conf)
        logger.success("Tool installation complete.")
    except Exception as e:
        logger.error(f"An error occurred during tool installation: {e}")
        logger.info("Please check the log file for more details.")
