
import os
import re
import sys
from .config import load_config
from .cli_logger import logger
import stdlib_list

import ast

STDLIB_MODULES = frozenset(stdlib_list.stdlib_list())

def get_explicit_dependencies(path="."):
    """
    Loads the droidbuilder.toml file and returns the python and system packages.
    """
    config = load_config(path)
    if not config:
        return [], []

    python_packages = config.get("project", {}).get("requirements", [])
    system_packages = config.get("project", {}).get("system_packages", [])

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
    Gets all python dependencies in a given path.
    """
    explicit_deps, _ = get_explicit_dependencies(path)
    implicit_deps = get_implicit_python_dependencies(path)
    
    all_deps = set(explicit_deps)
    all_deps.update(implicit_deps)
    
    # Filter out standard library modules
    final_deps = [dep for dep in all_deps if dep not in STDLIB_MODULES]

    # Filter out local modules
    local_modules = []
    for root, dirs, _ in os.walk(path):
        for dir in dirs:
            if os.path.exists(os.path.join(root, dir, "__init__.py")):
                local_modules.append(dir)

    final_deps = [dep for dep in final_deps if dep not in local_modules]

    # Filter out empty strings
    final_deps = [dep for dep in final_deps if dep]
    
    return final_deps

