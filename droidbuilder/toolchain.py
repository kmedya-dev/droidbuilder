import os
import sys
import json
import shutil
import requests
import platform
import subprocess
from . import config
from .cli_logger import logger
from .utils import download, extract_file, run_shell_command, move_files

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")


# -------------------- JDK (Temurin) --------------------

def _get_available_jdk_versions():
    """Get available JDK versions from Adoptium API."""
    api_url = "https://api.adoptium.net/v3/info/available_releases"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        return data.get("available_lts_releases", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching available JDK versions: {e}")
        return []


def _get_latest_temurin_jdk_url(version):
    """Get the latest Temurin JDK URL for a specific version."""
    arch = platform.machine()
    if arch == "x86_64":
        arch = "x64"
    elif arch == "aarch64":
        arch = "aarch64"
    else:
        logger.error(f"Unsupported architecture for JDK download: {arch}")
        return None

    api_url = f"https://api.adoptium.net/v3/assets/latest/{version}/hotspot?vendor=eclipse&os=linux&architecture={arch}&image_type=jdk"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        if data and isinstance(data, list) and data[0].get("binary", {}).get("package", {}).get("link"):
            return data[0]["binary"]["package"]["link"]
        else:
            logger.error(f"Could not find a download link for JDK {version} for architecture {arch}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching JDK download URL: {e}")
        return None

# -------------------- Android SDK --------------------

def _get_sdk_manager(sdk_install_dir):
    """Get the path to the sdkmanager executable."""
    sdk_manager = os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin", "sdkmanager")
    if not os.path.exists(sdk_manager):
        return None
    try:
        os.chmod(sdk_manager, 0o755)
    except OSError as e:
        logger.error(f"Error setting executable permissions for sdkmanager at {sdk_manager}: {e}")
        return None
    return sdk_manager

def _check_sdk_manager(sdk_install_dir):
    sdk_manager = _get_sdk_manager(sdk_install_dir)
    if sdk_manager is None:
        return False
    return True

def install_cmdline_tools(cmdline_tools_version, verbose=False):
    """Install the Android command-line tools."""
    sdk_install_dir = os.path.join(INSTALL_DIR, "android-sdk")
    cmdline_tools_dir = os.path.join(sdk_install_dir, "cmdline-tools")
    latest_dir = os.path.join(cmdline_tools_dir, "latest")

    if os.path.exists(latest_dir):
        logger.info("  - Android command-line tools are already installed. Skipping.")
        os.environ["ANDROID_HOME"] = sdk_install_dir
        os.environ["PATH"] += os.pathsep + os.path.join(sdk_install_dir, "platform-tools")
        os.environ["PATH"] += os.pathsep + os.path.join(latest_dir, "bin")
        return True

    logger.info(f"  - Installing Android command-line tools version {cmdline_tools_version}...")
    sdk_url = f"https://dl.google.com/android/repository/commandlinetools-linux-{cmdline_tools_version}_latest.zip"

    try:
        archive_path = download(sdk_url, timeout=30)
        if not archive_path:
            return False

        if not extract_file(archive_path, cmdline_tools_dir, verbose=verbose):
            os.remove(archive_path)
            return False

        if os.path.exists(latest_dir):
            os.rmdir(latest_dir)
        move_files(cmdline_tools_dir, latest_dir)

        os.environ["ANDROID_HOME"] = sdk_install_dir
        os.environ["PATH"] += os.pathsep + os.path.join(sdk_install_dir, "platform-tools")
        os.environ["PATH"] += os.pathsep + os.path.join(latest_dir, "bin")
        return True
    except Exception as e:
        logger.error(f"Error installing command-line tools: {e}")
        return False

def install_sdk_packages(version, sdk_install_dir, jdk_install_dir, verbose=False):
    """Install Android SDK packages."""
    sdk_manager = _get_sdk_manager(sdk_install_dir)
    if not _check_sdk_manager(sdk_install_dir):
        return False

    platform_dir = os.path.join(sdk_install_dir, "platforms", f"android-{version}")
    if os.path.exists(platform_dir):
        logger.info(f"  - Android SDK platform {version} is already installed. Skipping.")
        return True

    env = os.environ.copy()
    env["JAVA_HOME"] = jdk_install_dir

    try:
        result = run_shell_command(f"{sdk_manager} --list", description="📃 Listing available SDK packages...", env=env)
        for line in result['stdout'].splitlines():
            logger.step_info(line.strip(), overwrite=not verbose, verbose=verbose)
        if result['returncode'] != 0:
            raise subprocess.CalledProcessError(result['returncode'], f"{sdk_manager} --list")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to list SDK packages: {e}")
        return False
    try:
        result = run_shell_command(f"{sdk_manager} 'platforms;android-{version}' 'build-tools;{version}.0.0' 'platform-tools'", description=f"📦 Installing Android SDK components for API {version}...", env=env)
        for line in result['stdout'].splitlines():
            logger.step_info(line.strip(), overwrite=not verbose, verbose=verbose)
        if result['returncode'] != 0:
            raise subprocess.CalledProcessError(result['returncode'], f"{sdk_manager} platforms;android-{version}")
        logger.info("  - Android SDK components installed.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"SDK installation failed (Exit code {e.returncode})")
        return False
    except FileNotFoundError as e:
        logger.error(f"SDK installation failed: {e}. Is sdkmanager in your PATH?")
        return False

# -------------------- Android NDK --------------------

def install_ndk(version, sdk_install_dir, jdk_install_dir, verbose=False):
    """Install Android NDK."""
    ndk_path = os.path.join(sdk_install_dir, "ndk", version)
    if os.path.exists(ndk_path):
        logger.info(f"  - Android NDK version {version} is already installed. Skipping.")
        os.environ["ANDROID_NDK_HOME"] = ndk_path
        os.environ["PATH"] += os.pathsep + ndk_path
        return True

    sdk_manager = _get_sdk_manager(sdk_install_dir)
    if not _check_sdk_manager(sdk_install_dir):
        return False

    env = os.environ.copy()
    env["JAVA_HOME"] = jdk_install_dir

    try:
        result = run_shell_command(f"{sdk_manager} 'ndk;{version}'", description=f"📦 Installing Android NDK {version}...", env=env)
        for line in result['stdout'].splitlines():
            logger.step_info(line.strip(), overwrite=not verbose, verbose=verbose)
        if result['returncode'] != 0:
            raise subprocess.CalledProcessError(result['returncode'], f"{sdk_manager} ndk;{version}")

        os.environ["ANDROID_NDK_HOME"] = ndk_path
        os.environ["PATH"] += os.pathsep + ndk_path
        logger.info("  - Android NDK components installed.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"NDK installation failed (Exit code {e.returncode})")
        return False
    except FileNotFoundError as e:
        logger.error(f"NDK installation failed: {e}. Is sdkmanager in your PATH?")
        return False


# -------------------- JDK --------------------

def install_jdk(version, verbose=False):
    """Install Java Development Kit (JDK)."""
    jdk_install_dir = os.path.join(INSTALL_DIR, f"jdk-{version}")
    if os.path.exists(jdk_install_dir):
        logger.info(f"  - JDK version {version} is already installed. Skipping.")
        os.environ["JAVA_HOME"] = jdk_install_dir
        os.environ["PATH"] += os.pathsep + os.path.join(jdk_install_dir, "bin")
        return True

    logger.info(f"  - Installing JDK version {version}...")
    jdk_url = _get_latest_temurin_jdk_url(version)
    if not jdk_url:
        return False

    try:
        archive_path = download(jdk_url, timeout=30)
        if not archive_path:
            return False
        if not extract_file(archive_path, jdk_install_dir, verbose=verbose):
            return False
        os.remove(archive_path)

    except Exception as e:
        logger.error(f"Error downloading and extracting JDK: {e}")
        return False

    # Set environment variables
    os.environ["JAVA_HOME"] = jdk_install_dir
    os.environ["PATH"] += os.pathsep + os.path.join(jdk_install_dir, "bin")
    return True


# -------------------- Gradle --------------------

def _get_available_gradle_versions():
    """Get available Gradle versions from the official Gradle API."""
    api_url = "https://services.gradle.org/versions/all"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        versions = response.json()
        return [v['version'] for v in versions if not v.get('snapshot', True)] # Return stable versions
    except (requests.exceptions.RequestException, json.jsonDecodeError) as e:
        logger.error(f"Error fetching available Gradle versions: {e}")
        return []

def _get_gradle_download_url(version):
    """Get the download URL for a specific Gradle version."""
    return f"https://services.gradle.org/distributions/gradle-{version}-bin.zip"


def install_gradle(version, verbose=False):
    """Install Gradle."""
    gradle_install_dir = os.path.join(INSTALL_DIR, f"gradle-{version}")
    if os.path.exists(gradle_install_dir):
        logger.info(f"  - Gradle version {version} is already installed. Skipping.")
        os.environ["GRADLE_HOME"] = gradle_install_dir
        os.environ["PATH"] += os.pathsep + os.path.join(gradle_install_dir, "bin")
        return True

    logger.info(f"  - Installing Gradle version {version}...")
    gradle_url = _get_gradle_download_url(version)

    try:
        archive_path = download(gradle_url, timeout=30)
        if not archive_path:
            return False
        if not extract_file(archive_path, gradle_install_dir, verbose=verbose):
            return False
        os.remove(archive_path)

    except Exception as e:
        logger.error(f"Error downloading and extracting gradle: {e}")
        return False

    # Set environment variables
    os.environ["GRADLE_HOME"] = gradle_install_dir
    os.environ["PATH"] += os.pathsep + os.path.join(gradle_install_dir, "bin")
    return True


# -------------------- Licenses --------------------

def _accept_sdk_licenses(sdk_install_dir, jdk_install_dir):
    """Accept Android SDK licenses."""
    logger.info("  - Accepting Android SDK licenses...")
    sdk_manager = _get_sdk_manager(sdk_install_dir)
    if not sdk_manager:
        logger.error("sdkmanager is not available. Cannot accept SDK licenses.")
        return False

    env = os.environ.copy()
    env["JAVA_HOME"] = jdk_install_dir

    try:
        result = run_shell_command(
            [sdk_manager, "--licenses"],
            description="  - Attempting to automatically accept SDK licenses...",
            input_data="y\n" * 20, # Send multiple 'y' responses
            env=env
        )

        if result['returncode'] != 0:
            logger.warning(f"sdkmanager --licenses exited with a non-zero code ({result['returncode']}), which may be normal.")
            if result['stderr']:
                logger.warning(f"Stderr:\n{result['stderr']}")
        
        logger.info("  - License acceptance process finished.")
        return True

    except Exception as e:
        logger.error(f"An unexpected error occurred during license acceptance: {e}")
        logger.exception(*sys.exc_info())
        return False


# -------------------- Orchestrators --------------------

def setup_tools(conf, verbose=False):
    """Install all the required tools."""
    logger.info("Setting up development tools...")
    sdk_version = conf.get("android", {}).get("sdk_version")
    ndk_version = conf.get("android", {}).get("ndk_version")
    jdk_version = conf.get("java", {}).get("jdk_version")
    gradle_version = conf.get("java", {}).get("gradle_version")
    cmdline_tools_version = conf.get("android", {}).get("cmdline_tools_version")
    accept_sdk_license = conf.get("android", {}).get("accept_sdk_license", "non-interactive")
    sdk_install_dir = os.path.join(INSTALL_DIR, "android-sdk")

    all_successful = True

    jdk_install_dir = os.path.join(INSTALL_DIR, f"jdk-{jdk_version}")

    if jdk_version:
        if not install_jdk(jdk_version, verbose=verbose):
            logger.error(f"Failed to install Java JDK version {jdk_version}.")
            all_successful = False

    # Set JAVA_HOME in the environment for subsequent sdkmanager calls
    if all_successful and jdk_install_dir and os.path.exists(jdk_install_dir):
        os.environ["JAVA_HOME"] = jdk_install_dir

    if cmdline_tools_version:
        if not install_cmdline_tools(cmdline_tools_version, verbose=verbose):
            logger.error("Failed to install Android command-line tools.")
            all_successful = False

    if accept_sdk_license == "non-interactive":
        if not _accept_sdk_licenses(sdk_install_dir, jdk_install_dir):
            logger.error("Failed to accept Android SDK licenses.")
            all_successful = False

    if sdk_version:
        if not install_sdk_packages(sdk_version, sdk_install_dir, jdk_install_dir):
            logger.error(f"Failed to install Android SDK Platform {sdk_version}.")
            all_successful = False

    if ndk_version:
        if not install_ndk(ndk_version, sdk_install_dir, jdk_install_dir):
            logger.error(f"Failed to install Android NDK version {ndk_version}.")
            all_successful = False

    if gradle_version:
        if not install_gradle(gradle_version, verbose=verbose):
            logger.error(f"Failed to install Gradle version {gradle_version}.")
            all_successful = False

    if all_successful:
        _create_env_file(sdk_install_dir, ndk_version, jdk_version, jdk_install_dir)

    return all_successful

def _create_env_file(sdk_install_dir, ndk_version, jdk_version, jdk_install_dir):
    """Create a shell script to set environment variables."""
    env_file_path = os.path.join(INSTALL_DIR, "env.sh")
    os.makedirs(os.path.dirname(env_file_path), exist_ok=True)

    with open(env_file_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f"export ANDROID_HOME={sdk_install_dir}\n")
        if ndk_version:
            f.write(f"export ANDROID_NDK_HOME={os.path.join(sdk_install_dir, 'ndk', ndk_version)}\n")
            f.write(f"export ANDROID_NDK_ROOT={os.path.join(sdk_install_dir, 'ndk', ndk_version)}\n")
        if jdk_install_dir and os.path.exists(jdk_install_dir):
            f.write(f"export JAVA_HOME={jdk_install_dir}\n")
        f.write("export PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_NDK_HOME:$JAVA_HOME/bin:$PATH\n")

    logger.info(f"Environment script created at {env_file_path}")
    logger.info(f"Run 'source {env_file_path}' to set up your environment.")

def list_installed_tools():
    """Scan the installation directory and list installed tools and versions."""
    installed = {
        "android_sdk": [],
        "android_ndk": [],
        "java_jdk": [],
        "gradle": [],
        "android_cmdline_tools": False,
    }

    if not os.path.exists(INSTALL_DIR):
        return installed

    try:
        # Android SDK
        sdk_dir = os.path.join(INSTALL_DIR, "android-sdk", "platforms")
        if os.path.exists(sdk_dir):
            installed["android_sdk"] = [
                p.replace("android-", "") for p in os.listdir(sdk_dir)
                if p.startswith("android-") and os.path.isdir(os.path.join(sdk_dir, p))
            ]

        # Android NDK
        ndk_dir = os.path.join(INSTALL_DIR, "android-sdk", "ndk")
        if os.path.exists(ndk_dir):
            installed["android_ndk"] = [d for d in os.listdir(ndk_dir) if os.path.isdir(os.path.join(ndk_dir, d))]

        # Java JDK and Gradle
        for item in os.listdir(INSTALL_DIR):
            path = os.path.join(INSTALL_DIR, item)
            if not os.path.isdir(path):
                continue
            if item.startswith("jdk-"):
                installed["java_jdk"].append(item.replace("jdk-", ""))
            if item.startswith("gradle-"):
                installed["gradle"].append(item.replace("gradle-", ""))
    except OSError as e:
        logger.warning(f"Could not fully scan for installed tools: {e}")

    # Android Command-line Tools
    cmdline_tools_path = os.path.join(INSTALL_DIR, "android-sdk", "cmdline-tools", "latest", "bin", "sdkmanager")
    if os.path.exists(cmdline_tools_path):
        installed["android_cmdline_tools"] = True

    return installed


def uninstall_tool(tool_name):
    """Uninstall a specified tool by removing its directory."""
    logger.info(f"Attempting to uninstall {tool_name}...")

    tool_path = os.path.join(INSTALL_DIR, tool_name)
    if not os.path.exists(tool_path):
        logger.info(f"{tool_name} is not installed at {tool_path}. Nothing to uninstall.")
        return True

    try:
        os.rmdir(tool_path)
        logger.success(f"{tool_name} has been successfully uninstalled.")
        return True
    except OSError as e:
        logger.error(f"Error uninstalling {tool_name} from {tool_path}: {e}")
        logger.info("Please check file permissions and ensure the directory is not in use.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while uninstalling {tool_name}: {e}")
        logger.exception(*sys.exc_info())
        return False


def update_tool(tool_name):
    """Update a specified tool to the latest version."""
    logger.info(f"Attempting to update {tool_name}...")

    installed_tools = list_installed_tools()
    success = True

    if tool_name.lower() == 'jdk':
        if installed_tools["java_jdk"]:
            for jdk_version in installed_tools["java_jdk"]:
                if not uninstall_tool(f"jdk-{jdk_version}"):
                    success = False
                    logger.error(f"Failed to uninstall existing JDK version {jdk_version}. Aborting update.")
                    return False # Abort if uninstall fails
        
        available_jdks = _get_available_jdk_versions()
        if not available_jdks:
            logger.error("Could not retrieve available JDK versions. Cannot update JDK.")
            return False
        latest_jdk = available_jdks[0] # Assuming the first one is the latest or desired
        if not install_jdk(latest_jdk, verbose=True):
            success = False
            logger.error(f"Failed to install latest JDK version {latest_jdk}.")
    elif tool_name.lower() == 'gradle':
        if installed_tools["gradle"]:
            for gradle_version in installed_tools["gradle"]:
                if not uninstall_tool(f"gradle-{gradle_version}"):
                    success = False
                    logger.error(f"Failed to uninstall existing Gradle version {gradle_version}. Aborting update.")
                    return False # Abort if uninstall fails
        
        available_gradle = _get_available_gradle_versions()
        if not available_gradle:
            logger.error("Could not retrieve available Gradle versions. Cannot update Gradle.")
            return False
        latest_gradle = available_gradle[0] # Assuming the first one is the latest or desired
        if not install_gradle(latest_gradle, verbose=True):
            success = False
            logger.error(f"Failed to install latest Gradle version {latest_gradle}.")
    elif tool_name.lower() == 'android-sdk':
        conf = config.load_config()
        if not conf:
            logger.error("Error: droidbuilder.toml not found. Cannot update Android SDK.")
            return False

        cmdline_tools_version = conf.get("android", {}).get("cmdline_tools_version")
        sdk_version = conf.get("android", {}).get("sdk_version")
        sdk_install_dir = os.path.join(INSTALL_DIR, "android-sdk")

        if installed_tools["android_cmdline_tools"] or cmdline_tools_version:
            logger.info("Updating Android command-line tools...")
            if not install_cmdline_tools(cmdline_tools_version, verbose=True):
                success = False
                logger.error("Failed to update Android command-line tools.")
        else:
            logger.warning("Android command-line tools version not specified in droidbuilder.toml. Skipping update.")

        if installed_tools["android_sdk"] or sdk_version:
            logger.info("Updating Android SDK packages...")
            jdk_install_dir = os.path.join(INSTALL_DIR, f"jdk-{conf.get('java',{}).get('jdk_version')}")
            if not install_sdk_packages(sdk_version, sdk_install_dir, jdk_install_dir, verbose=True):
                success = False
                logger.error("Failed to update Android SDK packages.")
        else:
            logger.warning("Android SDK version not specified in droidbuilder.toml. Skipping update.")
    else:
        logger.error(f"Error: '{tool_name}' is not a valid tool to update. Supported tools are 'jdk', 'gradle', and 'android-sdk'.")
        return False

    if success:
        logger.success(f"Successfully updated {tool_name}.")
    else:
        logger.error(f"Failed to update {tool_name}. Please check the logs for details.")
    return success


def search_tool(tool_name):
    """Search for available versions of a specified tool."""
    logger.info(f"Searching for available versions of {tool_name}...")

    if tool_name.lower() == 'jdk':
        versions = _get_available_jdk_versions()
        if versions:
            logger.info("Available JDK versions:")
            for version in versions:
                logger.info(f"  - {version}")
        else:
            logger.info("Could not find any JDK versions. Please check your internet connection or try again later.")
    elif tool_name.lower() == 'gradle':
        versions = _get_available_gradle_versions()
        if versions:
            logger.info("Available Gradle versions:")
            for version in versions:
                logger.info(f"  - {version}")
        else:
            logger.info("Could not find any Gradle versions. Please check your internet connection or try again later.")
    elif tool_name.lower() == 'android-sdk':
        logger.info("Android SDK versions can be found on the Android developer website:")
        logger.info("https://developer.android.com/studio/releases/sdk-tools")
    elif tool_name.lower() == 'android-ndk':
        logger.info("Android NDK versions can be found on the Android developer website:")
        logger.info("https://developer.android.com/ndk/downloads")
    else:
        logger.error(f"Error: '{tool_name}' is not a valid tool to search for. Supported tools are 'jdk', 'gradle', 'android-sdk', and 'android-ndk'.")


def check_environment():
    """Check if all required tools are installed and environment variables are set."""
    logger.info("Checking DroidBuilder environment...")
    
    conf = None
    try:
        conf = config.load_config()
        if not conf:
            logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
            return False
    except FileNotFoundError:
        logger.error("Error: No droidbuilder.toml found. Please run 'droidbuilder init' first.")
        return False
    except Exception as e:
        logger.error(f"Error loading droidbuilder.toml: {e}")
        logger.info("Please check the file's format and permissions.")
        return False

    installed_tools = list_installed_tools()
    all_ok = True

    # Check for main file
    main_file = conf.get("app", {}).get("main_file", "main.py")
    if not os.path.exists(main_file):
        logger.warning(f"Main file '{main_file}' not found. Please create it or update your droidbuilder.toml.")
        all_ok = False
    elif not os.path.isfile(main_file):
        logger.warning(f"Main file '{main_file}' is not a file. Please ensure it points to a valid file.")
        all_ok = False

    # Required tools
    sdk_version = conf.get("android", {}).get("sdk_version")
    if sdk_version:
        if str(sdk_version) not in installed_tools["android_sdk"]:
            logger.warning(f"Android SDK Platform {sdk_version} is not installed. Run 'droidbuilder install-tools'.")
            all_ok = False

    ndk_version = conf.get("android", {}).get("ndk_version")
    if ndk_version and ndk_version not in installed_tools["android_ndk"]:
        logger.warning(f"Android NDK version {ndk_version} is not installed. Run 'droidbuilder install-tools'.")
        all_ok = False

    jdk_version = conf.get("java", {}).get("jdk_version")
    if jdk_version and str(jdk_version) not in installed_tools["java_jdk"]:
        logger.warning(f"Java JDK version {jdk_version} is not installed. Run 'droidbuilder install-tools'.")
        all_ok = False

    gradle_version = conf.get("java", {}).get("gradle_version")
    if gradle_version and str(gradle_version) not in installed_tools["gradle"]:
        logger.warning(f"Gradle version {gradle_version} is not installed. Run 'droidbuilder install-tools'.")
        all_ok = False

    # Environment variables
    if "ANDROID_HOME" not in os.environ:
        logger.warning(f"ANDROID_HOME environment variable is not set. Run 'source {os.path.join(INSTALL_DIR, 'env.sh')}' or restart your shell.")
        all_ok = False
    if "ANDROID_NDK_HOME" not in os.environ:
        logger.warning(f"ANDROID_NDK_HOME environment variable is not set. Run 'source {os.path.join(INSTALL_DIR, 'env.sh')}' or restart your shell.")
        all_ok = False
    if "JAVA_HOME" not in os.environ:
        logger.warning(f"JAVA_HOME environment variable is not set. Run 'source {os.path.join(INSTALL_DIR, 'env.sh')}' or restart your shell.")
        all_ok = False

    if all_ok:
        logger.success("DroidBuilder environment is set up correctly!")
        return True
    else:
        logger.error("DroidBuilder environment has issues. Please fix them and run 'droidbuilder doctor' again.")
        return False
