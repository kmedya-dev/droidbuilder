import os
import click

@click.command()
@click.argument('pattern')
def search_code(pattern):
    """Search for a pattern in the codebase."""
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith(('.py', '.toml', '.md')):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, 1):
                        if pattern in line:
                            click.echo(f'{path}:{i}:{line.strip()}')