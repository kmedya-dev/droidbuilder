import click
from .. import installer
from ..cli_logger import logger

@click.command(name="list-tools")
@click.pass_context
def list_tools(ctx):
    """List all installed tools (SDK, NDK, JDK versions)."""
    logger.info("Listing installed tools...")
    installed_tools = installer.list_installed_tools()
    if not installed_tools:
        logger.info("No tools installed yet. Run 'droidbuilder install-tools' to begin.")
        return

    for tool, versions in installed_tools.items():
        if versions:
            logger.info(f"{tool.replace('_', ' ').title()}:")
            for version in versions:
                logger.info(f"  - {version}")
        else:
            logger.info(f"{tool.replace('_', ' ').title()}: Not installed")
