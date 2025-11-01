import os
import requests
from urllib.parse import quote_plus
from ..cli_logger import logger

def resolve_package_url(name, version=None):
    search_query = f"{name}{f' {version}' if version else ''} download source tar.gz"
    logger.info(f"Searching for '{search_query}' using Google Custom Search...")

    api_key = os.environ.get("GOOGLE_API_KEY")
    cx = os.environ.get("GOOGLE_CX")

    if not api_key or not cx:
        logger.error("Google API key or CX not found. Please set them as environment variables.")
        return None

    try:
        search_url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={quote_plus(search_query)}"
        response = requests.get(search_url)
        response.raise_for_status()
        search_results = response.json()

        if "items" in search_results:
            for item in search_results["items"]:
                if item["link"].endswith(".tar.gz"):
                    logger.info(f"  - Found URL: {item['link']}")
                    return item["link"]
        
        logger.warning(f"Could not find a .tar.gz download link for {name} via web search.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error during web search for {name}: {e}")
        return None


def _resolve_from_pypi(name, version=None):
    """
    Resolves a package to a source URL using the PyPI API.
    """
    pypi_url = f"https://pypi.org/pypi/{name}/json"
    if version:
        pypi_url = f"https://pypi.org/pypi/{name}/{version}/json"

    try:
        response = requests.get(pypi_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        urls = data.get("urls", [])
        for url_info in urls:
            if url_info.get("packagetype") == "sdist" and url_info["url"].endswith(".tar.gz"):
                logger.info(f"  - Found PyPI source distribution: {url_info['url']}")
                return url_info["url"], data["info"]["version"]
        
        return None, None

    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not resolve {name} from PyPI: {e}")
        return None, None

def resolve_package(name, version, dependency_mapping):
    """
    Resolves a package to a source URL and a specific version.
    """
    logger.info(f"Resolving package: {name}{f' version {version}' if version else ''}")

    # 1. Check dependency_mapping in droidbuilder.toml
    if name in dependency_mapping:
        logger.info(f"  - Found '{name}' in dependency_mapping.")
        url_template = dependency_mapping[name]
        if version:
            url = url_template.format(version=version)
        else:
            # This might fail if version is required for the URL.
            # Assuming if no version is specified, the URL is as-is.
            url = url_template
        return name, url, version # Assuming version is correct

    # 2. Try to resolve from PyPI
    logger.info(f"  - Attempting to resolve '{name}' from PyPI...")
    pypi_url, pypi_version = _resolve_from_pypi(name, version)
    if pypi_url:
        return name, pypi_url, pypi_version

    # 3. Fallback to web search for a download link
    logger.info(f"  - PyPI resolution failed. Falling back to web search for '{name}'.")
    web_url = resolve_package_url(name, version)
    if web_url:
        # We don't know the exact version from the web url, so we return what was passed.
        return name, web_url, version

    # 4. If nothing works
    logger.error(f"Failed to resolve package '{name}'. Could not find a downloadable source URL.")
    return name, None, version
