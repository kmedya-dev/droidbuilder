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

    if installed_tools["android_sdk"]:
        logger.info("Android SDK:")
        for version in installed_tools["android_sdk"]:
            logger.info(f"  - {version}")
    else:
        logger.info("Android SDK: Not installed")

    if installed_tools["android_ndk"]:
        logger.info("Android NDK:")
        for version in installed_tools["android_ndk"]:
            logger.info(f"  - {version}")
    else:
        logger.info("Android NDK: Not installed")

    if installed_tools["java_jdk"]:
        logger.info("Java JDK:")
        for version in installed_tools["java_jdk"]:
            logger.info(f"  - {version}")
    else:
        logger.info("Java JDK: Not installed")

    if installed_tools["gradle"]:
        logger.info("Gradle:")
        for version in installed_tools["gradle"]:
            logger.info(f"  - {version}")
    else:
        logger.info("Gradle: Not installed")

    if installed_tools["android_cmdline_tools"]:
        logger.info("Android Command-line Tools: Installed")
    else:
        logger.info("Android Command-line Tools: Not installed")
