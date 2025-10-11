import click
import sys
import os
from .. import config as config_module
from .. import installer
from ..cli_logger import logger

@click.command()
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
@click.pass_context
def install_tools(ctx, verbose):
    """Install required SDK, NDK, and JDK versions."""
    logger.info("Installing DroidBuilder tools...")
    conf = None
    try:
        conf = config_module.load_config(path=ctx.obj["path"])
        if not conf:
            logger.error("Error: No droidbuilder.toml found in the current directory or specified path.")
            logger.info("Please run 'droidbuilder init' to create a new project configuration.")
            return False
    except FileNotFoundError:
        logger.error("Error: droidbuilder.toml not found. Please ensure you are in the correct project directory or specify the path.")
        logger.info("Run 'droidbuilder init' to create a new project configuration.")
        return False
    except Exception as e:
        logger.error(f"Error loading droidbuilder.toml: {e}")
        logger.info("Please check the file's format and permissions.")
        return False
    
    try:
        if installer.setup_tools(conf, verbose=verbose):
            logger.success("Tool installation complete.")
            env_file_path = os.path.join(os.path.expanduser("~"), ".droidbuilder", "env.sh")
            if os.path.exists(env_file_path):
                with open(env_file_path, "r") as f:
                    for line in f:
                        if line.startswith("export "):
                            line = line.strip().replace("export ", "")
                            parts = line.split("=", 1)
                            if len(parts) == 2:
                                key, value = parts
                                if key == "PATH":
                                    # Expand $PATH
                                    if "$PATH" in value:
                                        value = value.replace("$PATH", os.environ.get("PATH", ""))
                                    # Also expand other variables
                                    for var_key, var_value in os.environ.items():
                                        value = value.replace(f"${var_key}", var_value)
                                os.environ[key] = value
                logger.info(f"Environment variables from {env_file_path} have been set for the current session.")
            return True
        else:
            logger.error("Tool installation failed. Please check the logs for details.")
            return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during tool installation: {e}")
        logger.info("Please check the log file for more details and report this issue to the DroidBuilder developers if it persists.")
        logger.exception(*sys.exc_info())
        return False
