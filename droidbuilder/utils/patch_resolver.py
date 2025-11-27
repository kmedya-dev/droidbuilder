import os
import glob
import sys
from ..cli_logger import logger
from ..utils import run_shell_command

def apply_patches(package_name: str, package_source_path: str, config: dict) -> bool:
    """
    Applies patches to a given package's source directory.

    Args:
        package_name: The name of the package to patch.
        package_source_path: The absolute path to the package's source directory.
        config: The global configuration dictionary.

    Returns:
        True if all applicable patches were applied successfully or no patches were found, False otherwise.
    """
    patches_dir = config.get("app", {}).get("dependency", {}).get("patch_dir")
    if patches_dir:
        # Resolve patches_dir to an absolute path relative to the current working directory
        patches_dir = os.path.abspath(os.path.join(os.getcwd(), patches_dir))

    if patches_dir and os.path.isdir(patches_dir):
        patch_pattern = os.path.join(patches_dir, f"{package_name}-*")
        patch_files = glob.glob(patch_pattern)

        if patch_files:
            logger.info(f"  - Found patches for {package_name} in {patches_dir}...")
            for patch_path in patch_files:
                if patch_path.endswith(".py"):
                    # If the file is a Python script, run it with the current interpreter
                    command = [sys.executable, patch_path]
                    description = f"Executing patch script {os.path.basename(patch_path)}"
                elif patch_path.endswith(".sh"):
                    # If the file is a Shell script
                    command = ["bash", patch_path]
                    description = f"Executing patch script {os.path.basename(patch_path)}"
                elif os.path.isfile(patch_path) and os.access(patch_path, os.X_OK):
                    # If the file is an executable script, run it directly
                    command = [patch_path]
                    description = f"Executing patch script {os.path.basename(patch_path)}"
                else:
                    # Otherwise, assume it's a traditional patch file
                    command = ["patch", "-p1", "-i", patch_path]
                    description = f"Applying patch: {os.path.basename(patch_path)}"

                result = run_shell_command(
                    command,
                    description=description,
                    cwd=package_source_path
                )

                if result['stdout']:
                    logger.debug(result['stdout'])
                if result['returncode'] != 0:
                    logger.error(f"    - Failed to apply patch {os.path.basename(patch_path)}: (Exit Code: {result['returncode']})")
                    if result.get('stdout'):
                        logger.error(f"      Patch Stdout:\n{result['stdout']}")
                    if result.get('stderr'):
                        logger.error(f"      Patch Stderr:\n{result['stderr']}")
                    return False
        else:
            logger.info(f"  - No patches found for {package_name} in {patches_dir}.")
    else:
        logger.info(f"  - 'app.dependency.patch_dir' not specified or found. Skipping patches for {package_name}.")

    return True
