import click
import os
import requests
import zipfile
import tarfile
import subprocess
import shutil
import sys
import time
from .cli_logger import logger
from . import config

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")


# -------------------- Helpers: safe paths & extraction --------------------

def _safe_join(base, *paths):
    base = os.path.abspath(base)
    final = os.path.abspath(os.path.join(base, *paths))
    if not final.startswith(base + os.sep) and final != base:
        raise IOError(f"Unsafe path detected: {final}")
    return final

def _safe_extract_zip(zip_ref: zipfile.ZipFile, dest_dir: str, log_each=True):
    for member in zip_ref.infolist():
        # protect against zip slip
        target_path = _safe_join(dest_dir, member.filename)
        # logging like unzip
        if member.is_dir():
            if log_each:
                logger.step_info(f"creating: {member.filename}", indent=3)
            os.makedirs(target_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            if log_each:
                if os.path.exists(target_path):
                    logger.step_info(f" replace: {member.filename}", indent=2)
                else:
                    logger.step_info(f"inflating: {member.filename}", indent=2)
            with zip_ref.open(member, 'r') as src, open(target_path, 'wb') as out:
                shutil.copyfileobj(src, out)

def _safe_extract_tar(tar_ref: tarfile.TarFile, dest_dir: str, log_each=True):
    for member in tar_ref.getmembers():
        # deny absolute or parent traversal
        member_path = _safe_join(dest_dir, member.name)
        if member.isdir():
            if log_each:
                logger.step_info(f"creating: {member.name}", indent=3)
            os.makedirs(member_path, exist_ok=True)
            continue
        # ensure parent exists
        os.makedirs(os.path.dirname(member_path), exist_ok=True)
        if log_each:
            if os.path.exists(member_path):
                logger.step_info(f" replace: {member.name}", indent=2)
            else:
                logger.step_info(f"extracting: {member.name}", indent=2)
        with tar_ref.extractfile(member) as src, open(member_path, "wb") as out:
            if src is None:
                # could be special file; skip silently
                continue
            shutil.copyfileobj(src, out)


# -------------------- Download & Extract --------------------

def _download_and_extract(url, dest_dir, filename=None, timeout=60):
    os.makedirs(dest_dir, exist_ok=True)
    if filename is None:
        filename = url.split('/')[-1]
    filepath = os.path.join(dest_dir, filename)

    temp_filepath = filepath + ".tmp"

    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))

            with open(temp_filepath, 'wb') as f:
                chunks = r.iter_content(chunk_size=1024 * 256)  # 256KB chunks
                iterable = logger.progress(
                    chunks,
                    description=f"Downloading {filename}",
                    total=total_size,
                    unit="b"
                )
                for chunk in iterable:
                    if chunk:  # keep-alive chunks may be empty
                        f.write(chunk)

        # Atomic rename
        os.replace(temp_filepath, filepath)

        logger.step_info(f"Archive:  {filename}")

        if filename.endswith(".zip"):
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                _safe_extract_zip(zip_ref, dest_dir)
        elif filename.endswith((".tar.gz", ".tgz")):
            # filter mode enforces gz; tarfile.open auto-detects too
            with tarfile.open(filepath, 'r:*') as tar_ref:
                _safe_extract_tar(tar_ref, dest_dir)
        else:
            logger.warning(f"Unsupported archive type for {filename}. Skipping extraction.")
            return

        # Remove archive after successful extraction
        try:
            os.remove(filepath)
        except OSError:
            pass

        logger.success(f"Successfully extracted to {dest_dir}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading the file: {e}")
        # cleanup temp
        with contextlib.suppress(Exception):
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
    except (zipfile.BadZipFile, tarfile.TarError, IOError) as e:
        logger.error(f"Error during extraction: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.exception(*sys.exc_info())


# -------------------- JDK (Temurin) --------------------

def _get_latest_temurin_jdk_url(version):
    api_url = f"https://api.github.com/repos/adoptium/temurin{version}-binaries/releases/latest"
    try:
        resp = requests.get(api_url, timeout=30)
        resp.raise_for_status()
        release_info = resp.json()

        # Find the asset for linux x64 tar.gz
        for asset in release_info.get('assets', []):
            name = asset.get('name', '')
            if ("OpenJDK" in name and
                f"jdk_x64_linux_hotspot" in name and
                name.endswith(".tar.gz")):
                return asset.get('browser_download_url')

        logger.error(f"Error: Could not find a suitable JDK asset for Temurin {version} on Linux x64.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching latest Temurin JDK release for version {version}: {e}")
        return None
    except (KeyError, ValueError):
        logger.error(f"Error parsing GitHub API response for Temurin {version}.")
        return None


# -------------------- Android SDK --------------------

def install_sdk(version, cmdline_tools_version):
    logger.info(f"  - Installing Android SDK version {version}...")
    sdk_url = f"https://dl.google.com/android/repository/commandlinetools-linux-{cmdline_tools_version}_latest.zip"
    sdk_install_dir = os.path.join(INSTALL_DIR, "android-sdk")

    _download_and_extract(sdk_url, sdk_install_dir)

    # Resolve actual cmdline-tools root (cases: nested cmdline-tools/)
    # Expected: <sdk_install_dir>/cmdline-tools/<bin>
    # Some zips: cmdline-tools/cmdline-tools/<bin>
    root = sdk_install_dir
    ct = os.path.join(root, "cmdline-tools")

    actual_tools_root = None
    if os.path.exists(os.path.join(ct, "bin")):
        actual_tools_root = ct
    elif os.path.exists(os.path.join(ct, "cmdline-tools", "bin")):
        actual_tools_root = os.path.join(ct, "cmdline-tools")
    else:
        # fallback: try to find a single folder containing bin/
        for item in os.listdir(root):
            candidate = os.path.join(root, item)
            if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, "bin")):
                actual_tools_root = candidate
                break

    if actual_tools_root is None:
        logger.error("Error: Could not locate extracted command-line tools (bin not found).")
        return

    # Create final "latest" dir
    final_ct_latest = os.path.join(ct, "latest")
    os.makedirs(final_ct_latest, exist_ok=True)

    # Move contents of actual_tools_root -> latest (avoid moving 'latest' into itself)
    for item in os.listdir(actual_tools_root):
        src = os.path.join(actual_tools_root, item)
        dst = os.path.join(final_ct_latest, item)
        if os.path.abspath(src) == os.path.abspath(final_ct_latest):
            continue
        if os.path.exists(dst):
            # merge/replace
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
                shutil.rmtree(src, ignore_errors=True)
            else:
                os.replace(src, dst)
        else:
            shutil.move(src, final_ct_latest)

    # If actual_tools_root was not ct, clean it up to avoid nesting
    if os.path.abspath(actual_tools_root) != os.path.abspath(ct):
        with contextlib.suppress(Exception):
            shutil.rmtree(actual_tools_root, ignore_errors=True)

    sdk_manager = os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin", "sdkmanager")
    if not os.path.exists(sdk_manager):
        logger.error(f"Error: sdkmanager not found at {sdk_manager}. SDK installation failed.")
        return

    os.environ["ANDROID_HOME"] = sdk_install_dir
    os.environ["PATH"] += os.pathsep + os.path.join(sdk_install_dir, "platform-tools")
    os.environ["PATH"] += os.pathsep + os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin")

    logger.info(f"  - Installing Android SDK Platform {version} and build-tools...")
    try:
        subprocess.run(
            [sdk_manager, f"platforms;android-{version}", f"build-tools;{version}.0.0", "platform-tools"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("  - Android SDK components installed.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing SDK components: {e.stderr}")
        logger.info("Please ensure the SDK version is valid and try again.")


# -------------------- Android NDK --------------------

def install_ndk(version, sdk_install_dir):
    logger.info(f"  - Installing Android NDK version {version}...")

    sdk_manager = os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin", "sdkmanager")
    if not os.path.exists(sdk_manager):
        logger.error(f"Error: sdkmanager not found at {sdk_manager}. Cannot install NDK.")
        return

    try:
        subprocess.run([sdk_manager, f"ndk;{version}"], check=True, capture_output=True, text=True)
        logger.info("  - Android NDK components installed.")
        # Set ANDROID_NDK_HOME and PATH
        ndk_path = os.path.join(sdk_install_dir, "ndk", version)  # NDK is installed under ndk/<version>
        os.environ["ANDROID_NDK_HOME"] = ndk_path
        os.environ["PATH"] += os.pathsep + ndk_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing NDK components: {e.stderr}")
        logger.info("Please ensure the NDK version is valid and try again.")


# -------------------- JDK --------------------

def install_jdk(version):
    logger.info(f"  - Installing JDK version {version}...")

    jdk_url = _get_latest_temurin_jdk_url(version)
    if not jdk_url:
        logger.error(f"  - Failed to get download URL for JDK version {version}. Aborting installation.")
        return

    jdk_install_dir = os.path.join(INSTALL_DIR, f"jdk-{version}")
    _download_and_extract(jdk_url, jdk_install_dir)

    # Find extracted jdk dir like jdk-XX.X.X+X
    extracted_jdk_dir = None
    for item in os.listdir(jdk_install_dir):
        if item.startswith("jdk-") and os.path.isdir(os.path.join(jdk_install_dir, item)):
            extracted_jdk_dir = os.path.join(jdk_install_dir, item)
            break

    if extracted_jdk_dir:
        os.environ["JAVA_HOME"] = extracted_jdk_dir
        os.environ["PATH"] += os.pathsep + os.path.join(extracted_jdk_dir, "bin")
        logger.info(f"  - JDK installed to {extracted_jdk_dir}")
    else:
        logger.warning("Warning: Could not find extracted JDK directory.")


# -------------------- Licenses --------------------

def _accept_sdk_licenses(sdk_install_dir):
    logger.info("  - Accepting Android SDK licenses...")
    sdk_manager = os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin", "sdkmanager")
    if not os.path.exists(sdk_manager):
        logger.error(f"Error: sdkmanager not found at {sdk_manager}. Cannot accept licenses.")
        return

    try:
        p = subprocess.Popen([sdk_manager, "--licenses"],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True)
        stdout, stderr = p.communicate(input='y\n' * 50)  # generous yes
        if p.returncode == 0:
            logger.info("  - Android SDK licenses accepted.")
        else:
            logger.error(f"Error accepting licenses: {stderr}")
    except Exception as e:
        logger.error(f"An error occurred during license acceptance: {e}")
        logger.exception(*sys.exc_info())


# -------------------- Orchestrators --------------------

def setup_tools(conf, ci_mode=False):
    logger.info("Setting up development tools...")
    sdk_version = conf.get("android", {}).get("sdk_version")
    ndk_version = conf.get("android", {}).get("ndk_version")
    jdk_version = conf.get("java", {}).get("jdk_version")
    cmdline_tools_version = conf.get("android", {}).get("cmdline_tools_version")
    sdk_install_dir = os.path.join(INSTALL_DIR, "android-sdk")

    if sdk_version and cmdline_tools_version:
        install_sdk(sdk_version, cmdline_tools_version)
    elif sdk_version and not cmdline_tools_version:
        logger.warning("cmdline_tools_version missing in config; cannot install SDK command-line tools.")

    if ndk_version:
        install_ndk(ndk_version, sdk_install_dir)
    if jdk_version:
        install_jdk(jdk_version)

    if ci_mode:
        _accept_sdk_licenses(sdk_install_dir)


def list_installed_tools():
    """Scan the installation directory and list installed tools and versions."""
    installed = {
        "android_sdk": [],
        "android_ndk": [],
        "java_jdk": [],
    }

    if not os.path.exists(INSTALL_DIR):
        return installed

    # Android SDK
    sdk_dir = os.path.join(INSTALL_DIR, "android-sdk", "platforms")
    if os.path.exists(sdk_dir):
        installed["android_sdk"] = [
            p.replace("android-", "") for p in os.listdir(sdk_dir)
            if p.startswith("android-")
        ]

    # Android NDK
    ndk_dir = os.path.join(INSTALL_DIR, "android-sdk", "ndk")
    if os.path.exists(ndk_dir):
        installed["android_ndk"] = [d for d in os.listdir(ndk_dir) if os.path.isdir(os.path.join(ndk_dir, d))]

    # Java JDK
    for item in os.listdir(INSTALL_DIR):
        if item.startswith("jdk-") and os.path.isdir(os.path.join(INSTALL_DIR, item)):
            installed["java_jdk"].append(item.replace("jdk-", ""))

    return installed


def list_installed_droids():
    """Scan the installation directory and list installed droids."""
    droids_dir = os.path.join(INSTALL_DIR, "droids")
    if not os.path.exists(droids_dir):
        return []
    return [d for d in os.listdir(droids_dir) if os.path.isdir(os.path.join(droids_dir, d))]


def uninstall_tool(tool_name):
    """Uninstall a specified tool by removing its directory."""
    logger.info(f"Attempting to uninstall {tool_name}...")

    tool_path = os.path.join(INSTALL_DIR, tool_name)

    if not os.path.exists(tool_path):
        logger.error(f"Error: {tool_name} is not installed.")
        return

    try:
        shutil.rmtree(tool_path)
        logger.success(f"{tool_name} has been successfully uninstalled.")
    except OSError as e:
        logger.error(f"Error uninstalling {tool_name}: {e}")


def update_tool(tool_name):
    """Update a specified tool to the latest version."""
    logger.info(f"Attempting to update {tool_name}...")

    installed_tools = list_installed_tools()

    if tool_name.lower() == 'jdk':
        if installed_tools["java_jdk"]:
            for jdk_version in installed_tools["java_jdk"]:
                uninstall_tool(f"jdk-{jdk_version}")
            install_jdk("17")  # LTS default
        else:
            logger.info("JDK is not installed. Installing the latest version (17)...")
            install_jdk("17")
    elif tool_name.lower() == 'android-sdk':
        conf = config.load_config()
        if installed_tools["android_sdk"]:
            logger.info("Android SDK is already installed. Updating components...")
            install_sdk(conf.get("android", {}).get("sdk_version"), conf.get("android", {}).get("cmdline_tools_version"))
        else:
            logger.info("Android SDK is not installed. Installing...")
            install_sdk(conf.get("android", {}).get("sdk_version"), conf.get("android", {}).get("cmdline_tools_version"))
    else:
        logger.error(f"Error: {tool_name} is not a valid tool to update.")


def search_tool(tool_name):
    """Search for available versions of a specified tool."""
    logger.info(f"Searching for available versions of {tool_name}...")

    if tool_name.lower() == 'jdk':
        for version in ["11", "17", "21"]:  # common LTS
            url = _get_latest_temurin_jdk_url(version)
            if url:
                logger.info(f"Found JDK {version}: {url}")
            else:
                logger.info(f"Could not find JDK {version}")
    elif tool_name.lower() == 'android-sdk':
        logger.info("Android SDK versions can be found on the Android developer website:")
        logger.info("https://developer.android.com/studio/releases/sdk-tools")
    elif tool_name.lower() == 'android-ndk':
        logger.info("Android NDK versions can be found on the Android developer website:")
        logger.info("https://developer.android.com/ndk/downloads")
    else:
        logger.error(f"Error: {tool_name} is not a valid tool to search for.")


def check_environment():
    """Check if all required tools are installed and environment variables are set."""
    logger.info("Checking DroidBuilder environment...")
    conf = config.load_config()
    if not conf:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return

    installed_tools = list_installed_tools()
    all_ok = True

    # Required tools
    if not installed_tools["android_sdk"]:
        logger.warning("Android SDK is not installed. Run 'droidbuilder install-tools'.")
        all_ok = False
    if not installed_tools["android_ndk"]:
        logger.warning("Android NDK is not installed. Run 'droidbuilder install-tools'.")
        all_ok = False
    if not installed_tools["java_jdk"]:
        logger.warning("Java JDK is not installed. Run 'droidbuilder install-tools'.")
        all_ok = False

    # Environment variables
    if "ANDROID_HOME" not in os.environ:
        logger.warning("ANDROID_HOME environment variable is not set.")
        all_ok = False
    if "ANDROID_NDK_HOME" not in os.environ:
        logger.warning("ANDROID_NDK_HOME environment variable is not set.")
        all_ok = False
    if "JAVA_HOME" not in os.environ:
        logger.warning("JAVA_HOME environment variable is not set.")
        all_ok = False

    if all_ok:
        logger.success("DroidBuilder environment is set up correctly!")
    else:
        logger.error("DroidBuilder environment has issues. Please fix them and run 'droidbuilder doctor' again.")
