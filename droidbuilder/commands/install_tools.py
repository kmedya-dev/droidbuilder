import click
import sys
from .. import config as config_module
from .. import installer
from ..cli_logger import logger

@click.command()
@click.pass_context
def install_tools(ctx):
    """Install required SDK, NDK, and JDK versions."""
    logger.info("Installing DroidBuilder tools...")
    conf = None
    try:
        conf = config_module.load_config(path=ctx.obj["path"])
        if not conf:
            logger.error("Error: No droidbuilder.toml found in the current directory or specified path.")
            logger.info("Please run 'droidbuilder init' to create a new project configuration.")
            return False
    except FileNotFoundError:
        logger.error("Error: droidbuilder.toml not found. Please ensure you are in the correct project directory or specify the path.")
        logger.info("Run 'droidbuilder init' to create a new project configuration.")
        return False
    except Exception as e:
        logger.error(f"Error loading droidbuilder.toml: {e}")
        logger.info("Please check the file's format and permissions.")
        return False
    
    try:
        if installer.setup_tools(conf):
            logger.success("Tool installation complete.")
            return True
        else:
            logger.error("Tool installation failed. Please check the logs for details.")
            return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during tool installation: {e}")
        logger.info("Please check the log file for more details and report this issue to the DroidBuilder developers if it persists.")
        logger.exception(*sys.exc_info())
        return False
