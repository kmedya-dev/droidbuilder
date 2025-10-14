import os
import sys

from ..cli_logger import logger

def resolve_config_type(package_config: dict, package_name: str, package_source_path: str, arch: str, ndk_api: str, install_dir: str, build_triplet: str, host_triplet: str, cflags: str = "", ldflags: str = "", cc: str = "", cxx: str = "", ar: str = "", ld: str = "", ranlib: str = "", strip: str = "", readelf: str = "") -> dict:
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
        dict: A dictionary containing 'configure_command', 'build_command', and 'install_command' lists.
              Returns empty lists if no suitable configuration is found or an unsupported type is given.

    Raises:
        ValueError: If an unsupported config_type is provided.
    """
    config_type = package_config.get("config_type", "standard").lower()
    logger.info(f"Resolving configuration for {package_name} with config_type: {config_type}")

    configure_cmd = []
    build_cmd = ["make", "-j", str(os.cpu_count())]
    install_cmd = ["make", "install"]
    autogen_cmd = []
    autoreconf_cmd = []

    cmake_lists_path = os.path.join(package_source_path, "CMakeLists.txt")
    specialized_configure_path = os.path.join(package_source_path, "Configure")
    standard_configure_path = os.path.join(package_source_path, "configure")
    autogen_script_path = os.path.join(package_source_path, "autogen.sh")
    configure_ac_path = os.path.join(package_source_path, "configure.ac")
    configure_in_path = os.path.join(package_source_path, "configure.in")

    has_cmake = os.path.exists(cmake_lists_path)
    has_specialized_configure = os.path.exists(specialized_configure_path)
    has_standard_configure = os.path.exists(standard_configure_path)
    has_autogen_script = os.path.exists(autogen_script_path)
    has_configure_ac = os.path.exists(configure_ac_path)
    has_configure_in = os.path.exists(configure_in_path)

    if has_autogen_script:
        autogen_cmd = [autogen_script_path]

    # Always run autoreconf if configure.ac or configure.in exists
    if has_configure_ac or has_configure_in:
        logger.info(f"  - 'configure.ac' or 'configure.in' exists for {package_name}. Adding autoreconf command.")
        autoreconf_cmd = ["autoreconf", "-fi"]




    # Determine the effective config_type and script to use
    effective_config_type = None
    configure_script_to_use = None

    if config_type == "cmake" and has_cmake:
        effective_config_type = "cmake"
        configure_script_to_use = "cmake"
    elif config_type in ["specialized", "C"] and has_specialized_configure:
        effective_config_type = "specialized"
        configure_script_to_use = specialized_configure_path
    elif config_type in ["standard", "c"] and has_standard_configure:
        effective_config_type = "standard"
        configure_script_to_use = standard_configure_path
    elif has_cmake:  # Fallback: if CMakeLists.txt exists, use it
        effective_config_type = "cmake"
        configure_script_to_use = "cmake"
        logger.info(f"  - No explicit config_type found, but CMakeLists.txt exists for {package_name}. Using CMake.")
    elif has_specialized_configure:  # Fallback: if specialized exists, use it
        effective_config_type = "specialized"
        configure_script_to_use = specialized_configure_path
        logger.info(f"  - No explicit config_type or standard 'configure' found, but specialized 'Configure' exists for {package_name}. Using specialized.")
    elif has_standard_configure:  # Fallback: if standard exists, use it
        effective_config_type = "standard"
        configure_script_to_use = standard_configure_path
        logger.info(f"  - No explicit config_type or specialized 'Configure' found, but standard 'configure' exists for {package_name}. Using standard.")
    else:
        logger.warning(f"  - No supported build system found for {package_name}. Proceeding without configure step.")

    if effective_config_type == "cmake":
        logger.info(f"  - Using CMake for {package_name}.")
        configure_cmd = [
            "cmake",
            f"-DCMAKE_TOOLCHAIN_FILE={os.getenv('NDK_HOME')}/build/cmake/android.toolchain.cmake",
            f"-DANDROID_ABI={arch}",
            f"-DANDROID_NDK={os.getenv('NDK_HOME')}",
            f"-DANDROID_PLATFORM=android-{ndk_api}",
            f"-DCMAKE_ANDROID_ARCH_ABI={arch}",
            f"-DCMAKE_ANDROID_NDK={os.getenv('NDK_HOME')}",
            f"-DCMAKE_BUILD_TYPE=Release",
            f"-DCMAKE_INSTALL_PREFIX={install_dir}",
            "-S",
            package_source_path,
            "-B",
            "build"
        ]
        build_cmd = ["cmake", "--build", "build"]
        install_cmd = ["cmake", "--install", "build"]
    elif effective_config_type == "specialized":
        logger.info(f"  - Using specialized 'Configure' script for {package_name}.")
        # Map droidbuilder arch to specialized target
        specialized_arch_target = ""
        if arch == "arm64-v8a":
            specialized_arch_target = "android-arm64"
        elif arch == "armeabi-v7a":
            specialized_arch_target = "android-arm"
        elif arch == "x86":
            specialized_arch_target = "android-x86"
        elif arch == "x86_64":
            specialized_arch_target = "android-x86_64"
        else:
            logger.warning(f"  - Unknown architecture for specialized build: {arch}. Proceeding without specialized arch target.")
            # Proceed without specialized arch target if arch not recognized for specialized

        if configure_script_to_use:
            configure_cmd = [
                configure_script_to_use,
                specialized_arch_target,
                "no-shared",
                f"--prefix={install_dir}",
            ]
    elif effective_config_type == "standard":
        logger.info(f"  - Using standard configure script for {package_name}.")
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
    elif config_type == "python":
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
            f"CFLAGS={cflags} -isysroot {os.path.join(os.getenv('NDK_HOME'), 'sysroot')}",
            f"LDFLAGS={ldflags}",
        ]
    elif config_type == "pip":
        logger.info(f"  - Generating pip install command for {package_name}.")
        configure_cmd = []
        build_cmd = []
        install_cmd = [
            os.path.join(install_dir, "bin", "python3"), # Path to target Python interpreter
            "-m", "pip", "install",
            "--no-deps", # Dependencies are handled explicitly by droidbuilder
            "--target", install_dir, # Install into the target Python environment
            package_source_path # Path to the downloaded package source (sdist)
        ]
    elif effective_config_type is None:  # No configure script found or used
        configure_cmd = []
    else:
        raise ValueError(f"Unsupported config_type: {config_type} for package {package_name}. Only 'standard' (c) and 'specialized' (C) are supported.")

    return {
        "configure_command": configure_cmd,
        "build_command": build_cmd,
        "install_command": install_cmd,
        "autogen_command": autogen_cmd,
        "autoreconf_command": autoreconf_cmd,
    }