import click
import toml
import subprocess
import sys
import os
from ..cli_logger import logger
from ..utils.command_executor import run_shell_command

@click.command()
def update_deps():
    """Update DroidBuilder's project dependencies."""
    logger.info("Updating DroidBuilder dependencies...")
    try:
        pyproject_path = "pyproject.toml"
        if not os.path.exists(pyproject_path):
            logger.error(f"Error: '{pyproject_path}' not found in the current directory.")
            return

        with open(pyproject_path, "r") as f:
            pyproject_data = toml.load(f)

        dependencies = pyproject_data.get("project", {}).get("dependencies", [])

        if not dependencies:
            logger.info("No dependencies found in pyproject.toml.")
            return

        logger.info(f"Found dependencies: {', '.join(dependencies)}")

        # Construct the pip install command
        command = [sys.executable, "-m", "pip", "install", "--upgrade"] + dependencies

        stdout, stderr, returncode = run_shell_command(command)
        if returncode != 0:
            logger.error(f"Failed to update dependencies (Exit Code: {returncode}):")
            if stdout:
                logger.error(f"Stdout:\n{stdout}")
            if stderr:
                logger.error(f"Stderr:\n{stderr}")
            logger.info("Please check your network connection and ensure the dependencies are correctly specified.")
            return

        logger.info(stdout)
        if stderr:
            logger.warning(stderr)
        logger.success("DroidBuilder dependencies updated successfully.")

    except FileNotFoundError: # Redundant due to os.path.exists check, but keeping for robustness
        logger.error("pyproject.toml not found in the current directory.")
    except toml.TomlDecodeError:
        logger.error("Error decoding pyproject.toml. Please check its format for syntax errors.")
    except IOError as e:
        logger.error(f"Error reading pyproject.toml: {e}")
        logger.info("Please check file permissions.")
    except FileNotFoundError:
        logger.error(f"Error: Python executable '{sys.executable}' or pip not found. Please ensure Python and pip are correctly installed and in your PATH.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during dependency update: {e}")
        logger.info("Please report this issue to the DroidBuilder developers.")
        logger.exception(*sys.exc_info())

