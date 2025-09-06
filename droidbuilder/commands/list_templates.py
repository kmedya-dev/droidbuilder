import click
import os
from droidbuilder.cli_logger import logger

@click.command(name="list-templates")
@click.pass_context
def list_templates(ctx):
    """List available templates."""
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    logger.info("Available templates:")
    try:
        if not os.path.exists(templates_dir):
            logger.error(f"Error: Templates directory not found at {templates_dir}. This might indicate a corrupted installation.")
            return
        for item in os.listdir(templates_dir):
            logger.info(item)
    except FileNotFoundError: # This should ideally be caught by os.path.exists, but keeping for robustness
        logger.error(f"Error: Templates directory not found at {templates_dir}. This might indicate a corrupted installation.")
    except PermissionError:
        logger.error(f"Error: Permission denied to access templates directory at {templates_dir}. Please check your permissions.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while listing templates: {e}")
        logger.exception(*sys.exc_info())
