import click
import os
import subprocess
import shutil
import sys
from pythonforandroid.toolchain import ToolchainCL
from .cli_logger import logger

BUILD_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder_build")

def build_android(config, verbose=False):
    """Build the Android application using python-for-android."""
    logger.info("Building Android application using python-for-android...")
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
        logger.error("Error: Android is not specified as a target platform in droidbuilder.toml.")
        return

    # Get Android specific configurations
    sdk_version = config.get("android", {}).get("sdk_version")
    ndk_version = config.get("android", {}).get("ndk_version")
    min_sdk_version = config.get("android", {}).get("min_sdk_version") # New
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
        "--sdk-dir", os.environ.get("ANDROID_HOME", ""), # Pass SDK version
        "--ndk-dir", os.environ.get("NDK_HOME", "") , # Pass NDK version
        "--java-home", os.environ.get("JAVA_HOME", ""), # Use JAVA_HOME set by installer
        "--android-api", str(sdk_version), # Target Android API
	"--android-minapi", str(min_sdk_version), # Minimum Android API
        "--dist-name", f"{project_name.lower().replace(' ', '')}_dist",
        "--orientation", "all",
        "--add-source", os.getcwd(), # Add current working directory as source
        "--main", main_file,
    ]

    if verbose:
        p4a_args.append("--verbose")

    if manifest_file: # Add manifest file if provided
        p4a_args.extend(["--manifest", manifest_file])

    if min_sdk_version: # Add min-sdk if provided
        p4a_args.extend(["--min-sdk", str(min_sdk_version)])

    if build_type == "release": # Use build_type from config
        logger.warning("Warning: Release builds require signing. This prototype does not handle signing keys.")
        # p4a_args.extend(["--release", "--keystore", "path/to/keystore", "--keyalias", "your_alias", "--keypass", "your_key_pass", "--storepass", "your_store_pass"])

    # Clean up previous p4a build directory if it exists
    p4a_build_dir = os.path.join(os.path.expanduser("~"), ".p4a_build")
    if os.path.exists(p4a_build_dir):
        logger.info(f"  - Cleaning up previous p4a build directory: {p4a_build_dir}")
        shutil.rmtree(p4a_build_dir)

    logger.info(f"  - Running p4a command: build apk {' '.join(p4a_args)}")
    try:
        import sys
        original_argv = sys.argv[:] # Save original sys.argv

        # Construct arguments for ToolchainCL
        # The first argument is the script name, then the subcommand 'apk', then the p4a_args
        sys.argv = ["toolchain.py", "apk"] + p4a_args

        try:
            toolchain_instance = ToolchainCL()
            toolchain_instance.apk(toolchain_instance.args) # Pass the parsed args object
            logger.success("  - Android APK build complete via python-for-android.")
            logger.info(f"  - APK should be in {os.path.join(os.getcwd(), project_name.lower().replace(' ', '') + '_dist/bin/')}")
        finally:
            sys.argv = original_argv # Restore original sys.argv
    except Exception as e:
        logger.error(f"Error building Android APK with python-for-android: {e}")
        logger.info("Please ensure all required tools are installed and configured correctly.")
        logger.exception(*sys.exc_info())

def build_ios(config, verbose=False):
    """Build the iOS application."""
    logger.info("Building iOS application...")
    project_name = config.get("project", {}).get("name", "Unnamed Project")
    logger.info(f"  - Project: {project_name}")
    logger.info("  - iOS build requires Xcode and specific iOS development tools.")
    logger.info("  - This functionality is a placeholder and needs full implementation.")
    if verbose:
        logger.info("  - Verbose mode enabled.")
    logger.info("  - iOS build complete (placeholder).")

def build_desktop(config, verbose=False):
    """Build the Desktop application."""
    logger.info("Building Desktop application...")
    project_name = config.get("project", {}).get("name", "Unnamed Project")
    logger.info(f"  - Project: {project_name}")
    logger.info("  - Desktop build depends on the chosen framework (e.g., Electron, PyInstaller, Kivy desktop). ")
    logger.info("  - This functionality is a placeholder and needs full implementation.")
    if verbose:
        logger.info("  - Verbose mode enabled.")
    logger.info("  - Desktop build complete (placeholder).")
