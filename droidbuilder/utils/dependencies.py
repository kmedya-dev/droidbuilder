from .. import config
from ..cli_logger import logger

def get_explicit_dependencies(conf):
    app_config = conf.get("app", {})
    dependency = app_config.get("dependency", {})
    dependency_mapping = app_config.get("dependency_mapping", {})

    python_packages = []
    system_packages = []

    if isinstance(dependency, dict):
        python_packages = dependency.get("python_packages", [])
        system_packages = dependency.get("system_packages", [])
    elif isinstance(dependency, list):
        # If 'dependency' is a list, assume it contains only python packages.
        python_packages = dependency

    return python_packages, system_packages, dependency_mapping
