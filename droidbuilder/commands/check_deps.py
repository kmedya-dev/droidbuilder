import click
import os
import ast
import stdlib_list
from .. import config
from ..utils.dependencies import get_explicit_dependencies
from ..cli_logger import logger

STDLIB_MODULES = frozenset(stdlib_list.stdlib_list())

def find_python_imports(source_code):
    """
    Finds all top-level python imports in a given source code using the AST.
    """
    imports = set()
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
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
        if "venv" in file:
            continue
        # logger.debug(f"Processing file: {file}")
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            source_code = f.read()
            imports = find_python_imports(source_code)
            all_imports.update(imports)
            
    return list(all_imports)

@click.command("check-deps")
@click.pass_context
def check_deps(ctx):
    """Check for discrepancies between explicit and implicit dependencies."""
    path = ctx.obj["path"]
    conf = config.load_config(path=path)
    if not conf:
        logger.error("Error: Could not load project configuration.")
        return
    explicit_deps_str, _, _ = get_explicit_dependencies(conf)
    implicit_deps = get_implicit_python_dependencies(path)

    explicit_deps = {dep.split("==")[0].strip() for dep in explicit_deps_str}

    # Filter out standard library modules
    non_stdlib_implicit_deps = {dep for dep in implicit_deps if dep not in STDLIB_MODULES}

    # Filter out local modules
    local_modules = set()
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in ['.git', 'venv', '.venv']]
        if "__init__.py" in files:
            local_modules.add(os.path.basename(root))
    
    final_implicit_deps = non_stdlib_implicit_deps - local_modules - {'droidbuilder'}

    missing_deps = final_implicit_deps - explicit_deps
    
    if not missing_deps:
        logger.success("All imported packages are listed in droidbuilder.toml.")
    else:
        logger.warning("Found imported packages not listed in droidbuilder.toml:")
        for dep in sorted(list(missing_deps)):
            logger.warning(f"  - {dep}")
        logger.info("Please add them to the [project.requirements] section of your droidbuilder.toml file.")
