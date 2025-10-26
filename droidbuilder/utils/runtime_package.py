import requests
from ..cli_logger import logger
from ..utils import get_explicit_dependencies


def _resolve_from_pypi(name, version=None):
    """
    Resolves a Python package to a source URL using the PyPI API.
    """
    logger.info(f"  - Resolving Python package: {name}{f'=={version}' if version else ''}...")
    pypi_url = f"https://pypi.org/pypi/{name}/json"

    try:
        response = requests.get(pypi_url, timeout=10)
        response.raise_for_status()
        package_data = response.json()

        if version is None:
            version = package_data["info"]["version"]
            logger.info(f"  - No version specified for {name}. Found latest: {version}")

        release = package_data.get("releases", {}).get(version)
        if not release:
            logger.error(f"Could not find version {version} for {name} on PyPI.")
            return None, None

        # Find the source distribution (sdist)
        source_dist = None
        for dist in release:
            if dist["packagetype"] == "sdist":
                source_dist = dist
                break

        if not source_dist:
            logger.error(f"Could not find source distribution (sdist) for {name} {version}")
            return None, None

        download_url = source_dist["url"]
        
        logger.info(f"Resolved URL: {download_url}")
        return download_url, version

    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying PyPI API for {name}: {e}")
        return None, None
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing {name}: {e}")
        return None, None


def resolve_runtime_packages(conf):
    """
    Resolves runtime packages.
    It first checks the dependency mapping. If not found, it falls back to PyPI.
    """
    runtime_packages, _, dependency_mapping = get_explicit_dependencies(conf)

    resolved_packages = []

    logger.info("Resolving runtime packages...")
    for package in runtime_packages:
        name = package.get("name")
        version = package.get("version")
        url = None

        logger.info(f"  - Resolving: {name}{f'=={version}' if version else ''}")

        if name in dependency_mapping:
            url_template = dependency_mapping[name]
            logger.info("    - Found in dependency mapping.")
            if '{version}' in url_template:
                if version:
                    url = url_template.format(version=version)
                else:
                    logger.warning(f"    - Version needed for {name} but not specified. Searching online for latest.")
                    url = resolve_package_url(name)
            else:
                url = url_template
        else:
            logger.info("    - Not in dependency mapping. Querying PyPI...")
            url, new_version = _resolve_from_pypi(package)
            if new_version and not version:
                version = new_version  # Update version if one was found by PyPI

        if url:
            resolved_packages.append({"name": name, "version": version, "url": url})
            logger.info(f"    - Resolved to: {url}")
        else:
            logger.error(f"    - Failed to resolve {name}")

    return resolved_packages
