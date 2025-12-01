import click
import sys
from .. import config as config_module
from .. import builder_gradle
from ..cli_logger import logger

@click.command()
@click.pass_context
@click.argument("platform")
@click.option("--build-type", default="debug", help="Build type (e.g., debug, release).")
def gradle(ctx, platform, build_type):
    """Build the application for a specified platform.

    PLATFORM: The target platform (e.g., android, ios, desktop).
    """
    logger.info(f"Building for {platform}...")
    conf = None
    try:
        conf = config_module.load_config(path=ctx.obj["path"])
        if not conf:
            logger.error("Error: No droidbuilder.toml found in the current directory or specified path.")
            return False
    except FileNotFoundError:
        logger.error("Error: droidbuilder.toml not found. Please ensure you are in the correct project directory or specify the path.")
        return False

    build_successful = False

    if platform == "android":
        build_successful = builder_gradle.build_android(conf, build_type=build_type)
    if build_successful:
        logger.success(f"Build for {platform} completed successfully.")
        return True
    else:
        logger.error(f"Build for {platform} failed. Please check the logs for details.")
        return False
