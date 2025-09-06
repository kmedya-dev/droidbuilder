import click
from .. import installer
from ..cli_logger import logger # Import logger

@click.command()
@click.argument('tool_name')
@click.pass_context
def search(ctx, tool_name):
    """Search for available versions of a specified tool (e.g., jdk)."""
    try:
        installer.search_tool(tool_name)
    except Exception as e:
        logger.error(f"An unexpected error occurred during search for '{tool_name}': {e}")
        logger.info("Please check the log file for more details and report this issue to the DroidBuilder developers if it persists.")
        logger.exception(*sys.exc_info())
