import os
import sys
import shutil
from . import config
from .utils.command_executor import run_shell_command
from .cli_logger import logger

# Path to the internal gradle project template/source
BUILD_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder", "build")

def build_android(config, build_type="debug"):
    """
    Builds the project using Gradle.
    
    Args:
        config (dict): The application configuration.
        build_type (str): "debug" or "release". Defaults to "debug".
    
    Returns:
        bool: True if build succeeded, False otherwise.
    """
    
    # app configs
    app_config = config.get("app", {})
    app_name = app_config.get("name")
    target_platforms = app_config.get("target_platforms", [])

    # Build configs
    # If build_type is passed as argument (and not default/None if we handled None), 
    # it overrides config. But here we have a default "debug".
    # The CLI passes "debug" by default too.
    # If the user specifically put something in config, maybe they want that?
    # Usually CLI overrides config.
    # So we stick with the argument 'build_type'.
    # However, if we want to respect config if CLI was default... 
    # simpler to just use the argument as the source of truth since the CLI handles the default.
    
    # The gradle project root is BUILD_DIR
    build_path = os.path.join(BUILD_DIR, app_name)
    
    if not os.path.exists(build_path):
        logger.error(f"Build directory not found at: {build_path}")
        return False

    gradle_home = os.environ.get("GRADLE_HOME")
    gradle_executable = None
    
    if gradle_home:
        gradle_executable = os.path.join(gradle_home, "bin", "gradle")
        if sys.platform == "win32":
            gradle_executable = os.path.join(gradle_home, "bin", "gradle.bat")
    
    if not gradle_executable or not os.path.exists(gradle_executable):
        # Fallback to system path
        gradle_executable = shutil.which("gradle")

    if not gradle_executable:
        logger.error(f"Error: gradle not found. Please set GRADLE_HOME or ensure gradle is in your PATH.")
        return False

    build_task = "assembleDebug"
    if build_type == "release":
        build_task = "assembleRelease"

    gradle_build_cmd = [gradle_executable, build_task, "--info"]
    
    logger.info(f"Building {build_type} version in {build_path}...")
    
    result = run_shell_command(
        gradle_build_cmd,
        description=f"Running Gradle build: {' '.join(gradle_build_cmd)}", 
        cwd=build_path
    )
    
    if result["returncode"] != 0:
        logger.error(f"Gradle build failed (Exit Code: {result['returncode']}):")
        if result["stdout"]:
            logger.error(f"Stdout:\n{result['stdout']}")
        if result["stderr"]:
            logger.error(f"Stderr:\n{result['stderr']}")
        logger.info("Please review the Gradle output above for specific errors and ensure your Android SDK and NDK are correctly installed and configured.")
        return False
    
    logger.success("Gradle build completed successfully.")
    return True
