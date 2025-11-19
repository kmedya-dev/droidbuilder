import click
import os
from urllib.parse import urlparse
from ..cli_logger import logger
from ..tools.installer import install as install_package
from ..utils.package_resolver import resolve_package
from ..config import load_config

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")

def is_url(path):
    """Check if a given path is a URL."""
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

@click.command()
@click.argument('package')
@click.option('--version', default=None, help='Version of the package to install.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def install(package, version, verbose):
    """
    Installs a package from a direct URL or by resolving a package name.
    """
    config = load_config()
    dependency_mapping = config.get('dependencies', {})

    if is_url(package):
        url = package
        name = url.split('/')[-1].split('.')[0]
    else:
        name = package
        _, url, version = resolve_package(name, version, dependency_mapping)

    if not url:
        logger.error(f"Could not resolve package: {name}")
        return

    logger.info(f"Installing {name} from {url}...")

    dest_dir = os.path.join(INSTALL_DIR, "sources", name)
    installed_path = install_package(url, dest_dir, verbose=verbose)

    if installed_path:
        logger.success(f"Successfully installed {name} to {installed_path}")
    else:
        logger.error(f"Failed to install {name}")
