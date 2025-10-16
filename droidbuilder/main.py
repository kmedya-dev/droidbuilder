import click
from . import commands
import inspect


@click.group()
@click.option("--path", "-p", default=".", help="Path to the project directory.")
@click.pass_context
def cli(ctx, path):
    """DroidBuilder CLI tool."""
    ctx.obj = {"path": path}

for name, command in inspect.getmembers(commands, lambda member: isinstance(member, click.Command)):
    cli.add_command(command)

if __name__ == '__main__':
    try:
        cli()
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
        click.echo("Please report this issue to the DroidBuilder developers.", err=True)
