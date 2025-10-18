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

def _autodetect_config_type(package_source_path: str, package_name: str) -> str:
    if os.path.exists(os.path.join(package_source_path, "configure")):
        logger.info("  - Found 'configure' script, assuming autotools.")
        return "autotools"
    elif os.path.exists(os.path.join(package_source_path, "meson.build")):
        logger.info("  - Found 'meson.build', assuming meson.")
        return "meson"
    elif os.path.exists(os.path.join(package_source_path, "CMakeLists.txt")):
        logger.info("  - Found 'CMakeLists.txt', assuming cmake.")
        return "cmake"
    else:
        logger.warning(f"  - Could not auto-detect build system for {package_name}.")
        return ""

def _generate_meson_cross_file(
    package_source_path: str,
    arch: str,
    cc: str,
    cxx: str,
    ar: str,
    strip: str,
    sysroot: str,
) -> str:
    meson_cpu_family = ARCH_MAP[arch][1]
    meson_cpu = ARCH_MAP[arch][2]
    cross_file_path = os.path.join(package_source_path, f"meson-cross-{arch}.ini")

    with open(cross_file_path, "w") as f:
        f.write("[binaries]\n")
        f.write(f"c = '{cc}'\n")
        f.write(f"cpp = '{cxx}'\n")
        f.write(f"ar = '{ar}'\n")
        f.write(f"strip = '{strip}'\n")
        f.write("\n")
        f.write("[host_machine]\n")
        f.write("system = 'android'\n")
        f.write(f"cpu_family = '{meson_cpu_family}'\n")
        f.write(f"cpu = '{meson_cpu}'\n")
        f.write("endian = 'little'\n")
        f.write("\n")
        f.write("[properties]\n")
        f.write(f"sys_root = '{sysroot}'\n")
    return cross_file_path

def _generate_autotools_commands(
    package_name: str,
    package_source_path: str,
    arch: str,
    ndk_api: str,
    install_dir: str,
    cflags: str,
    ldflags: str,
    cc: str,
    cxx: str,
    ar: str,
    as_: str,
    ld: str,
    ranlib: str,
    readelf: str,
    nm: str,
    strip: str,
    ndk_root: str,
    sysroot: str,
    extra_configure_args: list[str] = [],
) -> tuple:
    logger.info("  - Generating autotools build commands.")
    configure_cmd = [
        os.path.join(package_source_path, "configure"),
        f"--prefix={install_dir}",
        f"--host={ARCH_MAP[arch][0]}",
        f"AS={as_}",
        f"CC={cc}",
        f"CXX={cxx}",
        f"LD={ld}",
        f"AR={ar}",
        f"RANLIB={ranlib}",
        f"READELF={readelf}",
        f"NM={nm}",
        f"STRIP={strip}",
        f"CFLAGS={cflags}",
        f"LDFLAGS={ldflags}",
    ] + extra_configure_args
    build_cmd = ["make", "-j", str(os.cpu_count())]
    install_cmd = ["make", "install"]
    clean_cmd = ["make", "distclean"]
    return clean_cmd, configure_cmd, build_cmd, install_cmd

def _generate_cmake_commands(
    package_name: str,
    package_source_path: str,
    arch: str,
    ndk_api: str,
    install_dir: str,
    cflags: str,
    ldflags: str,
    cc: str,
    cxx: str,
    ar: str,
    as_: str,
    ld: str,
    ranlib: str,
    readelf: str,
    nm: str,
    strip: str,
    ndk_root: str,
    sysroot: str,
) -> tuple:
    logger.info(f"  - Generating CMake build commands for {package_name}.")

    build_dir = os.path.join(package_source_path, "build")

    configure_cmd = [
        "cmake",
        "-S", package_source_path,
        "-B", build_dir,
        f"-DCMAKE_INSTALL_PREFIX={install_dir}",
        f"-DCMAKE_TOOLCHAIN_FILE={ndk_root}/build/cmake/android.toolchain.cmake",
        f"-DANDROID_ABI={arch}",
        f"-DANDROID_NATIVE_API_LEVEL={ndk_api}",
    ]

    build_cmd = ["cmake", "--build", build_dir, "--", "-j", str(os.cpu_count())]
    install_cmd = ["cmake", "--install", build_dir]
    clean_cmd = ["rm", "-rf", build_dir]
    return clean_cmd, configure_cmd, build_cmd, install_cmd

