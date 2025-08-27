import functools
import click
from .cli_logger import logger

def handle_exceptions(func):
    """A decorator to handle common exceptions for CLI commands."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except click.Abort:
            logger.warning("\nCommand aborted by user.")
        except FileNotFoundError as e:
            logger.error(f"Error: File not found - {e}")
        except Exception as e:
            logger.error(f"\nAn unexpected error occurred: {e}")
            logger.exception(e)
    return wrapper
