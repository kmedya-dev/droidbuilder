import os
import glob
from ..cli_logger import logger
from ..utils.command_executor import run_shell_command

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
    patches_dir = config.get("build", {}).get("patches")

    if patches_dir and os.path.isdir(patches_dir):
        patch_pattern = os.path.join(patches_dir, f"{package_name}*.patch")
        patch_files = glob.glob(patch_pattern)

        if patch_files:
            logger.info(f"  - Applying patches for {package_name} from {patches_dir}...")
            for patch_path in patch_files:
                logger.info(f"    - Applying patch: {os.path.basename(patch_path)}")
                command = f"patch -p1 -i {patch_path}"
                result = run_shell_command(
                    command,
                    description=f"Applying patch {os.path.basename(patch_path)}",
                    cwd=package_source_path
                )

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
        logger.info(f"  - 'build.patches' directory not specified or found. Skipping patches for {package_name}.")

    return True
