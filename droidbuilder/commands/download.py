import click
from ..cli_logger import logger
from ..downloader import download_from_url

@click.command()
@click.argument('url')
@click.option('--package-name', default=None, help='Optional: Name to use for the extracted package directory.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def download(url, package_name, verbose):
    """
    Downloads a file from a direct URL and extracts it.
    """
    extracted_path = download_from_url(url, package_name, verbose)

    if extracted_path:
        logger.success(f"Successfully downloaded and extracted to {extracted_path}")
    else:
        logger.error(f"Failed to download and extract from {url}")
