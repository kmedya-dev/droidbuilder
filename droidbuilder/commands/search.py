import click
from .. import installer

@click.command()
@click.argument('tool_name')
@click.pass_context
def search(ctx, tool_name):
    """Search for available versions of a specified tool (e.g., jdk)."""
    try:
        installer.search_tool(tool_name)
    except Exception as e:
        logger.error(f"An error occurred during search: {e}")
        logger.info("Please check the log file for more details.")
