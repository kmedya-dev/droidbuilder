
import click
from ..dependencies import get_explicit_dependencies
from ..cli_logger import logger

@click.command(name="search-packages")
@click.argument("package_name")
@click.pass_context
def search_packages(ctx, package_name):
    """Search for packages in the local repository."""
    logger.info(f"Searching for package: {package_name}")

    python_packages, system_packages = get_explicit_dependencies(ctx.obj["path"])
    
    found = False
    for package in python_packages:
        if package_name in package:
            logger.info(f"Found python package: {package}")
            found = True
            
    for package in system_packages:
        if package_name in package[0]:
            logger.info(f"Found system package: {package[0]}")
            found = True

    if not found:
        logger.info("Package not found.")
