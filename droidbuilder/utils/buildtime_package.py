from ..cli_logger import logger
from .dependencies import get_explicit_dependencies
from .package_resolver import resolve_package_url


def resolve_buildtime_packages(conf):
    """
    Resolves buildtime packages against the dependency mapping.
    If a package is not in the mapping, it attempts to find the URL.
    """
    _, buildtime_packages, dependency_mapping = get_explicit_dependencies(conf)

    resolved_packages = []

    logger.info("Resolving buildtime packages...")
    for package in buildtime_packages:
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
                    url = resolve_package_url(name)  # Find latest
            else:
                url = url_template
        else:
            logger.info("    - Not in dependency mapping. Searching online...")
            url = resolve_package_url(name, version)

        if url:
            resolved_packages.append({"name": name, "version": version, "url": url})
            logger.info(f"    - Resolved to: {url}")
        else:
            logger.error(f"    - Failed to resolve {name}")

    return resolved_packages
