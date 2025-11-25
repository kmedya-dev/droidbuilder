import click
import os
from urllib.parse import urlparse
from ... import cli_logger as logger
from ...utils.package_resolver import resolve_package
from ... import config
from ...constants import MWD

from ...tools.installer import install as install_package




def is_url(path):
    """Check if a given path is a URL."""
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

@click.command()
@click.argument('package_name')
@click.option('--version', help='Specify the version of the package to install.')
@click.option('--verbose', is_flag=True, help='Enable verbose output.')
def package(package_name, version, verbose):
    """
    Installs a package from a direct URL or by resolving a package name.
    """
    conf = load_config()
    dependency_mapping = conf.get('app', {}).get('dependency_mapping', {})

    if is_url(package_name):
        url = package_name
        name = url.split('/')[-1].split('.')[0]
    else:
        name = package_name
        _, url, version = resolve_package(name, version, dependency_mapping)

    if not url:
        logger.error(f"Could not resolve package: {name}")
        return

    logger.info(f"Installing {name} from {url}...")

    dest_dir = os.path.join(MWD, "sources", name)
    installed_path = install_package(url, dest_dir, verbose=verbose)

    if installed_path:
        logger.success(f"Successfully installed {name} to {installed_path}")
    else:
        logger.error(f"Failed to install {name}")
