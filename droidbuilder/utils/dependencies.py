from .. import config
from ..cli_logger import logger

def get_explicit_dependencies(conf):
    requirements = conf.get("project", {}).get("requirements", {})
    if isinstance(requirements, dict):
        python_packages = requirements.get("python_packages", [])
        system_packages = requirements.get("system_packages", [])
    else:
        python_packages = []
        system_packages = []
    return python_packages, system_packages
