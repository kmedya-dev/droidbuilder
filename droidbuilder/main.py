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
    click.echo("Initializing a new DroidBuilder project. Please provide the following details:")

    try:
        project_name = click.prompt("Project Name", default="MyDroidApp")
        project_version = click.prompt("Project Version", default="0.1.0")
        main_file = click.prompt("Main Python File (e.g., main.py)", default="main.py")

        while True:
            target_platforms_str = click.prompt("Target Platforms (comma-separated: android, ios, desktop)", default="android")
            target_platforms = [p.strip() for p in target_platforms_str.split(',') if p.strip()]
            valid_platforms = ["android", "ios", "desktop"]
            if all(p in valid_platforms for p in target_platforms):
                break
            else:
                click.echo(f"Invalid platform(s) detected. Please choose from: {', '.join(valid_platforms)}")

        while True:
            android_sdk_version = click.prompt("Android SDK Version (e.g., 34)", default="34")
            if android_sdk_version.isdigit():
                break
            else:
                click.echo("Android SDK Version must be a number.")

        android_ndk_version = click.prompt("Android NDK Version (e.g., 25.2.9519653)", default="25.2.9519653")

        while True:
            java_jdk_version = click.prompt("Java JDK Version (e.g., 11)", default="11")
            if java_jdk_version.isdigit():
                break
            else:
                click.echo("Java JDK Version must be a number.")

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
        click.echo(f"\nDroidBuilder project initialized successfully! Configuration saved to {config.CONFIG_FILE}")
        click.echo("Next steps: Run 'droidbuilder install-tools' to set up your development environment.")

    except click.Abort:
        click.echo("\nProject initialization aborted by user.")
    except Exception as e:
        click.echo(f"\nAn unexpected error occurred during initialization: {e}")


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
@click.option('--sdk-version', help='Override Android SDK version.')
@click.option('--ndk-version', help='Override Android NDK version.')
@click.option('--jdk-version', help='Override Java JDK version.')
@click.option('--build-type', type=click.Choice(['debug', 'release']), help='Override build type (debug or release).')
def build(platform, sdk_version, ndk_version, jdk_version, build_type):
    """Build the application for a specified platform.

    PLATFORM: The target platform (e.g., android, ios, desktop).
    """
    click.echo(f"Building for {platform}...")
    conf = config.load_config()
    if not conf:
        click.echo("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
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
        click.echo(f"Error: Unsupported platform '{platform}'. Supported platforms are 'android', 'ios', 'desktop'.")

if __name__ == '__main__':
    cli()
