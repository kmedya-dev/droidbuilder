import os
import sys

from .system_info import get_triplet, ARCH_MAP
from ..utils import run_shell_command
from ..cli_logger import logger

def _autodetect_config_type(package_source_path: str, package_name: str) -> str:
    if os.path.exists(os.path.join(package_source_path, "meson.build")):
        logger.info("  - Found 'meson.build', assuming meson.")
        return "meson"
    elif os.path.exists(os.path.join(package_source_path, "CMakeLists.txt")):
        logger.info("  - Found 'CMakeLists.txt', assuming cmake.")
        return "cmake"
    elif os.path.exists(os.path.join(package_source_path, "Configure")):
        logger.info("  - Found 'Configure', assuming Configure.")
        return "Configure"
    elif any(os.path.exists(os.path.join(package_source_path, fname)) for fname in ("configure", "configure.ac", "configure.in", "autogen.sh")):
        logger.info("  - Found autotools-related files, assuming autotools.")
        return "autotools"

    logger.warning(f"  - Could not auto-detect build system for {package_name}.")
    return ""


def _get_triplet(package_source_path: str) -> str:
    """
    Determines the build architecture triple by running config.guess or uname.
    """
    triplet = ""
    config_guess_path = os.path.join(package_source_path, "config.guess")
    if not os.path.exists(config_guess_path):
        config_guess_path = os.path.join(package_source_path, "build-aux", "config.guess")

    if os.path.exists(config_guess_path):
        logger.info("  - Trying to determine build host from config.guess")
        try:
            os.chmod(config_guess_path, 0o755)
        except OSError as e:
            logger.error(f"Error setting executable permission for {config_guess_path}: {e}")
        result = run_shell_command([config_guess_path], description=f"Determining build host using {config_guess_path}", cwd=package_source_path)
        if result["returncode"] == 0:
            triplet = result["stdout"].strip()
            logger.info(f"  - Detected build host: {triplet}")
            return triplet
        else:
            logger.warning(f"  - config.guess failed with error: {result['stderr'].strip()}")

    logger.info("  - Could not determine build host from config.guess, falling back to triplet detection.")
    try:
        triplet = get_triplet()

        logger.info(f"  - Detected build host: {triplet}")
        return triplet
    except Exception as e:
        logger.error(f"An unexpected error occurred while determining build host using triplet detection: {e}")
        logger.exception(*sys.exc_info())
    return ""

def _generate_autotools_commands(
    package_name: str,
    package_source_path: str,
    arch: str,
    ndk_api: str,
    install_dir: str,
    cflags: str,
    cxxflags: str,
    asmflags: str,
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
    pkgconfig: str,
    pkg_config: str,
    extra_configure_args: list[str] = [],
) -> tuple:
    logger.info("  - Generating autotools build commands.")

    triplet = _get_triplet(package_source_path)

    pre_configure_cmd = []
    configure_script_path = os.path.join(package_source_path, "configure")

    if not os.path.exists(configure_script_path):
        if os.path.exists(os.path.join(package_source_path, "autogen.sh")):
            logger.info("  - 'configure' script not found, running 'autogen.sh'.")
            pre_configure_cmd = ["autogen.sh"]
        elif any(os.path.exists(os.path.join(package_source_path, fname)) for fname in ("configure.ac", "configure.in")):
            logger.info("  - 'configure' script not found, running 'autoreconf -fi'.")
            pre_configure_cmd = ["autoreconf", "-fi"]
        else:
            logger.warning("  - No 'configure' script, 'autogen.sh', 'configure.ac', or 'configure.in' found.")

    configure_cmd = [
        configure_script_path,
        f"--prefix={install_dir}",
        f"--host={ARCH_MAP[arch][0]}",
        f"--build={triplet}",
        "--enable-shared",
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
        f"PKG_CONFIG={pkg_config}",
    ]

    configure_cmd.extend(extra_configure_args)
    build_cmd = ["make", "-j", str(os.cpu_count())]
    install_cmd = ["make", "install"]
    clean_cmd = ["make", "clean"]
    return clean_cmd, configure_cmd, build_cmd, install_cmd


