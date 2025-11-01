import click
from ..cli_logger import logger
from ..utils import run_shell_command

@click.command("grep")
@click.argument('pattern')
def grep(pattern):
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
        result = run_shell_command(command)
        stdout = result["stdout"]
        stderr = result["stderr"]
        return_code = result["returncode"]

        if return_code == 0:
            click.echo(stdout)
        elif return_code == 1:
            logger.warning(f"No results found for '{pattern}'.")
        else:
            logger.error(f"An error occurred during search: {stderr}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
