import os
import shutil
from ..cli_logger import logger
from ..utils import get_system, get_arch, ARCH_MAP

def _get_host_tag():
    """Returns the host tag for the NDK toolchain."""
    system = get_system()
    arch = get_arch()
    return f"{system}-{arch}"

class BuildEnvironment:
    def __init__(self, ndk_version, ndk_api, arch, ndk_dir_path, build_path, install_path):
        self.ndk_version = ndk_version
        self.ndk_api = ndk_api
        self.arch = arch
        self.ndk_dir_path = ndk_dir_path
        self.build_path = build_path
        self.install_path = install_path
        self.toolchain_bin = None
        self.sysroot = None
        self.cc_path = None
        self.cxx_path = None
        self.ar_path = None
        self.strip_path = None
        self.as_path = None
        self.ld_path = None
        self.ranlib_path = None
        self.readelf_path = None
        self.nm_path = None
        self.cflags = None
        self.cxxflags = None
        self.asmflags = None
        self.ldflags = None
        self.ndk_root = None
        self.compiler_prefix = None
        self.env = None
        self.pkg_config_libdir = None
        self.pkg_config_executable = None
        self.setup()

    def setup(self):
        """Set up environment variables for cross-compiling."""
        logger.info(f"  - Setting up build environment for {self.arch} (NDK {self.ndk_version}, API {self.ndk_api})...")

        self.ndk_root = self.ndk_dir_path
        if not os.path.exists(self.ndk_root):
            logger.error(f"Error: NDK root directory not found at {self.ndk_root}. Please ensure NDK {self.ndk_version} is installed.")
            raise FileNotFoundError(f"NDK root directory not found at {self.ndk_root}")

        host_tag = _get_host_tag()
        self.toolchain_bin = os.path.join(self.ndk_root, "toolchains", "llvm", "prebuilt", host_tag, "bin")
        if not os.path.exists(self.toolchain_bin):
            logger.error(f"Error: NDK toolchain binary directory not found at {self.toolchain_bin}. Please check your NDK installation.")
            raise FileNotFoundError(f"NDK toolchain binary directory not found at {self.toolchain_bin}")

        self.sysroot = os.path.join(self.toolchain_bin, f"../sysroot") # sysroot is usually relative to toolchain bin
        if not os.path.exists(self.sysroot):
            logger.error(f"Error: NDK sysroot not found at {self.sysroot}. Please check your NDK installation.")
            raise FileNotFoundError(f"NDK sysroot not found at {self.sysroot}")

        self.compiler_prefix = ARCH_MAP.get(self.arch, (None,))[0]
        if not self.compiler_prefix:
            logger.error(f"Error: Unsupported architecture for Python build: {self.arch}")
            raise ValueError(f"Unsupported architecture for Python build: {self.arch}")

        self.ar_path = f"{self.toolchain_bin}/llvm-ar"
        self.as_path = f"{self.toolchain_bin}/llvm-as"
        self.cc_path = f"{self.toolchain_bin}/{self.compiler_prefix}{self.ndk_api}-clang"
        self.cxx_path = f"{self.toolchain_bin}/{self.compiler_prefix}{self.ndk_api}-clang++"
        self.ld_path = f"{self.toolchain_bin}/ld"
        self.nm_path = f"{self.toolchain_bin}/llvm-nm"
        self.ranlib_path = f"{self.toolchain_bin}/llvm-ranlib"
        self.readelf_path = f"{self.toolchain_bin}/llvm-readelf"
        self.strip_path = f"{self.toolchain_bin}/llvm-strip"
        self.pkg_config_executable = shutil.which("pkg-config")

        # Initialize cflags, ldflags, asmflags, and cxxflags with base values
        self.cflags = f"-fPIC -DANDROID"
        self.cxxflags = f"-fPIC -DANDROID"
        self.asmflags = f"-fPIC -DANDROID"
        self.ldflags = "-lm -ldl"
        self.pkg_config_libdir = os.path.join(self.install_path, self.arch, "lib", "pkgconfig")

        # Prepare environment variables for subprocesses
        self.env = os.environ.copy()
        
        # Append to existing flags if they exist
        self.env["CFLAGS"] = f"{os.environ.get('CFLAGS', '')} {self.cflags}".strip()
        self.env["CXXFLAGS"] = f"{os.environ.get('CXXFLAGS', '')} {self.cxxflags}".strip()
        self.env["ASMFLAGS"] = f"{os.environ.get('ASMFLAGS', '')} {self.asmflags}".strip()
        self.env["LDFLAGS"] = f"{os.environ.get('LDFLAGS', '')} {self.ldflags}".strip()
        self.env["PKG_CONFIG_PATH"] = f"{os.environ.get('PKG_CONFIG_PATH', '')} {self.pkg_config_libdir}".strip()

        self.env["AR"] = self.ar_path
        self.env["AS"] = self.as_path
        self.env["CC"] = self.cc_path
        self.env["CXX"] = self.cxx_path
        self.env["LD"] = self.ld_path
        self.env["NM"] = self.nm_path
        self.env["RANLIB"] = self.ranlib_path
        self.env["READELF"] = self.readelf_path
        self.env["STRIP"] = self.strip_path
        self.env["SYSROOT"] = self.sysroot
        self.env["PKG_CONFIG"] = self.pkg_config_executable
        self.env["PATH"] = f"{self.toolchain_bin}:{self.env['PATH']}"

        logger.info("  - Build environment set up.")
