from .. import config
from ..cli_logger import logger

def get_explicit_dependencies(conf):
    python_packages = conf.get("project", {}).get("requirements", {}).get("python_packages", [])
    system_packages = conf.get("project", {}).get("requirements", {}).get("system_packages", [])
    return python_packages, system_packages
