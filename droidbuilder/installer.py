import click
import os
import requests
import zipfile
import tarfile
import subprocess
import shutil
import sys
from .cli_logger import logger

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")

def _download_and_extract(url, dest_dir, filename=None):
    os.makedirs(dest_dir, exist_ok=True)
    if filename is None:
        filename = url.split('/')[-1]
    filepath = os.path.join(dest_dir, filename)

    logger.info(f"  - Downloading {filename}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        downloaded_size = 0
        start_time = time.time()
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded_size += len(chunk)
                # Update progress bar
                done = int(50 * downloaded_size / total_size) if total_size else 0
                percentage = int(100 * downloaded_size / total_size) if total_size else 0
                elapsed_time = time.time() - start_time
                speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
                speed_str = f"{speed / (1024 * 1024):.2f} MB/s" if speed > (1024 * 1024) else f"{speed / 1024:.2f} KB/s"
                sys.stdout.write(f"\r  [{'=' * done}{' ' * (50 - done)}] {percentage}% {downloaded_size / (1024 * 1024):.2f}/{total_size / (1024 * 1024):.2f} MB ({speed_str})")
                sys.stdout.flush()
            sys.stdout.write("\n") # New line after download completes

    logger.info(f"  - Extracting {filename} to {dest_dir}...")
    if filename.endswith(".zip"):
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            for member in zip_ref.infolist():
                logger.info(f"    inflating: {member.filename}")
                zip_ref.extract(member, dest_dir)
    elif filename.endswith(".tar.gz") or filename.endswith(".tgz"):
        with tarfile.open(filepath, 'r:gz') as tar_ref:
            for member in tar_ref.getmembers():
                logger.info(f"    extracting: {member.name}")
                tar_ref.extract(member, dest_dir)
    else:
        logger.warning(f"Warning: Unknown archive type for {filename}. Skipping extraction.")
    os.remove(filepath)
    logger.info(f"  - Extracted to {dest_dir}")


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
