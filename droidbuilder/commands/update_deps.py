import click
import toml
import subprocess
import sys
from ..cli_logger import logger

@click.command()
def update_deps():
    """Update DroidBuilder's project dependencies."""
    logger.info("Updating DroidBuilder dependencies...")
    try:
        with open("pyproject.toml", "r") as f:
            pyproject_data = toml.load(f)

        dependencies = pyproject_data.get("project", {}).get("dependencies", [])

        if not dependencies:
            logger.info("No dependencies found in pyproject.toml.")
            return

        logger.info(f"Found dependencies: {', '.join(dependencies)}")

        # Construct the pip install command
        command = [sys.executable, "-m", "pip", "install", "--upgrade"] + dependencies

        process = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(process.stdout)
        if process.stderr:
            logger.warning(process.stderr)
        logger.success("DroidBuilder dependencies updated successfully.")

    except FileNotFoundError:
        logger.error("pyproject.toml not found in the current directory.")
    except toml.TomlDecodeError:
        logger.error("Error decoding pyproject.toml. Please check its format.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to update dependencies (Exit Code: {e.returncode}):")
        if e.stdout:
            logger.error(f"Stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"Stderr: {e.stderr}")
        logger.info("Please check your network connection and ensure the dependencies are correctly specified.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
