import click
from .commands import *


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
cli.add_command(search_dependency)
cli.add_command(search_code)

if __name__ == '__main__':
    try:
        cli()
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
        click.echo("Please report this issue to the DroidBuilder developers.", err=True)
