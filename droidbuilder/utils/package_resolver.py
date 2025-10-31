import re
import os
import sys
import requests
from typing import Optional
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, quote_plus, unquote # Added quote_plus, unquote
from ..cli_logger import logger
from .dependencies import get_explicit_dependencies


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

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to perform web search: {e}")
        return None

    logger.warning(f"Could not find tarball for {name} (version: {version or 'latest'}) after checking all search results.")
    return None


def _resolve_from_pypi(name, version=None):
    """
    Resolves a Python package to a source URL using the PyPI API.
    """
    logger.info(f"  - Resolving Python package: {name}{f'=={version}' if version else ''}...")
    pypi_url = f"https://pypi.org/pypi/{name}/json"

    try:
        response = requests.get(pypi_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if version:
            if version not in data["releases"]:
                logger.warning(f"Version {version} not found for {name}. Available versions: {list(data['releases'].keys())}")
                return None, None
            release_data = data["releases"][version]
        else:
            # Get the latest version
            latest_version = data["info"]["version"]
            release_data = data["releases"][latest_version]
            version = latest_version

        for file_info in release_data:
            if file_info["packagetype"] == "sdist":
                logger.info(f"Found source distribution for {name}=={version}: {file_info['url']}")
                return file_info["url"], version

        logger.warning(f"No source distribution found for {name}=={version} on PyPI.")
        return None, None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying PyPI API for {name}: {e}")
        return None, None

    except Exception as e:
        logger.error(f"An unexpected error occurred while processing {name}: {e}")
        return None, None

def resolve_packages(conf):
    """
    Resolves packages.
    It first checks the dependency mapping. If not mapped, try with PyPI. If not found, it falls back to search online.
    """
    resolved_packages = {}
    runtime_packages, buildtime_packages, dependency_mapping = get_explicit_dependencies(conf)

    all_packages = runtime_packages + buildtime_packages

    for package in all_packages:
        name = package["name"]
        version = package["version"]
        logger.info(f"Resolving {name}{f'=={version}' if version else ''}...")

        # 1. Check dependency mapping
        if name in dependency_mapping:
            url = dependency_mapping[name]
            logger.info(f"  - Resolved from dependency_mapping: {url}")
            resolved_packages[name] = {"url": url, "version": version}
            continue

        # 2. Try PyPI
        url, resolved_version = _resolve_from_pypi(name, version)
        if url:
            resolved_packages[name] = {"url": url, "version": resolved_version}
            continue

        # 3. Fallback to web search
        logger.info(f"Could not resolve {name} from PyPI. Falling back to web search.")
        url = resolve_package_url(name, version)
        if url:
            resolved_packages[name] = {"url": url, "version": version}
        else:
            logger.error(f"Failed to resolve package: {name}")

    return url, version
