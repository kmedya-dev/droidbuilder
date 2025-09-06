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
    try:
        with open(os.path.join(ctx.obj["path"], config_module.CONFIG_FILE), 'r') as f:
            click.echo(f.read())
    except IOError as e:
        logger.error(f"Error reading droidbuilder.toml: {e}")
        logger.info("Please check file permissions.")

@config.command()
@click.pass_context
def edit(ctx):
    """Edit the droidbuilder.toml file in your default editor."""
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return
    try:
        click.edit(filename=os.path.join(ctx.obj["path"], config_module.CONFIG_FILE))
    except Exception as e:
        logger.error(f"Error editing droidbuilder.toml: {e}")
        logger.info("Please ensure your default editor is configured correctly and has necessary permissions.")
