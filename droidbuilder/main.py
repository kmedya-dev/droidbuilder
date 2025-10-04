import click
from .commands.list_files import list_files
from .commands.list_templates import list_templates
from .commands.init import init
from .commands.install_tools import install_tools
from .commands.build import build
from .commands.clean import clean
from .commands.list_tools import list_tools
from .commands.list_droids import list_droids
from .commands.uninstall import uninstall
from .commands.update import update
from .commands.search import search

from .commands.doctor import doctor
from .commands.config import config
from .commands.version import version
from .commands.log import log
from .commands.update_deps import update_deps

from .commands.check_deps import check_deps

@click.group()
@click.option("--path", "-p", default=".", help="Path to the project directory.")
@click.pass_context
def cli(ctx, path):
    """DroidBuilder CLI tool."""
    ctx.obj = {"path": path}

cli.add_command(list_files)
cli.add_command(list_templates)
cli.add_command(init)
cli.add_command(install_tools)
cli.add_command(build)
cli.add_command(clean)
cli.add_command(list_tools)
cli.add_command(list_droids)
cli.add_command(uninstall)
cli.add_command(update)
cli.add_command(search)
cli.add_command(doctor)
cli.add_command(config)
cli.add_command(version)
cli.add_command(log)
cli.add_command(update_deps)


cli.add_command(check_deps)

if __name__ == '__main__':
    try:
        cli()
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
        click.echo("Please report this issue to the DroidBuilder developers.", err=True)
