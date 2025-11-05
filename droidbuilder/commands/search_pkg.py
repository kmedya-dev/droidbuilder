import click
import argparse
import os
from ..cli_logger import logger
from ..utils.package_resolver import resolve_from_pypi, resolve_package_url

@click.command()
@click.argument('name')
@click.argument('version', required=False)
def search_pkg(name, version):
    """Searches for a package download URL."""

    logger.info(f"Attempting to resolve '{name}' from PyPI...")
    url, pypi_version = resolve_from_pypi(name, version)

    if url:
        logger.info(f"Found PyPI source distribution: {url}")
        logger.info(f"Version: {pypi_version}")
    else:
        logger.info(f"PyPI resolution failed. Falling back to web search for '{name}'.")
        url = resolve_package_url(name, version)

        if url:
            logger.info(f"Found download URL: {url}")
        else:
            logger.info(f"Could not find a download URL for {name} {version or ''}.")
