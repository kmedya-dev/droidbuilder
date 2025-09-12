import click
import os
import sys
import json
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

@config.command()
@click.pass_context
def list(ctx):
    """List all configuration keys and values."""
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return
    click.echo(json.dumps(conf, indent=4))

@config.command()
@click.argument('key')
@click.pass_context
def get(ctx, key):
    """Get a value from the droidbuilder.toml file."""
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return

    keys = key.split('.')
    value = conf
    try:
        for k in keys:
            value = value[k]
        click.echo(value)
    except (KeyError, TypeError):
        logger.error(f"Error: Key '{key}' not found in droidbuilder.toml")

@config.command()
@click.argument('key')
@click.argument('value')
@click.pass_context
def set(ctx, key, value):
    """Set a value in the droidbuilder.toml file."""
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return
    
    keys = key.split('.')
    d = conf
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value
    
    if config_module.save_config(conf, path=ctx.obj["path"]):
        logger.info(f"Set '{key}' to '{value}'")

@config.command()
@click.argument('key')
@click.pass_context
def unset(ctx, key):
    """Remove a key from the droidbuilder.toml file."""
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return

    keys = key.split('.')
    d = conf
    try:
        for k in keys[:-1]:
            d = d[k]
        del d[keys[-1]]
        if config_module.save_config(conf, path=ctx.obj["path"]):
            logger.info(f"Unset '{key}'")
    except (KeyError, TypeError):
        logger.error(f"Error: Key '{key}' not found in droidbuilder.toml")
