from .. import config
from ..cli_logger import logger

def get_explicit_dependencies(conf):
    app_config = conf.get("app", {})
    dependency = app_config.get("dependency", {})
    dependency_mapping = app_config.get("dependency_mapping", {})

    runtime_packages = []
    buildtime_packages = []

    if isinstance(dependency, dict):
        runtime_packages = dependency.get("runtime_packages", [])
        buildtime_packages = dependency.get("buildtime_packages", [])

    return runtime_packages, buildtime_packages, dependency_mapping
