import click
from ..cli_logger import logger, get_latest_log_file

@click.command()
def log():
    """Display the latest log file."""
    latest_log = get_latest_log_file()
    if not latest_log:
        logger.info("No log files found.") # Changed from error to info as it's not necessarily an error
        return

    logger.info(f"Displaying log file: {latest_log}")
    try:
        with open(latest_log, 'r') as f:
            logger.info(f.read())
    except IOError as e:
        logger.error(f"Error reading log file {latest_log}: {e}")
        logger.info("Please check file permissions.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading log file {latest_log}: {e}")
        logger.exception(*sys.exc_info())
