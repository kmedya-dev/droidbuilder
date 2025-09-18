import click
import json
from droidbuilder.utils.system_package import resolve_system_package, find_tarball
from droidbuilder.cli_logger import logger

@click.command()
@click.argument('package_spec')
def search(package_spec):
    """Search for the download URL of a system package."""
    if '==' in package_spec:
        package_name, version = package_spec.split('==', 1)
    else:
        package_name, version = package_spec, None

    logger.info(f"Attempting to resolve package '{package_name}' using system package manager...")
    homepage = resolve_system_package(package_name)

    if homepage:
        logger.info(f"Found homepage: {homepage}")
        tarball_url = find_tarball(homepage, package_name, version=version)
        if tarball_url:
            logger.success(f"Found tarball URL: {tarball_url}")
            click.echo(tarball_url)
        else:
            logger.warning(f"Could not find a tarball on the homepage for '{package_name}'.")
            logger.info("Initiating web search to find the official source tarball download.")
            search_query = f"{package_name} official source tarball download"
            print(json.dumps({"tool": "web_search", "query": search_query}))
            logger.info("Please review the web search results and confirm the official source if prompted.")
    else:
        logger.warning(f"Could not find homepage for '{package_name}' using system package manager.")
        logger.info("Initiating web search to find the official homepage or a suitable download link.")
        search_query = f"{package_name} official homepage download"
        # Special output for the Gemini agent to interpret as a tool call
        print(json.dumps({"tool": "web_search", "query": search_query}))
        logger.info("Please review the web search results and confirm the official homepage if prompted.")
