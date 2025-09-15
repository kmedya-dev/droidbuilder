import requests # Keep requests for now, might be used by other modules
from ..cli_logger import logger

# Removed resolve_system_package function

def resolve_dependencies_recursively(packages, dependency_mapping):
    """
    Resolves all dependencies for a list of packages.
    With Repology removed, all system packages must be explicitly mapped.
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

        if name not in dependency_mapping:
            logger.error(f"Error: System package '{name}' is not explicitly mapped in 'dependency_mapping'. "
                         "All system packages must be explicitly mapped.")
            return None # Indicate failure

    return list(resolved_packages)