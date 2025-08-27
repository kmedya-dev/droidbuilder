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

def _download_and_extract(url, dest_dir, filename=None):
    os.makedirs(dest_dir, exist_ok=True)
    if filename is None:
        filename = url.split('/')[-1]
    filepath = os.path.join(dest_dir, filename)

    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            temp_filepath = filepath + ".tmp"
            with open(temp_filepath, 'wb') as f:
                chunks = r.iter_content(chunk_size=8192)
                iterable = logger.progress(
                    chunks,
                    description=f"Downloading {filename}",
                    total=total_size,
                    unit="b"
                )
                for chunk in iterable:
                    f.write(chunk)
            
            os.rename(temp_filepath, filepath)

        logger.step_info(f"Archive:  {filename}")
        if filename.endswith(".zip"):
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                infolist = zip_ref.infolist()
                for member in infolist:
                    target_path = os.path.join(dest_dir, member.filename)
                    if member.is_dir():
                        logger.step_info(f"creating: {member.filename}", indent=3)
                    elif os.path.exists(target_path):
                        logger.step_info(f" replace: {member.filename}", indent=2)
                    else:
                        logger.step_info(f"inflating: {member.filename}", indent=2)
                    zip_ref.extract(member, dest_dir)
        elif filename.endswith((".tar.gz", ".tgz")):
            with tarfile.open(filepath, 'r:gz') as tar_ref:
                members = tar_ref.getmembers()
                for member in members:
                    target_path = os.path.join(dest_dir, member.name)
                    if member.isdir():
                        logger.step_info(f"creating: {member.name}", indent=3)
                    elif os.path.exists(target_path):
                        logger.step_info(f" replace: {member.name}", indent=2)
                    else:
                        logger.step_info(f"extracting: {member.name}", indent=2)
                    tar_ref.extract(member, dest_dir)
        else:
            logger.warning(f"Unsupported archive type for {filename}. Skipping extraction.")
            return

        os.remove(filepath)
        logger.success(f"Successfully extracted to {dest_dir}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading the file: {e}")
    except (zipfile.BadZipFile, tarfile.TarError, IOError) as e:
        logger.error(f"Error during extraction: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.exception(*sys.exc_info())


def _get_latest_temurin_jdk_url(version):
    api_url = f"https://api.github.com/repos/adoptium/temurin{version}-binaries/releases/latest"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        release_info = response.json()
        
        # Find the asset for linux x64 tar.gz
        for asset in release_info['assets']:
            if f"OpenJDK{version}U-jdk_x64_linux_hotspot" in asset['name'] and asset['name'].endswith(".tar.gz"):
                return asset['browser_download_url']
        
        logger.error(f"Error: Could not find a suitable JDK asset for Temurin {version} on Linux x64.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching latest Temurin JDK release for version {version}: {e}")
        return None
    except KeyError:
        logger.error(f"Error parsing GitHub API response for Temurin {version}.")
        return None

def install_sdk(version, cmdline_tools_version):
    logger.info(f"  - Installing Android SDK version {version}...")
    sdk_url = f"https://dl.google.com/android/repository/commandlinetools-linux-{cmdline_tools_version}_latest.zip"
    sdk_install_dir = os.path.join(INSTALL_DIR, "android-sdk")
    _download_and_extract(sdk_url, sdk_install_dir)

    # After extraction, the content is typically in a 'cmdline-tools' directory
    # within sdk_install_dir. However, sometimes the extracted zip creates
    # an outer 'cmdline-tools' directory that contains the actual tools.
    
    # Find the actual root of the command-line tools (the directory containing 'bin')
    actual_tools_root = sdk_install_dir
    
    # Check for the common case: sdk_install_dir/cmdline-tools/bin
    if os.path.exists(os.path.join(sdk_install_dir, "cmdline-tools", "bin")):
        actual_tools_root = os.path.join(sdk_install_dir, "cmdline-tools")
    else:
        # Check for the nested case: sdk_install_dir/cmdline-tools/cmdline-tools/bin
        if os.path.exists(os.path.join(sdk_install_dir, "cmdline-tools", "cmdline-tools", "bin")):
            actual_tools_root = os.path.join(sdk_install_dir, "cmdline-tools", "cmdline-tools")

    # Create the 'latest' directory where the tools will reside
    final_cmdline_tools_path = os.path.join(sdk_install_dir, "cmdline-tools", "latest")
    os.makedirs(final_cmdline_tools_path, exist_ok=True)

    # Move the *contents* of the actual_tools_root into the 'latest' directory
    for item in os.listdir(actual_tools_root):
        shutil.move(os.path.join(actual_tools_root, item), final_cmdline_tools_path)

    # Remove the original extracted directory if it's not the sdk_install_dir itself
    if actual_tools_root != sdk_install_dir:
        shutil.rmtree(actual_tools_root)

    sdk_manager = os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin", "sdkmanager")
    if not os.path.exists(sdk_manager):
        logger.error(f"Error: sdkmanager not found at {sdk_manager}. SDK installation failed.")
        return

    os.environ["ANDROID_HOME"] = sdk_install_dir
    os.environ["PATH"] += os.pathsep + os.path.join(sdk_install_dir, "platform-tools")
    os.environ["PATH"] += os.pathsep + os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin")

    logger.info(f"  - Installing Android SDK Platform {version} and build-tools...")
    try:
        subprocess.run([sdk_manager, f"platforms;android-{version}", f"build-tools;{version}.0.0", "platform-tools"], check=True, capture_output=True, text=True)
        logger.info("  - Android SDK components installed.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing SDK components: {e.stderr}")
        logger.info("Please ensure the SDK version is valid and try again.")

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
        ndk_path = os.path.join(sdk_install_dir, "ndk", version) # NDK is installed under ndk/<version>
        os.environ["ANDROID_NDK_HOME"] = ndk_path
        os.environ["PATH"] += os.pathsep + ndk_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing NDK components: {e.stderr}")
        logger.info("Please ensure the NDK version is valid and try again.")

def install_jdk(version):
    logger.info(f"  - Installing JDK version {version}...")
    
    jdk_url = _get_latest_temurin_jdk_url(version)
    if not jdk_url:
        logger.error(f"  - Failed to get download URL for JDK version {version}. Aborting installation.")
        return

    jdk_install_dir = os.path.join(INSTALL_DIR, f"jdk-{version}")
    _download_and_extract(jdk_url, jdk_install_dir)

    # JDK usually extracts into a folder like 'jdk-XX.X.X+X'
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



def _accept_sdk_licenses(sdk_install_dir):
    logger.info("  - Accepting Android SDK licenses...")
    sdk_manager = os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin", "sdkmanager")
    if not os.path.exists(sdk_manager):
        logger.error(f"Error: sdkmanager not found at {sdk_manager}. Cannot accept licenses.")
        return

    try:
        # Use expect-style input for automated license acceptance
        p = subprocess.Popen([sdk_manager, "--licenses"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = p.communicate(input='y\n' * 10) # Send 'y' multiple times
        if p.returncode == 0:
            logger.info("  - Android SDK licenses accepted.")
        else:
            logger.error(f"Error accepting licenses: {stderr}")
    except Exception as e:
        logger.error(f"An error occurred during license acceptance: {e}")
        import sys
        logger.exception(*sys.exc_info())

def setup_tools(config, ci_mode=False):
    logger.info("Setting up development tools...")
    sdk_version = config.get("android", {}).get("sdk_version")
    ndk_version = config.get("android", {}).get("ndk_version")
    jdk_version = config.get("java", {}).get("jdk_version")
    cmdline_tools_version = config.get("android", {}).get("cmdline_tools_version")
    sdk_install_dir = os.path.join(INSTALL_DIR, "android-sdk")

    if sdk_version:
        install_sdk(sdk_version, cmdline_tools_version)
    if ndk_version:
        install_ndk(ndk_version, sdk_install_dir)
    if jdk_version:
        install_jdk(jdk_version)

    if ci_mode:
        sdk_install_dir = os.path.join(INSTALL_DIR, "android-sdk")
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

    # Check for Android SDK
    sdk_dir = os.path.join(INSTALL_DIR, "android-sdk", "platforms")
    if os.path.exists(sdk_dir):
        installed["android_sdk"] = [p.replace("android-", "") for p in os.listdir(sdk_dir) if p.startswith("android-")]

    # Check for Android NDK
    ndk_dir = os.path.join(INSTALL_DIR, "android-sdk", "ndk")
    if os.path.exists(ndk_dir):
        installed["android_ndk"] = os.listdir(ndk_dir)

    # Check for Java JDK
    for item in os.listdir(INSTALL_DIR):
        if item.startswith("jdk-"):
            installed["java_jdk"].append(item.replace("jdk-", ""))

    return installed


def list_installed_droids():
    """Scan the installation directory and list installed droids."""
    droids_dir = os.path.join(INSTALL_DIR, "droids")
    if not os.path.exists(droids_dir):
        return []
    return os.listdir(droids_dir)

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
            install_jdk("17") # Assuming 17 is the latest version
        else:
            logger.info("JDK is not installed. Installing the latest version...")
            install_jdk("17")
    elif tool_name.lower() == 'android-sdk':
        if installed_tools["android_sdk"]:
            logger.info("Android SDK is already installed. Updating components...")
            # The install_sdk function seems to handle updates implicitly
            conf = config.load_config()
            install_sdk(conf.get("android", {}).get("sdk_version"), conf.get("android", {}).get("cmdline_tools_version"))
        else:
            logger.info("Android SDK is not installed. Installing the latest version...")
            conf = config.load_config()
            install_sdk(conf.get("android", {}).get("sdk_version"), conf.get("android", {}).get("cmdline_tools_version"))
    else:
        logger.error(f"Error: {tool_name} is not a valid tool to update.")

def search_tool(tool_name):
    """Search for available versions of a specified tool."""
    logger.info(f"Searching for available versions of {tool_name}...")

    if tool_name.lower() == 'jdk':
        for version in ["11", "17", "21"]: # Common LTS versions
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

    # Check for required tools
    if not installed_tools["android_sdk"]:
        logger.warning("Android SDK is not installed. Run 'droidbuilder install-tools'.")
        all_ok = False
    if not installed_tools["android_ndk"]:
        logger.warning("Android NDK is not installed. Run 'droidbuilder install-tools'.")
        all_ok = False
    if not installed_tools["java_jdk"]:
        logger.warning("Java JDK is not installed. Run 'droidbuilder install-tools'.")
        all_ok = False

    # Check environment variables
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
