import click
import shutil
import os
import sys
from . import config as config_module
from . import installer
from . import builder
from .cli_logger import logger, get_latest_log_file
import importlib.metadata
from .commands.list_files import list_files

@click.group()
@click.option("--path", "-p", default=".", help="Path to the project directory.")
@click.pass_context
def cli(ctx, path):
    """DroidBuilder CLI tool."""
    ctx.obj = {"path": path}

cli.add_command(list_files)

@cli.command()
@click.pass_context
def init(ctx):
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

        while True: # New prompt for min_sdk_version
            android_min_sdk_version = click.prompt("Android Minimum SDK Version (e.g., 21)", default="21")
            if android_min_sdk_version.isdigit():
                break
            else:
                logger.warning("Android Minimum SDK Version must be a number.")

        while True:
            android_ndk_api = click.prompt("Android NDK API (e.g., 24)", default="24")
            if android_ndk_api.isdigit():
                break
            else:
                logger.warning("Android NDK API must be a number.")

        android_ndk_version = click.prompt("Android NDK Version (e.g., 25.2.9519653)", default="25.2.9519653")

        while True:
            java_jdk_version = click.prompt("Java JDK Version (e.g., 11)", default="11")
            if java_jdk_version.isdigit():
                break
            else:
                logger.warning("Java JDK Version must be a number.")
        
        accept_sdk_license = click.prompt("Accept SDK licenses automatically?", type=click.Choice(['interactive', 'non-interactive']), default="interactive")

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
                "min_sdk_version": android_min_sdk_version, # New
                "ndk_api": android_ndk_api,
                "archs": archs,                   # New
                "cmdline_tools_version": cmdline_tools_tag, # New, maps to cmdline_tools_tag
                "manifest_file": manifest_file,   # New
                "accept_sdk_license": accept_sdk_license
            },
            "java": {
                "jdk_version": java_jdk_version,
            }
        }

        config_module.save_config(conf, path=ctx.obj["path"])
        logger.success(f"DroidBuilder project initialized successfully! Configuration saved to {os.path.join(ctx.obj['path'], config_module.CONFIG_FILE)}")
        logger.info("Next steps: Run 'droidbuilder install-tools' to set up your development environment.")

    except click.Abort:
        logger.warning("\nProject initialization aborted by user.")
    except Exception as e:
        logger.error(f"\nAn unexpected error occurred during initialization: {e}")
        logger.exception(*sys.exc_info())




@cli.command()
@click.pass_context
def install_tools(ctx):
    """Install required SDK, NDK, and JDK versions."""
    logger.info("Installing DroidBuilder tools...")
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return
    installer.setup_tools(conf)
    logger.success("Tool installation complete.")

@cli.command()
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
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return

    # Override config values with command-line arguments if provided
    if sdk_version: conf.setdefault("android", {})["sdk_version"] = sdk_version
    if ndk_version: conf.setdefault("android", {})["ndk_version"] = ndk_version
    if jdk_version: conf.setdefault("java", {})["jdk_version"] = jdk_version
    if build_type: conf.setdefault("project", {})["build_type"] = build_type

    if platform == "android":
        builder.build_android(conf, verbose)
    elif platform == "ios":
        builder.build_ios(conf, verbose)
    elif platform == "desktop":
        builder.build_desktop(conf, verbose)
    else:
        logger.error(f"Error: Unsupported platform '{platform}'. Supported platforms are 'android', 'ios', 'desktop'.")

@cli.command()
@click.pass_context
def clean(ctx):
    """Remove build, dist, and temp files."""
    for folder in ["build", "dist", ".droidbuilder"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            logger.info(f"Removed {folder}")

@cli.command(name="list-tools")
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


@cli.command(name="list-droids")
@click.pass_context
def list_droids(ctx):
    """List all installed droids."""
    logger.info("Listing installed droids...")
    installed_droids = installer.list_installed_droids()
    if not installed_droids:
        logger.info("No droids installed yet.")
        return

    logger.info("Installed droids:")
    for droid in installed_droids:
        logger.info(f"  - {droid}")

@cli.command()
@click.argument('tool_name')
@click.pass_context
def uninstall(ctx, tool_name):
    """Uninstall a specified tool (e.g., jdk-11)."""
    installer.uninstall_tool(tool_name)

@cli.command()
@click.argument('tool_name')
@click.pass_context
def update(ctx, tool_name):
    """Update a specified tool to the latest version (e.g., jdk)."""
    installer.update_tool(tool_name)

@cli.command()
@click.argument('tool_name')
@click.pass_context
def search(ctx, tool_name):
    """Search for available versions of a specified tool (e.g., jdk)."""
    installer.search_tool(tool_name)

@cli.command()
@click.pass_context
def doctor(ctx):
    """Check if all required tools are installed and the environment is set up correctly."""
    installer.check_environment()

@cli.group()
@click.pass_context
def config(ctx):
    """View or edit the droidbuilder.toml configuration file."""
    pass

@config.command()
@click.pass_context
def view(ctx):
    """View the contents of the droidbuilder.toml file."""
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return
    with open(os.path.join(ctx.obj["path"], config_module.CONFIG_FILE), 'r') as f:
        click.echo(f.read())

@config.command()
@click.pass_context
def edit(ctx):
    """Edit the droidbuilder.toml file in your default editor."""
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return
    click.edit(filename=os.path.join(ctx.obj["path"], config_module.CONFIG_FILE))

@cli.command()
def version():
    """Print the version of the DroidBuilder tool."""
    try:
        ver = importlib.metadata.version("droidbuilder")
        logger.info(f"DroidBuilder version {ver}")
    except importlib.metadata.PackageNotFoundError:
        logger.error("Error: Could not determine the version of DroidBuilder.")

@cli.command()
def log():
    """Display the latest log file."""
    latest_log = get_latest_log_file()
    if not latest_log:
        logger.error("No log files found.")
        return

    logger.info(f"Displaying log file: {latest_log}")
    with open(latest_log, 'r') as f:
        logger.info(f.read())

if __name__ == '__main__':
    cli()
