from .. import config
from ..cli_logger import logger

def get_explicit_dependencies(conf):
    project_config = conf.get("project", {})
    requirements = project_config.get("requirements", {})
    if isinstance(requirements, dict):
        python_packages = requirements.get("python_packages", [])
        system_packages = requirements.get("system_packages", [])
    else:
        python_packages = []
        system_packages = []

    dependency_mapping = requirements.get("dependency_mapping", {})

    return python_packages, system_packages, dependency_mapping
