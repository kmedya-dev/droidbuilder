import click
from .. import installer
from ..cli_logger import logger # Import logger

@click.command()
@click.argument('tool_name')
@click.pass_context
def update(ctx, tool_name):
    """Update a specified tool to the latest version (e.g., jdk)."""
    logger.info(f"Attempting to update '{tool_name}'...")
    try:
        if installer.update_tool(tool_name):
            logger.success(f"Successfully updated '{tool_name}'.")
        else:
            logger.error(f"Failed to update '{tool_name}'. Please check the logs for details.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during update of '{tool_name}': {e}")
        logger.info("Please check the log file for more details and report this issue to the DroidBuilder developers if it persists.")
        logger.exception(*sys.exc_info())
