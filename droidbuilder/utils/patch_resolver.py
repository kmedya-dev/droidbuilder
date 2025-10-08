import os
import subprocess
from ..cli_logger import logger

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
        for patch_file_relative_path in patches_config[package_name]:
            # Assuming patch files are relative to the project root
            patch_path = os.path.join(os.getcwd(), patch_file_relative_path)
            
            if os.path.exists(patch_path):
                logger.info(f"    - Applying patch: {patch_file_relative_path}")
                try:
                    # Use -p1 for stripping one leading component from file names
                    # Use -i to specify the patch file
                    subprocess.run(
                        ["patch", "-p1", "-i", patch_path],
                        check=True,
                        cwd=package_source_path,
                        capture_output=True,
                        text=True
                    )
                    logger.success(f"    - Successfully applied patch: {patch_file_relative_path}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"    - Failed to apply patch {patch_file_relative_path}: {e}")
                    if e.stdout:
                        logger.error(f"      Patch Stdout:\n{e.stdout}")
                    if e.stderr:
                        logger.error(f"      Patch Stderr:\n{e.stderr}")
                    return False
            else:
                logger.warning(f"    - Patch file not found: {patch_file_relative_path}. Skipping.")
    else:
        logger.info(f"  - No patches defined for {package_name}.")
        
    return True
