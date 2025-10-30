import click
import os
import re

@click.command("search-code")
@click.argument('pattern')
@click.option('--ext', default='', help='File extension to search in.')
@click.pass_context
def search_code(ctx, pattern, ext):
    """Search for a regex pattern in the files of the project."""
    path = ctx.obj["path"]
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(ext):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                click.echo(f'{filepath}:{i}:{line.strip()}')
                except Exception as e:
                    click.echo(f"Error reading file {filepath}: {e}", err=True)
