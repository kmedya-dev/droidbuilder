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

def install_sdk(version):
    click.echo(f"  - Installing Android SDK version {version}...")
    sdk_url = "https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip"
    sdk_install_dir = os.path.join(INSTALL_DIR, "android-sdk")
    _download_and_extract(sdk_url, sdk_install_dir)

    # The extracted content might be in a 'cmdline-tools' directory, and then 'latest' inside it
    # We need to find the actual tools directory
    cmdline_tools_path = os.path.join(sdk_install_dir, "cmdline-tools")
    if not os.path.exists(cmdline_tools_path):
        # Sometimes it extracts directly into sdk_install_dir
        cmdline_tools_path = sdk_install_dir

    # Find the 'latest' or versioned directory within cmdline-tools
    actual_tools_path = None
    for item in os.listdir(cmdline_tools_path):
        if os.path.isdir(os.path.join(cmdline_tools_path, item)):
            actual_tools_path = os.path.join(cmdline_tools_path, item)
            break

    if actual_tools_path:
        # Move the contents of the actual_tools_path to cmdline-tools/latest
        final_cmdline_tools_path = os.path.join(sdk_install_dir, "cmdline-tools", "latest")
        os.makedirs(final_cmdline_tools_path, exist_ok=True)
        for item in os.listdir(actual_tools_path):
            shutil.move(os.path.join(actual_tools_path, item), final_cmdline_tools_path)
        shutil.rmtree(actual_tools_path) # Remove the old directory

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

def install_ndk(version):
    click.echo(f"  - Installing Android NDK version {version}...")
    # Placeholder URL for NDK. Find specific version from official Android NDK archives.
    ndk_url = f"https://dl.google.com/android/repository/android-ndk-r{version}-linux.zip" # Example: r25b
    ndk_install_dir = os.path.join(INSTALL_DIR, "android-ndk")
    _download_and_extract(ndk_url, ndk_install_dir)

    # NDK usually extracts into a folder like 'android-ndk-rXX'
    extracted_ndk_dir = None
    for item in os.listdir(ndk_install_dir):
        if item.startswith("android-ndk-r") and os.path.isdir(os.path.join(ndk_install_dir, item)):
            extracted_ndk_dir = os.path.join(ndk_install_dir, item)
            break
    
    if extracted_ndk_dir:
        os.environ["ANDROID_NDK_HOME"] = extracted_ndk_dir
        os.environ["PATH"] += os.pathsep + extracted_ndk_dir
        click.echo(f"  - NDK installed to {extracted_ndk_dir}")
    else:
        click.echo("Warning: Could not find extracted NDK directory.")

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

    if sdk_version:
        install_sdk(sdk_version)
    if ndk_version:
        install_ndk(ndk_version)
    if jdk_version:
        install_jdk(jdk_version)

    if ci_mode:
        sdk_install_dir = os.path.join(INSTALL_DIR, "android-sdk")
        _accept_sdk_licenses(sdk_install_dir)
