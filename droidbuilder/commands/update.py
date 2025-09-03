import click
from .. import installer

@click.command()
@click.argument('tool_name')
@click.pass_context
def update(ctx, tool_name):
    """Update a specified tool to the latest version (e.g., jdk)."""
    try:
        installer.update_tool(tool_name)
    except Exception as e:
        logger.error(f"An error occurred during update: {e}")
        logger.info("Please check the log file for more details.")
