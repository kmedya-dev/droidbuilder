import requests
from ..cli_logger import logger

def resolve_buildtime_package(package_spec, dependency_mapping):
    """
    Resolves buildtime packages against the dependency mapping.
    If a package is not in the mapping, it attempts to find the URL.
    Returns a dictionary mapping package names to their URLs and versions.
    """
    resolved_packages = {}

        if '==' in package_spec:
            name, version = package_spec.split('==', 1)
        else:
            name, version = package_spec, None

        if name in resolved_packages:
            continue

        if name in dependency_mapping:
            url_template = dependency_mapping[name]
            
            # Format the URL if a version is available
            final_url = url_template
            if version:
                try:
                    final_url = url_template.format(version=version)
                except KeyError:
                    logger.warning(f"Version placeholder not found in URL for '{name}'. Using unformatted URL.")
            
            resolved_packages[name] = {"url": final_url, "version": version}
            logger.info(f"Found mapping for '{name}': {final_url}")
        else:
            logger.warning(f"Buildtime package '{name}' is not explicitly mapped in your droidbuilder.toml.")
            logger.error("Please add its URL to [app.dependency_mapping]")
            return None

    return resolved_packages
