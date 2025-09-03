import click
from ..cli_logger import logger, get_latest_log_file

@click.command()
def log():
    """Display the latest log file."""
    latest_log = get_latest_log_file()
    if not latest_log:
        logger.error("No log files found.")
        return

    logger.info(f"Displaying log file: {latest_log}")
    with open(latest_log, 'r') as f:
        logger.info(f.read())
