import click
import os
from ..cli_logger import logger
from ..tools.installer import install

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")

@click.command()
@click.argument('url')
@click.option('--name', default=None, help='Optional: Name to use for the extracted package directory.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def install(url, name, dest_dir, verbose):
    """
    Installs a package from a direct URL by downloading and extracting it.
    """
    base_filename = url.split('/')[-1].split('.')[0]
    # Use provided package_name for extraction directory if available, otherwise use derived base_filename
    final_extract_name = name if name else base_filename

    if not dest_dir:
        dest_dir = os.path.join(INSTALL_DIR, "sources", final_extract_name)

    logger.info(f"Installing from {url} to {dest_dir}...")
    if install(url, dest_dir, final_extract_name, verbose=verbose):
        logger.success("Installation complete.")
    else:
        logger.error("Installation failed.")
