from .. import config
from ..cli_logger import logger

def get_explicit_dependencies(conf):
    app_config = conf.get("app", {})
    dependency = app_config.get("dependency", {})
    dependency_mapping = app_config.get("dependency_mapping", {})

    runtime_packages_str = dependency.get("runtime_packages", [])
    buildtime_packages_str = dependency.get("buildtime_packages", [])

    runtime_packages = [_parse_package_string(pkg) for pkg in runtime_packages_str]
    buildtime_packages = [_parse_package_string(pkg) for pkg in buildtime_packages_str]

    return runtime_packages, buildtime_packages, dependency_mapping

def _parse_package_string(pkg_str):
    """Parses a package string like 'name==version' or 'name'."""
    if "==" in pkg_str:
        name, version = pkg_str.split("==", 1)
        return name, version
    return pkg_str, None

