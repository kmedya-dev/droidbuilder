import os
import sys
import shlex

from ..cli_logger import logger

def resolve_config_type(package_config: dict, package_name: str, package_source_path: str, arch: str, ndk_api: str, install_dir: str, build_triplet: str, host_triplet: str, cflags: str = "", ldflags: str = "", cc: str = "", cxx: str = "", ar: str = "", ld: str = "", ranlib: str = "", strip: str = "", readelf: str = "", ndk_root: str = "") -> dict:
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
    config_type = package_config.get("config_type").lower()
    logger.info(f"Resolving configuration for {package_name} with config_type: {config_type}")
    pre_configure_cmd = []
    configure_cmd = []
    clean_cmd = ["make", "clean"]
    build_cmd = ["make", "-j", str(os.cpu_count())]
    install_cmd = ["make", "install"]

    cmake_lists_path = os.path.join(package_source_path, "CMakeLists.txt")
    Configure_configure_path = os.path.join(package_source_path, "Configure")
    configure_configure_path = os.path.join(package_source_path, "configure")
    autogen_path = os.path.join(package_source_path, "autogen.sh")
    configure_ac_path = os.path.join(package_source_path, "configure.ac")
    configure_in_path = os.path.join(package_source_path, "configure.in")
    meson_build_path = os.path.join(package_source_path, "meson.build")

    has_cmake = os.path.exists(cmake_lists_path)
    has_Configure_configure = os.path.exists(Configure_configure_path)
    has_configure_configure = os.path.exists(configure_configure_path)
    has_autogen = os.path.exists(autogen_path)
    has_configure_ac = os.path.exists(configure_ac_path)
    has_configure_in = os.path.exists(configure_in_path)
    has_meson = os.path.exists(meson_build_path)

    # Determine the effective config_type and script to use
    effective_config_type = None
    configure_script_to_use = None

    if config_type == "cmake" and has_cmake:
        configure_script_to_use = "cmake"
        effective_config_type = "cmake"
    elif config_type == "autotools":
        if has_autogen:
            pre_configure_cmd = [autogen_path, f"--host={host_triplet}"]
            configure_script_to_use = configure_configure_path
            effective_config_type = "configure"
        elif (has_configure_ac or has_configure_in) and not has_configure_configure:
            pre_configure_cmd = ["autoreconf", "-if"]
            configure_script_to_use = configure_configure_path
            effective_config_type = "configure"
        elif has_configure_configure:
            configure_script_to_use = configure_configure_path
            effective_config_type = "configure"
        elif config_type == "configure" and has_configure_configure:
            configure_script_to_use = configure_configure_path
            effective_config_type = "configure"
        elif config_type == "Configure" and has_Configure_configure:
            configure_script_to_use = Configure_configure_path
            effective_config_type = "Configure"
        elif config_type == "python":
            configure_script_to_use = os.path.join(package_source_path, "configure")
            effective_config_type = "python"
        elif config_type == "pip":
            effective_config_type = "pip"
        else:
            logger.info(f"  - Unknown config_type '{config_type}'. Auto-detecting build system for {package_name}.")
            if has_meson:
                effective_config_type = "meson"
            elif has_autogen:
                pre_configure_cmd = [autogen_path, f"--host={host_triplet}"]
                configure_script_to_use = configure_configure_path
                effective_config_type = "configure"
            elif (has_configure_ac or has_configure_in) and not has_configure_configure:
                pre_configure_cmd = ["autoreconf", "-if"]
                configure_script_to_use = configure_configure_path
                effective_config_type = "configure"
            elif has_cmake:
                effective_config_type = "cmake"
                configure_script_to_use = "cmake"
            elif has_Configure_configure:
                effective_config_type = "Configure"
                configure_script_to_use = Configure_configure_path
            elif has_configure_configure:
                effective_config_type = "configure"
                configure_script_to_use = configure_configure_path
    
    if effective_config_type == "cmake":
        logger.info(f"  - Using CMake for {package_name}.")
        configure_cmd = [
            "cmake",
            f"-DCMAKE_TOOLCHAIN_FILE={ndk_root}/build/cmake/android.toolchain.cmake",
            f"-DANDROID_ABI={arch}",
            f"-DANDROID_NDK={ndk_root}",
            f"-DANDROID_PLATFORM=android-{ndk_api}",
            f"-DCMAKE_ANDROID_ARCH_ABI={arch}",
            f"-DCMAKE_ANDROID_NDK={ndk_root}",
            f"-DCMAKE_BUILD_TYPE=Release",
            f"-DCMAKE_INSTALL_PREFIX={install_dir}",
            "-S",
            package_source_path,
            "-B",
            "build"
        ]
        build_cmd = ["cmake", "--build", "build"]
        install_cmd = ["cmake", "--install", "build"]
    elif effective_config_type == "Configure":
        logger.info(f"  - Using Configure script for {package_name}.")
        if configure_script_to_use:
            configure_cmd = [
                configure_script_to_use,
                f"--build={build_triplet}",
                f"--host={host_triplet}",
                "no-shared",
                f"--prefix={install_dir}",
            ]
    elif effective_config_type == "configure":
        logger.info(f"  - Using configure script for {package_name}.")
        if configure_script_to_use:
            configure_cmd = [
                configure_script_to_use,
                f"--build={build_triplet}",
                f"--host={host_triplet}",
                f"--prefix={install_dir}",
                f"--libdir={install_dir}/lib",
                "--disable-shared",  # Assuming static linking is preferred for Android
                "--enable-static",
                f"CC={cc}",
                f"CXX={cxx}",
                f"CFLAGS={cflags}",
                f"LDFLAGS={ldflags}",
            ]
    elif effective_config_type == "meson":
        logger.info(f"  - Using Meson for {package_name}.")
        build_dir = os.path.join(package_source_path, "build")
        configure_cmd = [
            "meson", "setup", build_dir,
            f"--prefix={install_dir}",
            f"--host={host_triplet}",
            "--buildtype=release",
                        "-Ddefault_library=static", # Prefer static libraries
                        f"CC={cc}",
                        f"CXX={cxx}",
                        f"CFLAGS={cflags}",
                        f"LDFLAGS={ldflags}",        ]
        build_cmd = ["meson", "compile", "-C", build_dir]
        install_cmd = ["meson", "install", "-C", build_dir]
    elif effective_config_type == "python":
        logger.info(f"  - Using Python configure script for {package_name}.")
        configure_cmd = [
            os.path.join(package_source_path, "configure"),
            f"--host={host_triplet}",
            f"--build={build_triplet}",
            "--enable-shared",
            "--disable-ipv6",
            "--without-ensurepip",
            f"--prefix={install_dir}",
            f"--with-build-python={sys.executable}",
            f"CFLAGS={cflags}",
            f"LDFLAGS={ldflags}",
        ]
    elif effective_config_type == "pip":
        logger.info(f"  - Generating pip install command for {package_name}.")
        configure_cmd = []
        build_cmd = []
        install_cmd = [
            os.path.join(install_dir, "bin", "python3"), # Path to target Python interpreter
            "-m", "pip", "install",
            "--no-deps", # Dependencies are handled explicitly by droidbuilder
            package_source_path # Path to the downloaded package source (sdist)
        ]
    elif effective_config_type is None:  # No configure script found or used
        logger.warning(f"  - No build system found for {package_name}. It will not be configured or built.")
        configure_cmd = []
    else:
        raise ValueError(f"Unsupported config_type: {effective_config_type} for package {package_name}.")

    return {
        "pre_configure_command": pre_configure_cmd,
        "clean_command": clean_cmd,
        "configure_command": configure_cmd,
        "build_command": build_cmd,
        "install_command": install_cmd,
    }
