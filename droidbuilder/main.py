import click
import shutil
import os
import sys
from . import config
from . import installer
from . import builder
from .cli_logger import logger

@click.group()
def cli():
    """DroidBuilder CLI tool."""
    pass

@cli.command()
def init():
    """Initialize a new DroidBuilder project."""
    logger.info("Initializing a new DroidBuilder project. Please provide the following details:")

    try:
        project_name = click.prompt("Project Name", default="MyDroidApp")
        project_version = click.prompt("Project Version", default="0.1")
        main_file = click.prompt("Main Python File (e.g., main.py)", default="main.py")

        while True:
            target_platforms_str = click.prompt("Target Platforms (comma-separated: android, ios, desktop)", default="android")
            target_platforms = [p.strip() for p in target_platforms_str.split(',') if p.strip()]
            valid_platforms = ["android", "ios", "desktop"]
            if all(p in valid_platforms for p in target_platforms):
                break
            else:
                logger.warning(f"Invalid platform(s) detected. Please choose from: {', '.join(valid_platforms)}")

        # New prompts
        package_domain = click.prompt("Package Domain (e.g., org.example)", default="org.test")
        build_type = click.prompt("Build Type", type=click.Choice(['debug', 'release']), default="debug")

        while True:
            archs_str = click.prompt("Target Architectures (comma-separated: e.g., arm64-v8a,armeabi-v7a)", default="arm64-v8a,armeabi-v7a")
            archs = [a.strip() for a in archs_str.split(',') if a.strip()]
            # No specific validation for archs, just take as string list
            break # Exit loop after getting input

        manifest_file = click.prompt("Path to custom AndroidManifest.xml (leave empty for default)", default="")

        while True:
            cmdline_tools_tag = click.prompt("Android Command Line Tools Tag (e.g., 9123335)", default="9123335")
            if cmdline_tools_tag.isdigit():
                break
            else:
                logger.warning("Command Line Tools Tag must be a number.")

        requirements_str = click.prompt("Python Requirements for p4a (comma-separated: e.g., python3,kivy)", default="python3")
        requirements = [r.strip() for r in requirements_str.split(',') if r.strip()]


        while True:
            android_sdk_version = click.prompt("Android SDK Version (e.g., 34)", default="34")
            if android_sdk_version.isdigit():
                break
            else:
                logger.warning("Android SDK Version must be a number.")

        android_ndk_version = click.prompt("Android NDK Version (e.g., 25.2.9519653)", default="25.2.9519653")

        while True:
            java_jdk_version = click.prompt("Java JDK Version (e.g., 11)", default="11")
            if java_jdk_version.isdigit():
                break
            else:
                logger.warning("Java JDK Version must be a number.")

        conf = {
            "project": {
                "name": project_name,
                "version": project_version,
                "main_file": main_file,
                "target_platforms": target_platforms,
                "package_domain": package_domain, # New
                "build_type": build_type,         # New
                "requirements": requirements,     # New
            },
            "android": {
                "sdk_version": android_sdk_version,
                "ndk_version": android_ndk_version,
                "archs": archs,                   # New
                "cmdline_tools_version": cmdline_tools_tag, # New, maps to cmdline_tools_tag
                "manifest_file": manifest_file,   # New
            },
            "java": {
                "jdk_version": java_jdk_version,
            }
        }

        config.save_config(conf)
        logger.success(f"
DroidBuilder project initialized successfully! Configuration saved to {config.CONFIG_FILE}")
        logger.info("Next steps: Run 'droidbuilder install-tools' to set up your development environment.")

    except click.Abort:
        logger.warning("\nProject initialization aborted by user.")
    except Exception as e:
        logger.error(f"\nAn unexpected error occurred during initialization: {e}")
        logger.exception(*sys.exc_info())



@cli.command()
@click.option('--ci', is_flag=True, help='Run in CI mode (non-interactive, accept licenses).')
def install_tools(ci):
    """Install required SDK, NDK, and JDK versions."""
    logger.info("Installing DroidBuilder tools...")
    conf = config.load_config()
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return
    installer.setup_tools(conf, ci_mode=ci)
    logger.success("Tool installation complete.")

@cli.command()
@click.argument('platform')
@click.option('--sdk-version', help='Override Android SDK version.')
@click.option('--ndk-version', help='Override Android NDK version.')
@click.option('--jdk-version', help='Override Java JDK version.')
@click.option('--build-type', type=click.Choice(['debug', 'release']), help='Override build type (debug or release).')
def build(platform, sdk_version, ndk_version, jdk_version, build_type, verbose):
    """Build the application for a specified platform.

    PLATFORM: The target platform (e.g., android, ios, desktop).
    """
    logger.info(f"Building for {platform}...")
    conf = config.load_config()
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return

    # Override config values with command-line arguments if provided
    if sdk_version: conf.setdefault("android", {})["sdk_version"] = sdk_version
    if ndk_version: conf.setdefault("android", {})["ndk_version"] = ndk_version
    if jdk_version: conf.setdefault("java", {})["jdk_version"] = jdk_version
    if build_type: conf.setdefault("project", {})["build_type"] = build_type

    if platform == "android":
        builder.build_android(conf)
    elif platform == "ios":
        builder.build_ios(conf)
    elif platform == "desktop":
        builder.build_desktop(conf)
    else:
        logger.error(f"Error: Unsupported platform '{platform}'. Supported platforms are 'android', 'ios', 'desktop'.")

@cli.command()
def clean():
    """Remove build, dist, and temp files."""
    for folder in ["build", "dist", ".droidbuilder"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            logger.info(f"Removed {folder}")

if __name__ == '__main__':
    cli()
