import click
from .. import installer

@click.command()
@click.pass_context
def doctor(ctx):
    """Check if all required tools are installed and the environment is set up correctly."""
    try:
        installer.check_environment()
    except Exception as e:
        logger.error(f"An error occurred during environment check: {e}")
        logger.info("Please check the log file for more details.")
