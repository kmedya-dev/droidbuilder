import click
from .. import installer

@click.command()
@click.argument('tool_name')
@click.pass_context
def uninstall(ctx, tool_name):
    """Uninstall a specified tool (e.g., jdk-11)."""
    try:
        installer.uninstall_tool(tool_name)
    except Exception as e:
        logger.error(f"An error occurred during uninstallation: {e}")
        logger.info("Please check the log file for more details.")
