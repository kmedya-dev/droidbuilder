import requests
from ..cli_logger import logger

def resolve_runtime_package(package_name, version=None):
    """
    Resolves a Python package to a source URL using the PyPI API.
    """
    logger.info(f"  - Resolving Python package: {package_name}{f'=={version}' if version else ''}...")
    pypi_url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = requests.get(pypi_url)
        response.raise_for_status()
        package_data = response.json()

        if version is None:
            version = package_data["info"]["version"]
            logger.info(f"  - No version specified for {package_name}. Found latest: {version}")

        release = package_data.get("releases", {}).get(version)
        if not release:
            logger.error(f"Could not find version {version} for {package_name} on PyPI.")
            return None, None

        # Find the source distribution (sdist)
        source_dist = None
        for dist in release:
            if dist["packagetype"] == "sdist":
                source_dist = dist
                break

        if not source_dist:
            logger.error(f"Could not find source distribution (sdist) for {package_name} {version}")
            return None, None

        download_url = source_dist["url"]
        
        logger.info(f"Resolved URL: {download_url}")
        return download_url, version

    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying PyPI API for {package_name}: {e}")
        return None, None
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing {package_name}: {e}")
        return None, None
