import click
from .. import config as config_module
from .. import builder
from ..cli_logger import logger

@click.command()
@click.argument('platform')
@click.option('--sdk-version', help='Override Android SDK version.')
@click.option('--ndk-version', help='Override Android NDK version.')
@click.option('--jdk-version', help='Override Java JDK version.')
@click.option('--build-type', type=click.Choice(['debug', 'release']), help='Override build type (debug or release).')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.pass_context
def build(ctx, platform, sdk_version, ndk_version, jdk_version, build_type, verbose):
    """Build the application for a specified platform.

    PLATFORM: The target platform (e.g., android, ios, desktop).
    """
    logger.info(f"Building for {platform}...")
    try:
        conf = config_module.load_config(path=ctx.obj["path"])
        if not conf:
            logger.error("Error: No droidbuilder.toml found in the current directory or specified path.")
            logger.info("Please run 'droidbuilder init' to create a new project configuration.")
            return
    except FileNotFoundError:
        logger.error("Error: droidbuilder.toml not found. Please ensure you are in the correct project directory or specify the path.")
        logger.info("Run 'droidbuilder init' to create a new project configuration.")
        return
    except Exception as e:
        logger.error(f"Error loading droidbuilder.toml: {e}")
        logger.info("Please check the file's format and permissions.")
        return

    # Override config values with command-line arguments if provided
    if sdk_version: conf.setdefault("android", {})["sdk_version"] = sdk_version
    if ndk_version: conf.setdefault("android", {})["ndk_version"] = ndk_version
    if jdk_version: conf.setdefault("java", {})["jdk_version"] = jdk_version
    if build_type: conf.setdefault("project", {})["build_type"] = build_type

    try:
        if platform == "android":
            builder.build_android(conf, verbose)
        elif platform == "ios":
            builder.build_ios(conf, verbose)
        elif platform == "desktop":
            builder.build_desktop(conf, verbose)
        else:
            logger.error(f"Error: Unsupported platform '{platform}'. Supported platforms are 'android', 'ios', 'desktop'.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during the build process: {e}")
        logger.info("Please check the log file for more details and report this issue to the DroidBuilder developers if it persists.")
