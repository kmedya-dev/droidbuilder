import click
import os
import requests
import zipfile
import tarfile
import subprocess
import shutil

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")

def _download_and_extract(url, dest_dir, filename=None):
    os.makedirs(dest_dir, exist_ok=True)
    if filename is None:
        filename = url.split('/')[-1]
    filepath = os.path.join(dest_dir, filename)

    click.echo(f"  - Downloading {filename}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    click.echo(f"  - Extracting {filename}...")
    if filename.endswith(".zip"):
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
    elif filename.endswith(".tar.gz") or filename.endswith(".tgz"):
        with tarfile.open(filepath, 'r:gz') as tar_ref:
            tar_ref.extractall(dest_dir)
    else:
        click.echo(f"Warning: Unknown archive type for {filename}. Skipping extraction.")
    os.remove(filepath)
    click.echo(f"  - Extracted to {dest_dir}")


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
        
        click.echo(f"Error: Could not find a suitable JDK asset for Temurin {version} on Linux x64.")
        return None
    except requests.exceptions.RequestException as e:
        click.echo(f"Error fetching latest Temurin JDK release for version {version}: {e}")
        return None
    except KeyError:
        click.echo(f"Error parsing GitHub API response for Temurin {version}.")
        return None

def install_sdk(version, cmdline_tools_version):
    click.echo(f"  - Installing Android SDK version {version}...")
    sdk_url = f"https://dl.google.com/android/repository/commandlinetools-linux-{cmdline_tools_version}_latest.zip"
    sdk_install_dir = os.path.join(INSTALL_DIR, "android-sdk")
    _download_and_extract(sdk_url, sdk_install_dir)

    # After extraction, the content is typically in a 'cmdline-tools' directory
    # within sdk_install_dir.
    extracted_cmdline_tools_root = os.path.join(sdk_install_dir, "cmdline-tools")

    # If the zip extracted directly into sdk_install_dir, then the root is sdk_install_dir itself.
    if not os.path.exists(extracted_cmdline_tools_root):
        extracted_cmdline_tools_root = sdk_install_dir

    # Create the 'latest' directory where the tools will reside
    final_cmdline_tools_path = os.path.join(sdk_install_dir, "cmdline-tools", "latest")
    os.makedirs(final_cmdline_tools_path, exist_ok=True)

    # Move the *contents* of the extracted_cmdline_tools_root into the 'latest' directory
    for item in os.listdir(extracted_cmdline_tools_root):
        shutil.move(os.path.join(extracted_cmdline_tools_root, item), final_cmdline_tools_path)

    # Remove the original extracted directory if it's not the sdk_install_dir itself
    if extracted_cmdline_tools_root != sdk_install_dir:
        shutil.rmtree(extracted_cmdline_tools_root)

    sdk_manager = os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin", "sdkmanager")
    if not os.path.exists(sdk_manager):
        click.echo(f"Error: sdkmanager not found at {sdk_manager}. SDK installation failed.")
        return

    os.environ["ANDROID_HOME"] = sdk_install_dir
    os.environ["PATH"] += os.pathsep + os.path.join(sdk_install_dir, "platform-tools")
    os.environ["PATH"] += os.pathsep + os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin")

    click.echo(f"  - Installing Android SDK Platform {version} and build-tools...")
    try:
        subprocess.run([sdk_manager, f"platforms;android-{version}", f"build-tools;{version}.0.0", "platform-tools"], check=True, capture_output=True, text=True)
        click.echo("  - Android SDK components installed.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error installing SDK components: {e.stderr}")
        click.echo("Please ensure the SDK version is valid and try again.")

def install_ndk(version, sdk_install_dir):
    click.echo(f"  - Installing Android NDK version {version}...")
    
    sdk_manager = os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin", "sdkmanager")
    if not os.path.exists(sdk_manager):
        click.echo(f"Error: sdkmanager not found at {sdk_manager}. Cannot install NDK.")
        return

    try:
        subprocess.run([sdk_manager, f"ndk;{version}"], check=True, capture_output=True, text=True)
        click.echo("  - Android NDK components installed.")
        # Set ANDROID_NDK_HOME and PATH
        ndk_path = os.path.join(sdk_install_dir, "ndk", version) # NDK is installed under ndk/<version>
        os.environ["ANDROID_NDK_HOME"] = ndk_path
        os.environ["PATH"] += os.pathsep + ndk_path
    except subprocess.CalledProcessError as e:
        click.echo(f"Error installing NDK components: {e.stderr}")
        click.echo("Please ensure the NDK version is valid and try again.")

def install_jdk(version):
    click.echo(f"  - Installing JDK version {version}...")
    
    jdk_url = _get_latest_temurin_jdk_url(version)
    if not jdk_url:
        click.echo(f"  - Failed to get download URL for JDK version {version}. Aborting installation.")
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
        click.echo(f"  - JDK installed to {extracted_jdk_dir}")
    else:
        click.echo("Warning: Could not find extracted JDK directory.")



def _accept_sdk_licenses(sdk_install_dir):
    click.echo("  - Accepting Android SDK licenses...")
    sdk_manager = os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin", "sdkmanager")
    if not os.path.exists(sdk_manager):
        click.echo(f"Error: sdkmanager not found at {sdk_manager}. Cannot accept licenses.")
        return

    try:
        # Use expect-style input for automated license acceptance
        p = subprocess.Popen([sdk_manager, "--licenses"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = p.communicate(input='y\n' * 10) # Send 'y' multiple times
        if p.returncode == 0:
            click.echo("  - Android SDK licenses accepted.")
        else:
            click.echo(f"Error accepting licenses: {stderr}")
    except Exception as e:
        click.echo(f"An error occurred during license acceptance: {e}")

def setup_tools(config, ci_mode=False):
    click.echo("Setting up development tools...")
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
