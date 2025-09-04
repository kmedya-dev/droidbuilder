import click
import os
import sys
from .. import config as config_module
from ..cli_logger import logger

def _prompt_for_input(prompt, default, validation_func=None, **kwargs):
    while True:
        value = click.prompt(prompt, default=default, **kwargs)
        if validation_func is None or validation_func(value):
            return value
        else:
            logger.warning(f"Invalid input for {prompt}. Please try again.")

def _prompt_for_list_input(prompt, default):
    while True:
        value_str = click.prompt(prompt, default=default)
        values = [v.strip() for v in value_str.split(',') if v.strip()]
        if values:
            return values
        else:
            logger.warning(f"Invalid input for {prompt}. Please provide a comma-separated list of values.")

@click.command()
@click.pass_context
def init(ctx):
    """Initialize a new DroidBuilder project."""
    logger.info("Initializing a new DroidBuilder project. Please provide the following details:")

    try:
        project_name = _prompt_for_input("Project Name", "MyDroidApp")
        project_version = _prompt_for_input("Project Version", "0.1")
        main_file = _prompt_for_input("Main Python File (e.g., main.py)", "main.py")

        target_platforms = _prompt_for_list_input("Target Platforms (comma-separated: android, ios, desktop)", "android")
        package_domain = _prompt_for_input("Package Domain (e.g., org.example)", "org.test")
        build_type = _prompt_for_input("Build Type", "debug", type=click.Choice(['debug', 'release']))
        
        archs = _prompt_for_list_input("Target Architectures (comma-separated: e.g., arm64-v8a,armeabi-v7a)", "arm64-v8a,armeabi-v7a")
        manifest_file = _prompt_for_input("Path to custom AndroidManifest.xml (leave empty for default)", "")
        cmdline_tools_tag = _prompt_for_input("Android Command Line Tools Tag (e.g., 9123335)", "9123335", validation_func=str.isdigit)
        requirements = _prompt_for_list_input("Python Requirements (comma-separated: e.g., py2jib)", "")
        
        android_sdk_version = _prompt_for_input("Android SDK Version (e.g., 34)", "34", validation_func=str.isdigit)
        android_min_sdk_version = _prompt_for_input("Android Minimum SDK Version (e.g., 21)", "21", validation_func=str.isdigit)
        android_ndk_api = _prompt_for_input("Android NDK API (e.g., 24)", "24", validation_func=str.isdigit)
        android_ndk_version = _prompt_for_input("Android NDK Version (e.g., 25.2.9519653)", "25.2.9519653")
        
        java_jdk_version = _prompt_for_input("Java JDK Version (e.g., 11)", "11", validation_func=str.isdigit)
        accept_sdk_license = _prompt_for_input("Accept SDK licenses automatically?", "interactive", type=click.Choice(['interactive', 'non-interactive']))
        system_packages = _prompt_for_list_input("System Packages (comma-separated: e.g., openssl, sdl2)", "")

        conf = {
            "project": {
                "name": project_name,
                "version": project_version,
                "main_file": main_file,
                "target_platforms": target_platforms,
                "package_domain": package_domain,
                "build_type": build_type,
                "requirements": requirements,
                "system_packages": system_packages,
            },
            "android": {
                "sdk_version": android_sdk_version,
                "ndk_version": android_ndk_version,
                "min_sdk_version": android_min_sdk_version,
                "ndk_api": android_ndk_api,
                "archs": archs,
                "cmdline_tools_version": cmdline_tools_tag,
                "manifest_file": manifest_file,
                "accept_sdk_license": accept_sdk_license,
            },
            "java": {
                "jdk_version": java_jdk_version,
            }
        }

        try:
            config_module.save_config(conf, path=ctx.obj["path"])
            logger.success(f"DroidBuilder project initialized successfully! Configuration saved to {os.path.join(ctx.obj['path'], config_module.CONFIG_FILE)}")
            logger.info("Next steps: Run 'droidbuilder install-tools' to set up your development environment.")
        except IOError as e:
            logger.error(f"Error saving configuration file: {e}")
            logger.info("Please check your file permissions and try again.")

    except click.Abort:
        logger.warning("\nProject initialization aborted by user.")
    except Exception as e:
        logger.error(f"\nAn unexpected error occurred during initialization: {e}")
        logger.info("Please report this issue on the DroidBuilder GitHub page.")
        logger.exception(*sys.exc_info())
