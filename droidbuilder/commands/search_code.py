import click
import subprocess
from ..cli_logger import logger

@click.command("search-code")
@click.argument('pattern')
def search_code(pattern):
    """Search for a string in the project's source code."""
    logger.info(f"Searching for '{pattern}' in the project...")
    try:
        cmd = [
            "grep",
            "-r",
            "-n",
            "--color=always",
            "--exclude-dir=.git",
            "--exclude-dir=venv",
            pattern,
            "."
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            click.echo(result.stdout)
        else:
            logger.info("No results found.")
    except FileNotFoundError:
        logger.error("Error: 'grep' command not found. Please make sure it is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        if e.stdout:
            click.echo(e.stdout)
        if e.stderr:
            click.echo(e.stderr)
        if e.returncode != 1: # grep returns 1 if no lines are selected
            logger.error(f"Error executing grep: {e}")
