import os
import subprocess
from ..cli_logger import logger
from ..utils import run_shell_command

def apply_patches(package_name: str, package_source_path: str, config: dict) -> bool:
    """
    Applies patches to a given package's source directory.

    Args:
        package_name: The name of the package to patch.
        package_source_path: The absolute path to the package's source directory.
        config: The global configuration dictionary, expected to contain patch definitions.

    Returns:
        True if all applicable patches were applied successfully or no patches were found, False otherwise.
    """
    patches_config = config.get("build", {}).get("patches", {})
    
    if package_name in patches_config:
        logger.info(f"  - Applying patches for {package_name}...")
        patch_files = patches_config[package_name]
        if isinstance(patch_files, str):
            patch_files = [patch_files]

        for patch_file_relative_path in patch_files:
            # Assuming patch files are relative to the project root
            patch_path = os.path.join(os.getcwd(), patch_file_relative_path)
            
            if os.path.exists(patch_path):
                logger.info(f"    - Applying patch: {patch_file_relative_path}")
                patch_command = ["patch", "-p1", "-i", patch_path]
                logger.debug(f"      Executing patch command: {' '.join(patch_command)}")
                result = run_shell_command(
                    patch_command,
                    description=f"    - Applying patch: {patch_file_relative_path}",
                    cwd=package_source_path
                )
                stdout = result["stdout"]
                stderr = result["stderr"]
                returncode = result["returncode"]
                if returncode != 0:
                    logger.error(f"    - Failed to apply patch {patch_file_relative_path}: (Exit Code: {returncode})")
                    if stdout:
                        logger.error(f"      Patch Stdout:\n{stdout}")
                    if stderr:
                        logger.error(f"      Patch Stderr:\n{stderr}")
                    return False
            else:
                logger.warning(f"    - Patch file not found: {patch_file_relative_path}. Skipping.")
    else:
        logger.info(f"  - No patches defined for {package_name}.")
        
    return True
