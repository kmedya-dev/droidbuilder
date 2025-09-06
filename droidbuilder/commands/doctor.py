import click
from .. import installer
from ..cli_logger import logger # Import logger

@click.command()
@click.pass_context
def doctor(ctx):
    """Check if all required tools are installed and the environment is set up correctly."""
    logger.info("Running environment check...")
    try:
        if installer.check_environment():
            logger.success("Environment check completed successfully.")
        else:
            logger.error("Environment check found issues. Please review the warnings/errors above.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during environment check: {e}")
        logger.info("Please check the log file for more details and report this issue to the DroidBuilder developers if it persists.")
        logger.exception(*sys.exc_info())
