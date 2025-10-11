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
        # Allow empty list if the input string was empty
        if not value_str.strip():
            return []
        values = [v.strip() for v in value_str.split(',') if v.strip()]
        if values:
            return values
        else:
            logger.warning(f"Invalid input for {prompt}. Please provide a comma-separated list of values.")

import click
import os
import sys
import toml
from .. import config as config_module
from ..cli_logger import logger


def _get_default_config():
    return {
        "app": {
            "name": "MyAwesomeApp",
            "package_domain": "org.test",
            "version": "0.1",
            "main_file": "main.py",
            "target_platforms": ["android"],
            "dependency": {
                "runtime_packages": [],
                "buildtime_packages": [],
            },
            "dependency_mapping": {},
        },
        "android": {
            "cmdline_tools_version": "13114758",
            "sdk_version": "34",
            "ndk_version": "25.2.9519653",
            "min_sdk_version": "21",
            "ndk_api": "24",
            "archs": ["arm64-v8a", "armeabi-v7a"],
            "manifest_file": "",
            "intent_filters_file": "",
            "accept_sdk_license": "interactive",
        },
        "java": {
            "jdk_version": "17",
            "gradle_version": "8.7",
        },
        "python": {
            "python_version": "3.9.13",
        },
        "build": {
            "type": "debug",
            "patches": {}
        }
    }


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
        # Allow empty list if the input string was empty
        if not value_str.strip():
            return []
        values = [v.strip() for v in value_str.split(',') if v.strip()]
        if values:
            return values
        else:
            logger.warning(f"Invalid input for {prompt}. Please provide a comma-separated list of values.")


@click.command()
@click.option('--non-interactive', is_flag=True, help='Run in non-interactive mode using default values.')
@click.option('--config-file', type=click.Path(exists=True), help='Path to a TOML file with configuration values.')
@click.pass_context
def init(ctx, non_interactive, config_file):
    """Initialize a new DroidBuilder app."""
    logger.info("Initializing a new DroidBuilder app.")

    conf = {}
    if config_file:
        logger.info(f"Loading configuration from {config_file}")
        with open(config_file, 'r') as f:
            conf = toml.load(f)
    elif non_interactive:
        logger.info("Running in non-interactive mode with default values.")
        conf = _get_default_config()
    else:
        logger.info("Please provide the following details:")
        try:
            app_name = _prompt_for_input("App Name", "MyAwesomeApp")
            app_version = _prompt_for_input("App Version", "0.1")
            main_file = _prompt_for_input("Main Python File (e.g., main.py)", "main.py")

            target_platforms = _prompt_for_list_input("Target Platforms (comma-separated: android, ios, desktop)", "android")
            package_domain = _prompt_for_input("Package Domain (e.g., org.example)", "org.test")
            build_type = _prompt_for_input("Build Type", "debug", type=click.Choice(['debug', 'release']))

            archs = _prompt_for_list_input("Target Architectures (comma-separated: e.g., arm64-v8a,armeabi-v7a)", "arm64-v8a,armeabi-v7a")
            manifest_file = _prompt_for_input("Path to custom AndroidManifest.xml (leave empty for default)", "")
            intent_filters_file = _prompt_for_input("Path to custom intent_filters.xml (leave empty for none)", "")
            cmdline_tools_tag = _prompt_for_input("Android Command Line Tools Tag (e.g., 13114758)", "13114758", validation_func=str.isdigit)
            runtime_packages = _prompt_for_list_input("Runtime Packages (comma-separated: e.g., kivy, pyjnius)", "")

            android_sdk_version = _prompt_for_input("Android SDK Version (e.g., 34)", "34", validation_func=str.isdigit)
            android_min_sdk_version = _prompt_for_input("Android Minimum SDK Version (e.g., 21)", "21", validation_func=str.isdigit)
            android_ndk_api = _prompt_for_input("Android NDK API (e.g., 24)", "24", validation_func=str.isdigit)
            android_ndk_version = _prompt_for_input("Android NDK Version (e.g., 25.2.9519653)", "25.2.9519653")

            java_jdk_version = _prompt_for_input("Java JDK Version (e.g., 17)", "17", validation_func=str.isdigit)
            java_gradle_version = _prompt_for_input("Java Gradle Version (e.g., 8.7)", "8.7")
            python_version = _prompt_for_input("Python Version for cross-compilation (e.g., 3.9.13)", "3.9.13")
            accept_sdk_license = _prompt_for_input("Accept SDK licenses automatically?", "interactive", type=click.Choice(['interactive', 'non-interactive']))
            buildtime_packages = _prompt_for_list_input("Buildtime Packages (comma-separated: e.g., openssl, libffi)", "")

            conf = {
                "app": {
                    "name": app_name,
                    "package_domain": package_domain,
                    "version": app_version,
                    "main_file": main_file,
                    "target_platforms": target_platforms,
                    "dependency": {
                        "runtime_packages": runtime_packages,
                        "buildtime_packages": buildtime_packages,
                    },
                    "dependency_mapping": {},
                },
                "android": {
                    "cmdline_tools_version": cmdline_tools_tag,
                    "sdk_version": android_sdk_version,
                    "ndk_version": android_ndk_version,
                    "min_sdk_version": android_min_sdk_version,
                    "ndk_api": android_ndk_api,
                    "archs": archs,
                    "manifest_file": manifest_file,
                    "intent_filters_file": intent_filters_file,
                    "accept_sdk_license": accept_sdk_license,
                },
                "java": {
                    "jdk_version": java_jdk_version,
                    "gradle_version": java_gradle_version,
                },
                "python": {
                    "python_version": python_version,
                },
                "build": {
                    "type": build_type,
                    "patches": {}
                }
            }
        except click.Abort:
            logger.warning("\nApp initialization aborted by user.")
            return

    try:
        config_module.save_config(conf, path=ctx.obj["path"])
        logger.success(f"DroidBuilder app initialized successfully! Configuration saved to {os.path.join(ctx.obj['path'], config_module.CONFIG_FILE)}")
        logger.info("Next steps: Run 'droidbuilder install-tools' to set up your development environment.")
    except IOError as e:
        logger.error(f"Error saving configuration file: {e}")
        logger.info("Please check your file permissions and try again.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving configuration file: {e}")
        logger.exception(*sys.exc_info())



