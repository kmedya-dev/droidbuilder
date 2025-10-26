import click
from ..cli_logger import logger
from ..utils import run_shell_command

@click.command("search-code")
@click.argument('pattern')
def search_code(pattern):
    """Search for a string in the project's source code."""
    search_dir = "."

    logger.info(f"Searching for '{pattern}' in '{search_dir}'...")
    try:
        command = [
            "grep",
            "-r",
            "-n",
            "--color=always",
            "--exclude-dir=.git",
            "--exclude-dir=venv",
            pattern,
            search_dir
        ]
        stdout, stderr, return_code = run_shell_command(command)

        if return_code == 0:
            click.echo(stdout)
        elif return_code == 1:
            logger.warning(f"No results found for '{pattern}'.")
        else:
            logger.error(f"An error occurred during search: {stderr}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
