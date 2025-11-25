import click
from .dev_kit import dev_kit
from .package import package

@click.group()
def install():
    """Commands for installing tools and packages."""
    pass

install.add_command(dev_kit)
install.add_command(package)
