import click
from .. import installer
from ..cli_logger import logger # Import logger
import shutil
import os

@click.command()
@click.argument('tool_name')
@click.pass_context
def uninstall(ctx, tool_name):
    """Uninstall a specified tool (e.g., jdk-11) or all installed tools."""
    if tool_name.lower() == "python":
        tool_name = "python-source"

    if tool_name.lower() == "all":
        logger.info("Attempting to uninstall all DroidBuilder tools...")
        installed_tools = installer.list_installed_tools()
        all_successful = True
        
        tools_to_uninstall = []
        for ndk_version in installed_tools.get("android_ndk", []):
            tools_to_uninstall.append(f"ndk-{ndk_version}")

        if installed_tools.get("android_cmdline_tools"):
            tools_to_uninstall.append("android-sdk") # This covers cmdline tools and SDK packages

        for jdk_version in installed_tools.get("java_jdk", []):
            tools_to_uninstall.append(f"jdk-{jdk_version}")
        
        for gradle_version in installed_tools.get("gradle", []):
            tools_to_uninstall.append(f"gradle-{gradle_version}")
        
        tools_to_uninstall = list(dict.fromkeys(tools_to_uninstall))

        for tool in tools_to_uninstall:
            # Special handling for NDK
            if tool.startswith("ndk-"):
                logger.info(f"Attempting to uninstall {tool}...")
                ndk_version = tool.replace("ndk-", "")
                tool_path = os.path.join(installer.INSTALL_DIR, "android-sdk", "ndk", ndk_version)
                if os.path.exists(tool_path):
                    shutil.rmtree(tool_path)
                    logger.success(f"✓ {tool} has been successfully uninstalled.")
                else:
                    logger.info(f"{tool} not found.")
                continue

            # Fallback to generic uninstaller
            if not installer.uninstall_tool(tool):
                logger.error(f"Failed to uninstall {tool}.")
                all_successful = False
        
        if all_successful:
            logger.success("All DroidBuilder tools uninstalled successfully.")
        else:
            logger.error("Some DroidBuilder tools failed to uninstall. Please check the logs for details.")
    else:
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
