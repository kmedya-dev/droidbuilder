
import click
import os
import subprocess
from .. import installer
from ..cli_logger import logger

@click.command(name="search-packages")
@click.argument("query", required=False)
@click.pass_context
def search_packages(ctx, query):
    """Search for available SDK packages."""
    logger.info("Searching for SDK packages...")

    sdk_install_dir = os.path.join(installer.INSTALL_DIR, "android-sdk")
    sdk_manager = installer._get_sdk_manager(sdk_install_dir)

    if not sdk_manager:
        logger.error("SDK manager not found. Please run 'droidbuilder install-tools' first.")
        return

    try:
        result = subprocess.run(
            [sdk_manager, "--list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.splitlines()
        
        if query:
            logger.info(f"Filtering results for '{query}':")
            for line in lines:
                if query.lower() in line.lower():
                    logger.info(line)
        else:
            logger.info("Available packages:")
            for line in lines:
                logger.info(line)

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running sdkmanager: {e.stderr}")
    except FileNotFoundError:
        logger.error("SDK manager not found. Please ensure it's installed and in your PATH.")

