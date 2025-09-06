import click
from .. import installer
from ..cli_logger import logger # Import logger

@click.command()
@click.argument('tool_name')
@click.pass_context
def uninstall(ctx, tool_name):
    """Uninstall a specified tool (e.g., jdk-11)."""
    logger.info(f"Attempting to uninstall '{tool_name}'...")
    try:
        if installer.uninstall_tool(tool_name):
            logger.success(f"Successfully uninstalled '{tool_name}'.")
        else:
            logger.error(f"Failed to uninstall '{tool_name}'. Please check the logs for details.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during uninstallation of '{tool_name}': {e}")
        logger.info("Please check the log file for more details and report this issue to the DroidBuilder developers if it persists.")
        logger.exception(*sys.exc_info())
