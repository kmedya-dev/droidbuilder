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
        for item in os.listdir(templates_dir):
            logger.info(item)
    except FileNotFoundError:
        logger.error(f"Error: Templates directory not found at {templates_dir}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
