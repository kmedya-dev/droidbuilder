import os
import shutil
from ..cli_logger import logger
from ..utils import ARCH_MAP

class BuildEnvironment:
    def __init__(self, ndk_version, ndk_api, arch, ndk_dir_path, build_path):
        self.ndk_version = ndk_version
        self.ndk_api = ndk_api
        self.arch = arch
        self.ndk_dir_path = ndk_dir_path
        self.build_path = build_path
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
        self.pkg_config_path = None
        self.setup()

    def setup(self):
        """Set up environment variables for cross-compiling."""
        logger.info(f"  - Setting up build environment for {self.arch} (NDK {self.ndk_version}, API {self.ndk_api})...")

        self.ndk_root = self.ndk_dir_path
        if not os.path.exists(self.ndk_root):
            logger.error(f"Error: NDK root directory not found at {self.ndk_root}. Please ensure NDK {self.ndk_version} is installed.")
            raise FileNotFoundError(f"NDK root directory not found at {self.ndk_root}")

        self.toolchain_bin = os.path.join(self.ndk_root, "toolchains", "llvm", "prebuilt", "linux-x86_64", "bin")
        if not os.path.exists(self.toolchain_bin):
            logger.error(f"Error: NDK toolchain binary directory not found at {self.toolchain_bin}. Please check your NDK installation.")
            raise FileNotFoundError(f"NDK toolchain binary directory not found at {self.toolchain_bin}")

        self.sysroot = os.path.join(self.toolchain_bin, f"../sysroot") # sysroot is usually relative to toolchain bin
        if not os.path.exists(self.sysroot):
            logger.error(f"Error: NDK sysroot not found at {self.sysroot}. Please check your NDK installation.")
            raise FileNotFoundError(f"NDK sysroot not found at {self.sysroot}")

        self.compiler_prefix = ARCH_MAP[self.arch][0]
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
        self.pkg_config_path = shutil.which("pkg-config")
        if not self.pkg_config_path:
            logger.warning("  - 'pkg-config' not found in PATH. Some packages may fail to build.")
            self.pkg_config_path = "pkg-config"

        # Initialize cflags, ldflags, asmflags, and cxxflags with base values
        self.cflags = f"--sysroot={self.sysroot} -fPIC -DANDROID"
        self.cxxflags = f"--sysroot={self.sysroot} -fPIC -DANDROID"
        self.asmflags = f"--sysroot={self.sysroot} -fPIC -DANDROID"
        self.ldflags = f"-lm -ldl --sysroot={self.sysroot}"

        # Prepare environment variables for subprocesses
        self.env = os.environ.copy()
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
        self.env["PATH"] = f"{self.toolchain_bin}:{self.env['PATH']}"
        self.env["CFLAGS"] = self.cflags
        self.env["CXXFLAGS"] = self.cxxflags # Added
        self.env["ASMFLAGS"] = self.asmflags
        self.env["LDFLAGS"] = self.ldflags
        self.env["PKG_CONFIG"] = self.pkg_config_path
        self.env["PKG_CONFIG_PATH"] = f"{self.sysroot}/usr/lib/pkgconfig"

        logger.info("  - Build environment set up.")