def _generate_cmake_commands(
    package_name: str,
    package_source_path: str,
    arch: str,
    ndk_api: str,
    install_dir: str,
    cflags: str,
    cxxflags: str,
    asmflags: str,
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
    pkgconfig: str,
    pkg_config: str,
    extra_configure_args: list[str] = [],
) -> tuple:
    build_dir = os.path.join(package_source_path, "build")

    configure_cmd = [
        "cmake",
        "-S", package_source_path,
        "-B", build_dir,
        f"-DCMAKE_INSTALL_PREFIX={install_dir}",
        f"-DCMAKE_PREFIX_PATH={install_dir}",
        f"-DCMAKE_TOOLCHAIN_FILE={ndk_root}/build/cmake/android.toolchain.cmake",
        f"-DANDROID_PLATFORM=android-{ndk_api}",
        f"-DANDROID_ABI={arch}",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_FIND_DEBUG_MODE=ON",
        f"-DCMAKE_C_FLAGS={cflags}",
        f"-DCMAKE_CXX_FLAGS={cxxflags}",
        f"-DCMAKE_ASM_FLAGS={asmflags}",
        f"-DCMAKE_SHARED_LINKER_FLAGS={ldflags}",
        f"-DCMAKE_MODULE_LINKER_FLAGS={ldflags}",
        f"-DCMAKE_EXE_LINKER_FLAGS={ldflags}",
        "-DBUILD_SHARED_LIBS=ON",
        "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        f"-DCMAKE_AR={ar}",
        f"-DCMAKE_ASM_COMPILER={as_}",
        f"-DCMAKE_C_COMPILER={cc}",
        f"-DCMAKE_CXX_COMPILER={cxx}",
        f"-DCMAKE_LINKER={ld}",
        f"-DCMAKE_RANLIB={ranlib}",
        f"-DCMAKE_NM={nm}",
        f"-DCMAKE_STRIP={strip}",
        f"-DPKG_CONFIG_EXECUTABLE={pkg_config}",
    ]

    configure_cmd.extend(extra_configure_args)
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
    cxxflags: str,
    asmflags: str,
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
    pkgconfig: str,
    pkg_config: str,
    extra_configure_args: list[str] = [],
) -> tuple:
    logger.info(f"  - Generating Meson build commands for {package_name}.")

    build_dir = os.path.join(package_source_path, "build")

    meson_cpu_family = ARCH_MAP[arch][1]
    meson_cpu = ARCH_MAP[arch][2]

    cross_file_path = os.path.join(package_source_path, f"meson-cross-{arch}.ini")

    with open(cross_file_path, "w") as f:
        f.write("[binaries]\n")
        f.write(f"c = '{cc}'\n")
        f.write(f"cpp = '{cxx}'\n")
        f.write(f"ar = '{ar}'\n")
        f.write(f"as = '{as_}'\n")
        f.write(f"strip = '{strip}'\n")
        f.write(f"pkg-config = '{pkg_config}'\n")
        f.write("\n")
        f.write("[host_machine]\n")
        f.write("system = 'android'\n")
        f.write(f"cpu_family = '{meson_cpu_family}'\n")
        f.write(f"cpu = '{meson_cpu}'\n")
        f.write("endian = 'little'\n")
        f.write("\n")
        f.write("[properties]\n")
        f.write(f"sys_root = '{sysroot}'\n")

    configure_cmd = [
        "meson", "setup", build_dir,
        f"-Dprefix={install_dir}",
        f"--cross-file={cross_file_path}",
        "--buildtype=release",
        "-Ddefault_library=shared",
        "-Db_staticpic=false",
    ]

    configure_cmd.extend(extra_configure_args)
    build_cmd = ["meson", "compile", "-C", build_dir]
    install_cmd = ["meson", "install", "-C", build_dir]
    clean_cmd = ["rm", "-rf", build_dir, cross_file_path]
    return clean_cmd, configure_cmd, build_cmd, install_cmd

def _generate_Configure_commands(
    package_name: str,
    package_source_path: str,
    arch: str,
    ndk_api: str,
    install_dir: str,
    cflags: str,
    cxxflags: str,
    asmflags: str,
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
    pkgconfig: str,
    pkg_config: str,
    extra_configure_args: list[str] = [],
) -> tuple:
    logger.info(f"  - Generating Configure build commands for {package_name}.")

    # Configure command
    configure_cmd = [
        os.path.join(package_source_path, "Configure"),
        ARCH_MAP[arch][3],
        f"--prefix={install_dir}",
        f"PKG_CONFIG={pkg_config}",
        "shared",
    ]

    configure_cmd.extend(extra_configure_args)

    # Build command
    build_cmd = ["make", "-j", str(os.cpu_count())]

    # Install command
    install_cmd = ["make", "install"]

    # Clean command
    clean_cmd = ["make", "clean"]

    return clean_cmd, configure_cmd, build_cmd, install_cmd

def resolve_config_type(
    package_name: str,
    package_config: dict,
    package_source_path: str,
    arch: str,
    ndk_api: str,
    install_dir: str,
    cflags: str = "",
    cxxflags: str = "",
    asmflags: str = "",
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
    pkgconfig: str = "",
    pkg_config: str = "",
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
        dict: A dictionary containing 'clean_command', 'configure_command', 'build_command', and 'install_command' lists.
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
        "Configure": _generate_Configure_commands,
    }

    if config_type in command_generators:
        clean_cmd, configure_cmd, build_cmd, install_cmd = command_generators[config_type](
            package_name,
            package_source_path,
            arch,
            ndk_api,
            install_dir,
            cflags,
            cxxflags,
            asmflags,
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
            pkgconfig,
            pkg_config,
            extra_configure_args,
        )
    elif config_type:
        logger.error(f"Unsupported config_type: {config_type} for package {package_name}.")
    else:
        logger.warning(f"  - No build system found for {package_name}. It will not be configured or built.")

    return {
        "config_type": config_type,
        "clean_command": clean_cmd,
        "configure_command": configure_cmd,
        "build_command": build_cmd,
        "install_command": install_cmd,
    }
