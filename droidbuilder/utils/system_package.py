import requests # Keep requests for now, might be used by other modules
from ..cli_logger import logger

# Removed resolve_system_package function

def resolve_dependencies_recursively(packages, dependency_mapping):
    """
    Resolves all dependencies for a list of packages.
    """
    resolved_packages = set()
    
    for package_spec in packages:
        if '==' in package_spec:
            name, version = package_spec.split('==', 1)
        else:
            name, version = package_spec, None

        if name in resolved_packages:
            continue

        resolved_packages.add(name)

    return list(resolved_packages)
