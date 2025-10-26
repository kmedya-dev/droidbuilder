from .. import config
from ..cli_logger import logger

def get_explicit_dependencies(conf):
    app_config = conf.get("app", {})
    dependency = app_config.get("dependency", {})
    dependency_mapping = app_config.get("dependency_mapping", {})

    runtime_packages = []
    buildtime_packages = []

    if isinstance(dependency, dict):
        runtime_packages_raw = dependency.get("runtime_packages", [])
        buildtime_packages_raw = dependency.get("buildtime_packages", [])

        for pkg_str in runtime_packages_raw:
            name, version = _parse_package_string(pkg_str)
            runtime_packages.append({"name": name, "version": version})

        for pkg_str in buildtime_packages_raw:
            name, version = _parse_package_string(pkg_str)
            buildtime_packages.append({"name": name, "version": version})

    return runtime_packages, buildtime_packages, dependency_mapping

def _parse_package_string(pkg_str):
    parts = pkg_str.split("==", 1)
    name = parts[0].strip()
    version = parts[1].strip() if len(parts) > 1 else None
    return name, version
