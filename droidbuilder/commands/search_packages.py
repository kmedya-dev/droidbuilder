
import click
import os
import subprocess
from .. import installer
from ..cli_logger import logger

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
            found_matches = False
            for line in lines:
                if query.lower() in line.lower():
                    logger.info(line)
                    found_matches = True
            if not found_matches:
                logger.info(f"No packages found matching '{query}'.")
        else:
            logger.info("Available packages:")
            for line in lines:
                logger.info(line)

    except FileNotFoundError:
        logger.error("SDK manager executable not found. This usually means the Android SDK Command-line Tools are not installed or configured correctly.")
        logger.info("Please run 'droidbuilder install-tools' to ensure all necessary SDK components are installed.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running sdkmanager (Exit Code: {e.returncode}):")
        if e.stdout:
            logger.error(f"Stdout:\n{e.stdout}")
        if e.stderr:
            logger.error(f"Stderr:\n{e.stderr}")
        logger.info("This might indicate an issue with your Android SDK installation or its components.")
        logger.info("Please try running 'droidbuilder doctor' to diagnose potential problems, or 'droidbuilder install-tools' to re-install SDK components.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while searching for packages: {e}")
        logger.info("Please report this issue to the DroidBuilder developers.")
        logger.exception(*sys.exc_info())


