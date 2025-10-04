import click
import sys
from .. import config as config_module
from .. import builder
from ..cli_logger import logger

@click.command()
@click.pass_context
@click.argument("platform")
@click.option("--sdk-version", default=None, help="Android SDK version to use.")
@click.option("--ndk-version", default=None, help="Android NDK version to use.")
@click.option("--jdk-version", default=None, help="JDK version to use.")
@click.option("--build-type", default="debug", help="Build type (e.g., debug, release).")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
def build(ctx, platform, sdk_version, ndk_version, jdk_version, build_type, verbose):
    """Build the application for a specified platform.

    PLATFORM: The target platform (e.g., android, ios, desktop).
    """
    logger.info(f"Building for {platform}...")
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

    # Override config values with command-line arguments if provided
    if sdk_version: conf.setdefault("android", {})["sdk_version"] = sdk_version
    if ndk_version: conf.setdefault("android", {})["ndk_version"] = ndk_version
    if jdk_version: conf.setdefault("java", {})["jdk_version"] = jdk_version
    if build_type: conf.setdefault("app", {})["build_type"] = build_type

    build_successful = False
    try:
        if platform == "android":
            build_successful = builder.build_android(conf, verbose)
        elif platform == "ios":
            # Assuming build_ios also returns a boolean
            build_successful = builder.build_ios(conf, verbose)
        elif platform == "desktop":
            # Assuming build_desktop also returns a boolean
            build_successful = builder.build_desktop(conf, verbose)
        else:
            logger.error(f"Error: Unsupported platform '{platform}'. Supported platforms are 'android', 'ios', 'desktop'.")
            return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during the build process for platform '{platform}': {e}")
        logger.info("Please check the log file for more details and report this issue to the DroidBuilder developers if it persists.")
        logger.exception(*sys.exc_info())
        return False

    if build_successful:
        logger.success(f"Build for {platform} completed successfully.")
        return True
    else:
        logger.error(f"Build for {platform} failed. Please check the logs for details.")
        return False
