import click
import os
from .. import config as config_module
from ..cli_logger import logger

@click.group()
@click.pass_context
def config(ctx):
    """View or edit the droidbuilder.toml configuration file."""
    pass

@config.command()
@click.pass_context
def view(ctx):
    """View the contents of the droidbuilder.toml file."""
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return
    config_file_path = os.path.join(ctx.obj["path"], config_module.CONFIG_FILE)
    try:
        with open(config_file_path, 'r') as f:
            click.echo(f.read())
    except IOError as e:
        logger.error(f"Error reading droidbuilder.toml at {config_file_path}: {e}")
        logger.info("Please check file permissions.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while viewing droidbuilder.toml: {e}")
        logger.exception(*sys.exc_info())

@config.command()
@click.pass_context
def edit(ctx):
    """Edit the droidbuilder.toml file in your default editor."""
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return
    config_file_path = os.path.join(ctx.obj["path"], config_module.CONFIG_FILE)
    try:
        click.edit(filename=config_file_path)
    except click.ClickException as e:
        logger.error(f"Click error editing droidbuilder.toml: {e}")
        logger.info("This might indicate an issue with your editor configuration or environment variables.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while editing droidbuilder.toml: {e}")
        logger.info("Please ensure your default editor is configured correctly and has necessary permissions.")
        logger.exception(*sys.exc_info())