def _generate_meson_commands(
    package_name: str,
    package_source_path: str,
    arch: str,
    ndk_api: str,
    install_dir: str,
    cflags: str,
    ldflags: str,
    cc: str,
    cxx: str,
    ar: str,
    as_: str,
    ld: str,
    ranlib: str,
    readelf: str,
    nm: str,
    strip: str,
    ndk_root: str,
    sysroot: str,
) -> tuple:
    logger.info(f"  - Generating Meson build commands for {package_name}.")

    build_dir = os.path.join(package_source_path, "build")
    cross_file_path = _generate_meson_cross_file(
        package_source_path, arch, cc, cxx, ar, strip, sysroot
    )

    configure_cmd = [
        "meson", "setup", build_dir,
        f"--prefix={install_dir}",
        f"--cross-file={cross_file_path}",
        "--buildtype=release",
    ]

    build_cmd = ["meson", "compile", "-C", build_dir]
    install_cmd = ["meson", "install", "-C", build_dir]
    clean_cmd = ["rm", "-rf", build_dir, cross_file_path]
    return clean_cmd, configure_cmd, build_cmd, install_cmd

def _generate_pip_commands(
    package_name: str,
    package_source_path: str,
    arch: str,
    ndk_api: str,
    install_dir: str,
    cflags: str,
    ldflags: str,
    cc: str,
    cxx: str,
    ar: str,
    as_: str,
    ld: str,
    ranlib: str,
    readelf: str,
    nm: str,
    strip: str,
    ndk_root: str,
    sysroot: str,
) -> tuple:
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
    clean_cmd = []
    return clean_cmd, configure_cmd, build_cmd, install_cmd


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
    as_: str = "",
    ld: str = "",
    ranlib: str = "",
    readelf: str = "",
    nm: str = "",
    strip: str = "",
    ndk_root: str = "",
    sysroot: str = "",
    extra_configure_args: list[str] = [],
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

    Returns:
        dict: A dictionary containing 'pre_configure_command', 'clean_command', 'configure_command', 'build_command', and 'install_command' lists.
              Returns empty lists if no suitable configuration is found or an unsupported type is given.

    Raises:
        ValueError: If an unsupported config_type is provided.
    """
    package_config = package_config or {}
    config_type = package_config.get("config_type", "").lower()

    if config_type:
        logger.info(f"Resolving configuration for {package_name} with config_type: {config_type}")
    else:
        config_type = _autodetect_config_type(package_source_path, package_name)
        logger.info(f"Resolving configuration for {package_name} with auto-detection. Detected: {config_type if config_type else 'None'}")

    clean_cmd = []
    configure_cmd = []
    build_cmd = []
    install_cmd = []

    command_generators = {
        "autotools": _generate_autotools_commands,
        "cmake": _generate_cmake_commands,
        "meson": _generate_meson_commands,
        "pip": _generate_pip_commands,
    }

    if config_type in command_generators:
        clean_cmd, configure_cmd, build_cmd, install_cmd = command_generators[config_type](
            package_name,
            package_source_path,
            arch,
            ndk_api,
            install_dir,
            cflags,
            ldflags,
            cc,
            cxx,
            ar,
            as_,
            ld,
            ranlib,
            readelf,
            nm,
            strip,
            ndk_root,
            sysroot,
            extra_configure_args,
        )
    elif config_type:
        logger.error(f"Unsupported config_type: {config_type} for package {package_name}.")
    else:
        logger.warning(f"  - No build system found for {package_name}. It will not be configured or built.")

    return {
        "clean_command": clean_cmd,
        "configure_command": configure_cmd,
        "build_command": build_cmd,
        "install_command": install_cmd,
    }
