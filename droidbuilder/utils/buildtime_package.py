import requests
from ..cli_logger import logger

def resolve_dependencies_recursively(packages, dependency_mapping):
    """
    Resolves buildtime packages against the dependency mapping.
    If a package is not in the mapping, it attempts to find the URL.
    Returns a dictionary mapping package names to their URLs.
    """
    resolved_packages = {}

    for package_spec in packages:
        if '==' in package_spec:
            name, version = package_spec.split('==', 1)
        else:
            name, version = package_spec, None

        if name in resolved_packages:
            continue

        if name in dependency_mapping and dependency_mapping[name]:
            resolved_packages[name] = {"url": dependency_mapping[name]}
            logger.info(f"Found mapping for '{name}': {dependency_mapping[name]}")
        else:
            logger.warning(f"buildtime package '{name}' is not explicitly mapped in your droidbuilder.toml.")
            logger.error("Please add its URL to [app.dependency_mapping]")
            return None

    return resolved_packages
