import os
import re
import requests
from urllib.parse import quote_plus
from ..cli_logger import logger

def _resolve_redirect(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        response.raise_for_status()
        logger.info(f"Followed redirect to: {response.url}")
        return response.url
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not follow redirect for {url}: {e}")
        return url


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
        # logger.info(f"search_results:{search_results}")

        if 'items' in search_results:
            for item in search_results['items']:
                if 'pagemap' in item and 'softwaresourcecode' in item['pagemap']:
                    for code in item['pagemap']['softwaresourcecode']:
                        if code.get('name', '').lower() == name.lower():
                            author = code.get('author')
                            if author:
                                logger.info(f"Found potential GitHub repository via softwaresourcecode: author='{author}', name='{name}'")
                                try:
                                    # Try to get from GitHub releases API
                                    if version:
                                        gh_api_url = f"https://api.github.com/repos/{author}/{name}/releases"
                                        gh_response = requests.get(gh_api_url)
                                        gh_response.raise_for_status()
                                        all_releases = gh_response.json()

                                        for release in all_releases:
                                            if version in release['tag_name']: # Check if version string is in tag_name
                                                if 'tarball_url' in release and release['tarball_url']:
                                                    logger.info(f"Found tarball via GitHub API for release tag {release['tag_name']}: {release['tarball_url']}")
                                                    return _resolve_redirect(release['tarball_url'])
                                    else: # No version specified, get latest
                                        gh_api_url = f"https://api.github.com/repos/{author}/{name}/releases/latest"
                                        gh_response = requests.get(gh_api_url)
                                        gh_response.raise_for_status()
                                        gh_data = gh_response.json()
                                        if 'tarball_url' in gh_data and gh_data['tarball_url']:
                                            logger.info(f"Found tarball via GitHub API for latest release: {gh_data['tarball_url']}")
                                            return _resolve_redirect(gh_data['tarball_url'])
                                except requests.exceptions.RequestException as gh_e:
                                    logger.warning(f"Could not fetch from GitHub API for {author}/{name}: {gh_e}")

        logger.warning(f"Could not find a .tar.gz download link for {name} via web search.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error during web search for {name}: {e}")
        return None


def resolve_from_pypi(name, version=None):
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
    if name.lower() in dependency_mapping:
        logger.info(f"  - Found '{name}' in dependency_mapping.")
        url_template = dependency_mapping[name.lower()]
        if '{version}' in url_template:
            if version:
                url = url_template.format(version=version)
            else:
                logger.error(f"'{name}' requires a version in dependency_mapping, but none was provided.")
                return name, None, None
        else:
            url = url_template

        # Try to extract version from URL if not provided
        if not version:
            match = re.search(r'(\d+\.\d+\.\d+)', url)
            if match:
                version = match.group(1)
        
        return name, url, version

    # 2. Try to resolve from PyPI
    logger.info(f"  - Attempting to resolve '{name}' from PyPI...")
    pypi_url, pypi_version = resolve_from_pypi(name, version)
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
