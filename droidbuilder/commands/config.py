import click
import os
import sys
import json
from .. import config as config_module
from ..cli_logger import logger

@click.command()
@click.argument('key', required=False)
@click.argument('value', required=False)
@click.option('--edit', is_flag=True, help='Edit the droidbuilder.toml file in your default editor.')
@click.option('--list', is_flag=True, help='List all configuration keys and values.')
@click.option('--unset', is_flag=True, help='Remove a key from the droidbuilder.toml file.')
@click.pass_context
def config(ctx, key, value, edit, list, unset):
    """View or edit the droidbuilder.toml configuration file."""
    conf = config_module.load_config(path=ctx.obj["path"])
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return

    config_file_path = os.path.join(ctx.obj["path"], config_module.CONFIG_FILE)

    if edit:
        try:
            click.edit(filename=config_file_path)
        except click.ClickException as e:
            logger.error(f"Click error editing droidbuilder.toml: {e}")
            logger.info("This might indicate an issue with your editor configuration or environment variables.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while editing droidbuilder.toml: {e}")
            logger.info("Please ensure your default editor is configured correctly and has necessary permissions.")
            logger.exception(*sys.exc_info())
        return

    if list:
        click.echo(json.dumps(conf, indent=4))
        return

    if unset:
        if not key:
            logger.error("Error: Please provide a key to unset.")
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
        return

    if key and value:
        keys = key.split('.')
        d = conf
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        
        if config_module.save_config(conf, path=ctx.obj["path"]):
            logger.info(f"Set '{key}' to '{value}'")
        return

    if key:
        keys = key.split('.')
        v = conf
        try:
            for k in keys:
                v = v[k]
            click.echo(v)
        except (KeyError, TypeError):
            logger.error(f"Error: Key '{key}' not found in droidbuilder.toml")
        return

    try:
        with open(config_file_path, 'r') as f:
            click.echo(f.read())
    except IOError as e:
        logger.error(f"Error reading droidbuilder.toml at {config_file_path}: {e}")
        logger.info("Please check file permissions.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while viewing droidbuilder.toml: {e}")
        logger.exception(*sys.exc_info())