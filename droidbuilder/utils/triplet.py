"""
Triplet Detection
-----------------

This module provides functions to determine the system triplet, which is a
string that identifies the system's architecture, vendor, OS, and C library.
The format of the triplet is: arch-vendor-system-libc.
"""


import os
import platform
import tempfile
from ..utils import run_shell_command

IMPLEMENTERS = {
    "0x41": "arm",
    "0x42": "broadcom",
    "0x43": "cavium",
    "0x44": "dec",
    "0x46": "fujitsu",
    "0x49": "infineon",
    "0x4d": "motorola",
    "0x4e": "nvidia",
    "0x50": "apm",
    "0x51": "qualcomm",
    "0x56": "marvell",
    "0x61": "ampere",
    "0x69": "intel",
}


def get_arch():
    """
    Gets the machine architecture from uname -m.

    Returns:
        str: The machine architecture (e.g., "x86_64", "aarch64").
    """
    return platform.machine()


def get_system():
    """
    Gets the operating system name from uname -s.

    Returns:
        str: The operating system name in lowercase (e.g., "linux", "darwin").
    """
    return platform.system().lower()


def get_vendor():
    """
    Gets the CPU vendor.

    This function attempts to read /proc/cpuinfo on Linux systems or uses sysctl
    on macOS to determine the CPU vendor.

    Returns:
        str: The CPU vendor, or "unknown" if it cannot be determined.
    """
    system = get_system()
    if system == "linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "vendor_id" in line or "CPU implementer" in line:
                        parts = line.strip().split(":")
                        if len(parts) > 1:
                            vendor_id = parts[1].strip()
                            return IMPLEMENTERS.get(vendor_id.lower(), vendor_id)
        except FileNotFoundError:
            pass  # /proc/cpuinfo not found
    elif system == "darwin":
        vendor_info = run_shell_command("sysctl -n machdep.cpu.vendor")
        if vendor_info and vendor_info.get("stdout"):
            return vendor_info.get("stdout").strip()
        return "apple"  # A reasonable default for macOS

    return "unknown"


def get_libc():
    """
    Determines the C library (libc) used by the system.

    This method first tries to use `ldd --version` to identify the libc.
    If that fails, it falls back to compiling a small C program with `cc`
    and checking for macros that identify the libc.

    Returns:
        str: The C library (e.g., "gnu", "musl", "android"), or "unknown".
    """
    # Try to use ldd first
    ldd_output = run_shell_command("ldd --version")
    if ldd_output and ldd_output.get("returncode") == 0:
        stdout = ldd_output.get("stdout", "")
        if "glibc" in stdout.lower():
            return "gnu"
        if "musl" in stdout.lower():
            return "musl"

    # Fallback to the compiler-based method
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.c') as temp_c_file:
        temp_c_file_path = temp_c_file.name
        temp_c_file.write("#if defined(__ANDROID__)\n")
        temp_c_file.write("LIBC=android\n")
        temp_c_file.write("#else\n")
        temp_c_file.write("#include <features.h>\n")
        temp_c_file.write("#if defined(__UCLIBC__)\n")
        temp_c_file.write("LIBC=uclibc\n")
        temp_c_file.write("#elif defined(__dietlibc__)\n")
        temp_c_file.write("LIBC=dietlibc\n")
        temp_c_file.write("#elif defined(__GLIBC__)\n")
        temp_c_file.write("LIBC=gnu\n")
        temp_c_file.write("#else\n")
        temp_c_file.write("#include <stdarg.h>\n")
        temp_c_file.write("/* First heuristic to detect musl */\n")
        temp_c_file.write("#ifdef __DEFINED_va_list\n")
        temp_c_file.write("LIBC=musl\n")
        temp_c_file.write("#endif\n")
        temp_c_file.write("#endif\n")
        temp_c_file.write("#endif\n")

    command = f"cc -E {temp_c_file_path} 2>/dev/null | grep LIBC="
    output = run_shell_command(command)
    os.remove(temp_c_file_path)

    if output and output.get("stdout") and "=" in output.get("stdout"):
        return output.get("stdout").split("=")[-1].strip()

    return "unknown"


def get_triplet():
    """
    Constructs and returns the system triplet.
    """
    arch = get_arch()
    vendor = get_vendor()
    system = get_system()
    libc = get_libc()

    return f"{arch}-{vendor}-{system}-{libc}"
