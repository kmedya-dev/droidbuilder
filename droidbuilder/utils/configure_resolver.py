import os
import sys
import shlex

from ..cli_logger import logger

# This map is needed for meson configuration.
ARCH_MAP = {
    "arm64-v8a": ["aarch64-linux-android", "aarch64", "aarch64"],
    "armeabi-v7a": ["armv7a-linux-androideabi", "arm", "armv7a"],
    "x86": ["i686-linux-android", "x86", "i686"],
    "x86_64": ["x86_64-linux-android", "x86_64", "x86_64"],
}


def resolve_config_type(
    package_name: str,
    package_config: dict,
    package_source_path: str,
    arch: str,
    ndk_api: str,
    install_dir: str,
    cflags: str = "",
    ldflags: str = "",
    cc: str = "",
    cxx: str = "",
    ar: str = "",
    strip: str = "",
    ndk_root: str = "",
    sysroot: str = "",
) -> dict:
    """
    This module only resolves configuration type; build execution is elsewhere.

    Accepts a package configuration object and resolves the appropriate build commands
    based on its 'config_type' attribute.

    Args:
        package_config (dict): The configuration object for the package, expected to have a 'config_type' key.
        package_name (str): The name of the package.
        package_source_path (str): The absolute path to the package's source directory.
        arch (str): The target architecture (e.g., "arm64-v8a").
        ndk_api (str): The Android NDK API level.
        install_dir (str): The installation directory for the package.
        build_triplet (str): The build triplet for the host system.
        host_triplet (str): The host triplet for the target architecture.

    Returns:
        dict: A dictionary containing 'pre_configure_command', 'clean_command', 'configure_command', 'build_command', and 'install_command' lists.
              Returns empty lists if no suitable configuration is found or an unsupported type is given.

    Raises:
        ValueError: If an unsupported config_type is provided.
    """
    config_type = package_config.get("config_type", "").lower()
    if config_type:
        logger.info(f"Resolving configuration for {package_name} with config_type: {config_type}")
    else:
        logger.info(f"Resolving configuration for {package_name} with auto-detection.")

    clean_cmd = []
    configure_cmd = []
    build_cmd = []
    install_cmd = []


    if config_type == "meson":
        logger.info(f"  - Generating Meson build commands for {package_name}.")

        meson_cpu_family = ARCH_MAP[arch][1]
        meson_cpu = ARCH_MAP[arch][2]

        build_dir = os.path.join(package_source_path, "build")
        cross_file_path = os.path.join(package_source_path, f"meson-cross-{arch}.ini")

        with open(cross_file_path, "w") as f:
            f.write("[binaries]")
            f.write(f"c = '{cc}'")
            f.write(f"cpp = '{cxx}'")
            f.write(f"ar = '{ar}'")
            f.write(f"strip = '{strip}'")
            f.write("")
            f.write("[host_machine]")
            f.write("system = 'android'")
            f.write(f"cpu_family = '{meson_cpu_family}'")
            f.write(f"cpu = '{meson_cpu}'")
            f.write("endian = 'little'")
            f.write("")
            f.write("[properties]")
            f.write(f"sys_root = '{sysroot}'")

        configure_cmd = [
            "meson", "setup", build_dir,
            f"--prefix={install_dir}",
            f"--cross-file={cross_file_path}",
            "--buildtype=release",
        ]

        build_cmd = ["meson", "compile", "-C", build_dir]
        install_cmd = ["meson", "install", "-C", build_dir]
        clean_cmd = ["rm", "-rf", build_dir, cross_file_path]

    elif config_type == "pip":
        logger.info(f"  - Generating pip install command for {package_name}.")
        configure_cmd = []
        build_cmd = []
        install_cmd = [
            os.path.join(install_dir, "bin", "python3"), # Path to target Python interpreter
            "-m",
            "pip",
            "install",
            "--no-deps", # Do not install dependencies, they should be handled by droidbuilder
            "--prefix", install_dir,
            package_source_path,
        ]
    elif config_type is None:
        logger.warning(f"  - No build system found for {package_name}. It will not be configured or built.")
    else:
        logger.error(f"Unsupported config_type: {config_type} for package {package_name}.")


    return {
        "clean_command": clean_cmd,
        "configure_command": configure_cmd,
        "build_command": build_cmd,
        "install_command": install_cmd,
    }
