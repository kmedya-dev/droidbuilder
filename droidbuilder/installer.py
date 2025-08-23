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



def install_sdk(version):
    click.echo(f"  - Installing Android SDK version {version}...")
    # TODO: Implement actual SDK download and installation

def install_ndk(version):
    click.echo(f"  - Installing Android NDK version {version}...")
    # TODO: Implement actual NDK download and installation

def install_jdk(version):
    click.echo(f"  - Installing JDK version {version}...")
    # TODO: Implement actual JDK download and installation

def install_py2jib():
    click.echo("  - Installing py2jib...")
    # TODO: Implement py2jib installation (e.g., pip install py2jib)

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

    install_py2jib()

    if ci_mode:
        click.echo("  - Accepting Android SDK licenses (CI mode)...")
        # TODO: Implement automated license acceptance
