import click
from . import config
from . import installer
from . import builder

@click.group()
def cli():
    """DroidBuilder CLI tool."""
    pass

@cli.command()
def init():
    """Initialize a new DroidBuilder project."""
    click.echo("Initializing DroidBuilder project...")

    project_name = click.prompt("Project Name", default="MyDroidApp")
    project_version = click.prompt("Project Version", default="0.1.0")
    main_file = click.prompt("Main Python File (e.g., main.py)", default="main.py")

    target_platforms_str = click.prompt("Target Platforms (comma-separated: android,ios,desktop)", default="android")
    target_platforms = [p.strip() for p in target_platforms_str.split(',') if p.strip()]

    android_sdk_version = click.prompt("Android SDK Version (e.g., 34)", default="34")
    android_ndk_version = click.prompt("Android NDK Version (e.g., 25.2.9519653)", default="25.2.9519653")
    java_jdk_version = click.prompt("Java JDK Version (e.g., 11)", default="11")

    conf = {
        "project": {
            "name": project_name,
            "version": project_version,
            "main_file": main_file,
            "target_platforms": target_platforms,
        },
        "android": {
            "sdk_version": android_sdk_version,
            "ndk_version": android_ndk_version,
        },
        "java": {
            "jdk_version": java_jdk_version,
        }
    }

    config.save_config(conf)
    click.echo(f"DroidBuilder project initialized. Configuration saved to {config.CONFIG_FILE}")

@cli.command()
@click.option('--ci', is_flag=True, help='Run in CI mode (non-interactive, accept licenses).')
def install_tools(ci):
    """Install required SDK, NDK, and JDK versions."""
    click.echo("Installing DroidBuilder tools...")
    conf = config.load_config()
    if not conf:
        click.echo("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return
    installer.setup_tools(conf, ci_mode=ci)
    click.echo("Tool installation complete.")

@cli.command()
@click.argument('platform')
def build(platform):
    """Build the application for a specified platform.

    PLATFORM: The target platform (e.g., android, ios, desktop).
    """
    click.echo(f"Building for {platform}...")
    conf = config.load_config()
    if not conf:
        click.echo("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return

    if platform == "android":
        builder.build_android(conf)
    elif platform == "ios":
        builder.build_ios(conf)
    elif platform == "desktop":
        builder.build_desktop(conf)
    else:
        click.echo(f"Error: Unsupported platform '{platform}'. Supported platforms are 'android', 'ios', 'desktop'.")

if __name__ == '__main__':
    cli()
