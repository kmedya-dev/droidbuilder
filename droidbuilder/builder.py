import click
import os
import subprocess
import shutil
from pythonforandroid.toolchain import ToolchainCL

BUILD_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder_build")

def build_android(config):
    click.echo("Building Android application using python-for-android...")
    project_name = config.get("project", {}).get("name", "Unnamed Project")
    main_file = config.get("project", {}).get("main_file", "main.py")
    app_version = config.get("project", {}).get("version", "1.0")
    target_platforms = config.get("project", {}).get("target_platforms", [])

    # New: Get parameters from config
    package_domain = config.get("project", {}).get("package_domain", "org.test")
    build_type = config.get("project", {}).get("build_type", "debug")
    archs = config.get("android", {}).get("archs", ["arm64-v8a", "armeabi-v7a"])
    manifest_file = config.get("android", {}).get("manifest_file", "")
    requirements = config.get("project", {}).get("requirements", ["python3"])


    # Ensure Android is a target platform
    if "android" not in target_platforms:
        click.echo("Error: Android is not specified as a target platform in droidbuilder.toml.")
        return

    # Get Android specific configurations
    sdk_version = config.get("android", {}).get("sdk_version")
    ndk_version = config.get("android", {}).get("ndk_version")
    jdk_version = config.get("java", {}).get("jdk_version")
    # build_type is now from project config, removed redundant line

    # Construct p4a arguments
    p4a_args = [
        "--name", project_name,
        "--version", app_version,
        "--package", f"{package_domain}.{project_name.lower().replace(' ', '')}", # Use package_domain
        "--bootstrap", "sdl2", # Common bootstrap for Kivy/SDL2 apps
        "--requirements", ",".join(requirements), # Use requirements from config
        "--arch", *archs, # Use archs from config, unpack list
        "--sdk", str(sdk_version), # Pass SDK version
        "--ndk", str(ndk_version), # Pass NDK version
        "--java-home", os.environ.get("JAVA_HOME", ""), # Use JAVA_HOME set by installer
        "--android-api", str(sdk_version), # Target Android API
        "--dist-name", f"{project_name.lower().replace(' ', '')}_dist",
        "--orientation", "all",
        "--add-source", os.getcwd(), # Add current working directory as source
        "--main", main_file,
    ]

    if manifest_file: # Add manifest file if provided
        p4a_args.extend(["--manifest", manifest_file])

    if build_type == "release": # Use build_type from config
        click.echo("Warning: Release builds require signing. This prototype does not handle signing keys.")
        # p4a_args.extend(["--release", "--keystore", "path/to/keystore", "--keyalias", "your_alias", "--keypass", "your_key_pass", "--storepass", "your_store_pass"])

    # Clean up previous p4a build directory if it exists
    p4a_build_dir = os.path.join(os.path.expanduser("~"), ".p4a_build")
    if os.path.exists(p4a_build_dir):
        click.echo(f"  - Cleaning up previous p4a build directory: {p4a_build_dir}")
        shutil.rmtree(p4a_build_dir)

    click.echo(f"  - Running p4a command: build apk {' '.join(p4a_args)}")
    try:
        import sys
        original_argv = sys.argv[:] # Save original sys.argv

        # Construct arguments for ToolchainCL
        # The first argument is the script name, then the subcommand 'apk', then the p4a_args
        sys.argv = ["toolchain.py", "apk"] + p4a_args

        try:
            toolchain_instance = ToolchainCL()
            toolchain_instance.apk(toolchain_instance.args) # Pass the parsed args object
            click.echo("  - Android APK build complete via python-for-android.")
            click.echo(f"  - APK should be in {os.path.join(os.getcwd(), project_name.lower().replace(' ', '') + '_dist/bin/')}")
        finally:
            sys.argv = original_argv # Restore original sys.argv
    except Exception as e:
        click.echo(f"Error building Android APK with python-for-android: {e}")
        click.echo("Please ensure all required tools are installed and configured correctly.")

def build_ios(config):
    click.echo("Building iOS application...")
    project_name = config.get("project", {}).get("name", "Unnamed Project")
    click.echo(f"  - Project: {project_name}")
    click.echo("  - iOS build requires Xcode and specific iOS development tools.")
    click.echo("  - This functionality is a placeholder and needs full implementation.")
    click.echo("  - iOS build complete (placeholder).")

def build_desktop(config):
    click.echo("Building Desktop application...")
    project_name = config.get("project", {}).get("name", "Unnamed Project")
    click.echo(f"  - Project: {project_name}")
    click.echo("  - Desktop build depends on the chosen framework (e.g., Electron, PyInstaller, Kivy desktop). ")
    click.echo("  - This functionality is a placeholder and needs full implementation.")
    click.echo("  - Desktop build complete (placeholder).")