import os
import re
import sys
from .config import load_config
from .cli_logger import logger
import stdlib_list

import ast

STDLIB_MODULES = frozenset(stdlib_list.stdlib_list())

def parse_dependency(dep_string):
    """Parses a dependency string into a name and version."""
    match = re.match(r"([^=]+)==(.+)", dep_string)
    if match:
        return match.groups()
    return dep_string, None

def get_explicit_dependencies(path="."):
    """
    Loads the droidbuilder.toml file and returns the python and system packages.
    """
    config = load_config(path)
    if not config:
        return [], []

    requirements = config.get("project", {}).get("requirements", {})
    python_packages = requirements.get("python_packages", [])
    system_packages_str = requirements.get("system_packages", [])
    
    system_packages = []
    for pkg_str in system_packages_str:
        system_packages.append(parse_dependency(pkg_str))

    return python_packages, system_packages

def find_python_imports(source_code):
    """
    Finds all top-level python imports in a given source code using the AST.
    """
    imports = set()
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        # Handle cases where the source code might be incomplete or malformed
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module: # Exclude relative imports like 'from . import foo'
                imports.add(node.module.split('.')[0])
    return list(imports)

def get_project_python_files(path="."):
    """
    Gets all python files in a given path.
    """
    python_files = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files

def get_implicit_python_dependencies(path="."):
    """
    Gets all implicit python dependencies in a given path.
    """
    python_files = get_project_python_files(path)
    
    all_imports = set()
    for file in python_files:
        # Ignore venv directory
        if "venv" in file:
            continue
        with open(file, "r") as f:
            source_code = f.read()
            imports = find_python_imports(source_code)
            all_imports.update(imports)
            
    return list(all_imports)

def get_python_dependencies(path="."):
    """
    Gets all python dependencies, prioritizing explicit requirements.
    """
    explicit_deps_str, _ = get_explicit_dependencies(path)
    implicit_deps = get_implicit_python_dependencies(path)

    # Use a dictionary to handle version pinning from explicit requirements
    final_deps_map = {}

    # First, add all implicitly found dependencies without version
    for dep in implicit_deps:
        final_deps_map[dep] = dep

    # Then, process explicit dependencies, which may have versions, overwriting
    # the implicit entry if it exists.
    for dep_str in explicit_deps_str:
        package_name = dep_str.split("==")[0].strip()
        final_deps_map[package_name] = dep_str

    # Filter out standard library modules from the keys of the map
    deps_to_process = {name: dep for name, dep in final_deps_map.items() if name not in STDLIB_MODULES}

    # Filter out local modules
    local_modules = set()
    for root, dirs, _ in os.walk(path):
        # Exclude common virtualenv and VCS directories
        dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '.git', '__pycache__']]
        for d in dirs:
            if os.path.exists(os.path.join(root, d, "__init__.py")):
                # Consider a directory a local module if it's in the project root
                if root == path:
                    local_modules.add(d)

    # Reconstruct the final list, excluding local modules
    final_deps = [dep for name, dep in deps_to_process.items() if name not in local_modules]

    # Filter out any empty strings that might have slipped through
    final_deps = [dep for dep in final_deps if dep]

    return final_deps
