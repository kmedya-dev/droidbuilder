import click
import os
import subprocess
import shutil
import sys
from .cli_logger import logger
from . import utils

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")
BUILD_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder_build")

# Architectures and their compiler prefixes
ARCH_COMPILER_PREFIXES = {
    "arm64-v8a": "aarch64-linux-android",
    "armeabi-v7a": "armv7a-linux-androideabi",
    "x86": "i686-linux-android",
    "x86_64": "x86_64-linux-android",
}

def _setup_python_build_environment(ndk_version, ndk_api, arch):
    """Set up environment variables for cross-compiling Python."""
    logger.info(f"  - Setting up build environment for {arch} (NDK {ndk_version}, API {ndk_api})...")

    ndk_root = os.path.join(INSTALL_DIR, "android-sdk", "ndk", ndk_version)
    if not os.path.exists(ndk_root):
        logger.error(f"Error: NDK root directory not found at {ndk_root}. Please ensure NDK {ndk_version} is installed.")
        return False

    toolchain_bin = os.path.join(ndk_root, "toolchains", "llvm", "prebuilt", "linux-x86_64", "bin")
    if not os.path.exists(toolchain_bin):
        logger.error(f"Error: NDK toolchain binary directory not found at {toolchain_bin}. Please check your NDK installation.")
        return False

    sysroot = os.path.join(toolchain_bin, f"../sysroot") # sysroot is usually relative to toolchain bin
    if not os.path.exists(sysroot):
        logger.error(f"Error: NDK sysroot not found at {sysroot}. Please check your NDK installation.")
        return False

    compiler_prefix = ARCH_COMPILER_PREFIXES.get(arch)
    if not compiler_prefix:
        logger.error(f"Error: Unsupported architecture for Python build: {arch}")
        return False

    os.environ["AR"] = f"{toolchain_bin}/{compiler_prefix}-ar"
    os.environ["CC"] = f"{toolchain_bin}/{compiler_prefix}{ndk_api}-clang"
    os.environ["CXX"] = f"{toolchain_bin}/{compiler_prefix}{ndk_api}-clang++"
    os.environ["LD"] = f"{toolchain_bin}/{compiler_prefix}-ld"
    os.environ["RANLIB"] = f"{toolchain_bin}/{compiler_prefix}-ranlib"
    os.environ["STRIP"] = f"{toolchain_bin}/{compiler_prefix}-strip"
    os.environ["SYSROOT"] = sysroot
    os.environ["PATH"] = f"{toolchain_bin}:{os.environ['PATH']}"

    logger.info("  - Build environment set up.")
    return True

def _build_python_for_android(python_version, ndk_version, ndk_api, arch, build_path):
    """Build Python for a specific Android architecture."""
    logger.info(f"  - Building Python {python_version} for {arch}...")

    python_source_dir = os.path.join(INSTALL_DIR, "python-source")
    if not os.path.exists(python_source_dir):
        logger.error(f"Error: Python source directory not found at {python_source_dir}. Please download Python source first.")
        return False

    python_install_dir = os.path.join(build_path, "python-install", arch)
    try:
        os.makedirs(python_install_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating Python install directory {python_install_dir}: {e}")
        return False

    # Get build triplet
    try:
        build_triplet = subprocess.check_output(["uname", "-m", "-s"]).decode().strip().replace(" ", "-").lower()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error determining build triplet: {e}")
        return False

    # Get host triplet
    host_triplet = ARCH_COMPILER_PREFIXES.get(arch)

    if not host_triplet:
        logger.error(f"Error: Could not determine host triplet for architecture: {arch}")
        return False

    # Configure command
    configure_script = os.path.join(python_source_dir, "configure")
    if not os.path.exists(configure_script):
        logger.error(f"Error: Configure script not found at {configure_script}. Python source might be incomplete.")
        return False

    configure_cmd = [
        configure_script,
        f"--host={host_triplet}",
        f"--build={build_triplet}",
        "--enable-shared",
        "--disable-ipv6",
        "--with-system-ffi=no",
        "--without-ensurepip",
        f"--prefix={python_install_dir}",
        f"CC={os.environ.get('CC', '')}",
        f"CXX={os.environ.get('CXX', '')}",
        f"AR={os.environ.get('AR', '')}",
        f"LD={os.environ.get('LD', '')}",
        f"RANLIB={os.environ.get('RANLIB', '')}",
        f"STRIP={os.environ.get('STRIP', '')}",
        f"SYSROOT={os.environ.get('SYSROOT', '')}",
        f"CFLAGS=-fPIC -DANDROID -D__ANDROID_API__={ndk_api}",
        f"LDFLAGS=-L{os.environ.get('SYSROOT', '')}/usr/lib/{host_triplet}/{ndk_api}",
    ]

    logger.info(f"  - Running configure: {' '.join(configure_cmd)}")
    try:
        subprocess.run(configure_cmd, check=True, cwd=python_source_dir, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Python configure failed (Exit Code: {e.returncode}):")
        if e.stdout:
            logger.error(f"Stdout:\n{e.stdout}")
        if e.stderr:
            logger.error(f"Stderr:\n{e.stderr}")
        logger.info("Please check the Python source, NDK setup, and compiler paths.")
        return False
    except FileNotFoundError:
        logger.error(f"Error: 'configure' command not found. Ensure your PATH is set correctly.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during configure: {e}")
        logger.exception(*sys.exc_info())
        return False

    # Make command
    make_cmd = ["make", "-j", str(os.cpu_count())]
    logger.info(f"  - Running make: {' '.join(make_cmd)}")
    try:
        subprocess.run(make_cmd, check=True, cwd=python_source_dir, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Python make failed (Exit Code: {e.returncode}):")
        if e.stdout:
            logger.error(f"Stdout:\n{e.stdout}")
        if e.stderr:
            logger.error(f"Stderr:\n{e.stderr}")
        logger.info("Please check the build logs for more details on the compilation error.")
        return False
    except FileNotFoundError:
        logger.error(f"Error: 'make' command not found. Ensure 'make' is installed and in your PATH.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during make: {e}")
        logger.exception(*sys.exc_info())
        return False

    # Make install command
    make_install_cmd = ["make", "install"]
    logger.info(f"  - Running make install: {' '.join(make_install_cmd)}")
    try:
        subprocess.run(make_install_cmd, check=True, cwd=python_source_dir, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Python make install failed (Exit Code: {e.returncode}):")
        if e.stdout:
            logger.error(f"Stdout:\n{e.stdout}")
        if e.stderr:
            logger.error(f"Stderr:\n{e.stderr}")
        logger.info("Please check the installation directory permissions and logs.")
        return False
    except FileNotFoundError:
        logger.error(f"Error: 'make' command not found for install. Ensure 'make' is installed and in your PATH.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during make install: {e}")
        logger.exception(*sys.exc_info())
        return False

    logger.success(f"  - Python {python_version} built and installed for {arch}.")
    return True


def _create_android_project(project_name, package_domain, build_path):
    """Create a basic Android project structure by copying from template."""
    logger.info(f"  - Creating Android project structure for {project_name} from template...")

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target", "android")
    
    if not os.path.exists(template_path):
        logger.error(f"Error: Android project template not found at {template_path}")
        return False

    try:
        shutil.copytree(template_path, build_path, dirs_exist_ok=True)
    except (shutil.Error, OSError) as e:
        logger.error(f"Error copying Android project template: {e}")
        logger.info("Please check file permissions and ensure the template directory is accessible.")
        return False

    logger.success(f"  - Android project structure created at {build_path}.")
    return True

def _configure_android_project(build_path, project_name, package_domain, app_version, sdk_version, min_sdk_version, ndk_api, manifest_file):
    """Configure the copied Android project with actual values."""
    logger.info(f"  - Configuring Android project at {build_path}...")

    files_to_configure = {
        "settings.gradle.kts": {
            "path": os.path.join(build_path, "settings.gradle.kts"),
            "replacements": [
                ("rootProject.name = \"MyDroidApp\"", f"rootProject.name = \"{project_name}\""),
            ]
        },
        "app/build.gradle.kts": {
            "path": os.path.join(build_path, "app", "build.gradle.kts"),
            "replacements": [
                ("namespace = \"com.example.myapp\"", f"namespace = \"{package_domain}.{project_name.lower()}\""),
                ("applicationId = \"com.example.myapp\"", f"applicationId = \"{package_domain}.{project_name.lower()}\""),
                ("compileSdk = 34", f"compileSdk = {sdk_version}"),
                ("minSdk = 21", f"minSdk = {min_sdk_version}"),
                ("targetSdk = 34", f"targetSdk = {sdk_version}"),
                ("versionName = \"1.0\"", f"versionName = \"{app_version}\""),
            ]
        },
        "app/src/main/AndroidManifest.xml": {
            "path": os.path.join(build_path, "app", "src", "main", "AndroidManifest.xml"),
            "replacements": [
                ("package=\"com.example.myapp\"", f"package=\"{package_domain}.{project_name.lower()}\""),
            ]
        },
        "app/src/main/res/values/strings.xml": {
            "path": os.path.join(build_path, "app", "src", "main", "res", "values", "strings.xml"),
            "replacements": [
                ("<string name=\"app_name\">MyDroidApp</string>", f"<string name=\"app_name\">{project_name}</string>"),
            ]
        }
    }

    for file_name, details in files_to_configure.items():
        file_path = details["path"]
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                
                for old, new in details["replacements"]:
                    content = content.replace(old, new)
                
                with open(file_path, "w") as f:
                    f.write(content)
                logger.info(f"    - Configured {file_name}")
            except IOError as e:
                logger.error(f"Error configuring {file_name} at {file_path}: {e}")
                logger.info("Please check file permissions and ensure the file is accessible.")
                return False
            except Exception as e:
                logger.error(f"An unexpected error occurred while configuring {file_name}: {e}")
                logger.exception(*sys.exc_info())
                return False

    logger.success("  - Android project configured.")
    return True


def _copy_python_assets(build_path, archs):
    """Copy compiled Python interpreter and modules to Android project assets."""
    logger.info("  - Copying Python assets to Android project...")

    assets_dir = os.path.join(build_path, "app", "src", "main", "assets")
    try:
        os.makedirs(assets_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating assets directory {assets_dir}: {e}")
        return False

    for arch in archs:
        python_install_dir = os.path.join(build_path, "python-install", arch)
        dest_dir = os.path.join(assets_dir, "python", arch)
        
        if not os.path.exists(python_install_dir):
            logger.error(f"Error: Compiled Python for {arch} not found at {python_install_dir}. Please ensure Python was built successfully for this architecture.")
            return False

        try:
            shutil.copytree(python_install_dir, dest_dir, dirs_exist_ok=True)
            logger.info(f"    - Copied Python assets for {arch} to {dest_dir}")
        except (shutil.Error, OSError) as e:
            logger.error(f"Error copying Python assets for {arch} from {python_install_dir} to {dest_dir}: {e}")
            logger.info("Please check directory permissions and ensure enough disk space is available.")
            return False

    logger.success("  - Python assets copied.")
    return True

def _copy_user_python_code(build_path, main_file):
    """Copy user's Python application code to Android project assets."""
    logger.info("  - Copying user's Python code to Android project...")

    user_python_assets_dir = os.path.join(build_path, "app", "src", "main", "assets", "user_python")
    try:
        os.makedirs(user_python_assets_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating user Python assets directory {user_python_assets_dir}: {e}")
        return False

    source_main_file_path = os.path.join(os.getcwd(), main_file)
    dest_main_file_path = os.path.join(user_python_assets_dir, os.path.basename(main_file))

    if not os.path.exists(source_main_file_path):
        logger.error(f"Error: Main Python file not found at {source_main_file_path}. Please ensure '{main_file}' exists in your project root.")
        return False
    if not os.path.isfile(source_main_file_path):
        logger.error(f"Error: '{source_main_file_path}' is not a file. Please ensure 'main_file' in droidbuilder.toml points to a valid file.")
        return False

    try:
        shutil.copyfile(source_main_file_path, dest_main_file_path)
        logger.success(f"  - Copied user's main Python file to {dest_main_file_path}")
    except (shutil.Error, OSError) as e:
        logger.error(f"Error copying user's main Python file from {source_main_file_path} to {dest_main_file_path}: {e}")
        logger.info("Please check file permissions and ensure the source file exists and is readable.")
        return False

    return True

def _download_python_packages(requirements, build_path):
    """Download Python packages for the Android app."""
    logger.info("  - Downloading Python packages...")

    packages_source_dir = os.path.join(build_path, "python-packages-source")
    try:
        os.makedirs(packages_source_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating packages source directory {packages_source_dir}: {e}")
        return False

    for req in requirements:
        package_name = req.split('==')[0]
        package_version = req.split('==')[1] if '==' in req else None
        
        if package_version:
            package_filename = f"{package_name}-{package_version}.tar.gz"
            # PyPI URL structure: https://pypi.org/packages/source/<first-letter-of-package>/<package-name>/<package-name>-<version>.tar.gz
            # Handle cases where package_name[0] might be a digit or special char
            first_char = package_name[0].lower()
            if not first_char.isalpha():
                first_char = '_' # Fallback for non-alphabetic first characters, though uncommon for PyPI
            package_url = f"https://pypi.org/packages/source/{first_char}/{package_name}/{package_filename}"
        else:
            logger.warning(f"  - No version specified for '{package_name}'. Skipping download. Please specify a version (e.g., '{package_name}==1.0.0') in your droidbuilder.toml for reliable downloads.")
            continue

        try:
            utils.download_and_extract(package_url, packages_source_dir, package_filename)
            logger.info(f"    - Downloaded {req}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading '{req}' from {package_url}: {e}")
            logger.info("Please check your internet connection, the package name/version, and the PyPI URL format.")
            return False
        except IOError as e:
            logger.error(f"File system error while downloading '{req}': {e}")
            logger.info("Please check disk space and permissions for the download directory.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while downloading '{req}': {e}")
            logger.exception(*sys.exc_info())
            return False

    logger.success("  - Python packages downloaded.")
    return True

def _compile_python_packages(requirements, build_path, ndk_version, ndk_api, archs):
    """Cross-compile Python packages for Android."""
    logger.info("  - Cross-compiling Python packages (placeholder)...")
    logger.warning("    NOTE: Actual cross-compilation of Python packages is highly complex and not fully implemented.")
    logger.warning("    This step would involve setting up build environments for each package and running their build systems with Android-specific flags.")
    logger.warning("    Manual intervention or a dedicated cross-compilation toolchain for each package might be required.")
    return True

def _bundle_python_packages(requirements, build_path, archs):
    """Bundle compiled Python packages into Android app assets."""
    logger.info("  - Bundling Python packages (placeholder)...")
    logger.warning("    NOTE: This step would involve copying compiled Python packages into the Android project's assets.")
    return True

def _download_system_packages(system_packages, build_path):
    """Download system packages (native libraries)."""
    logger.info("  - Downloading system packages (placeholder)...")
    logger.warning("    NOTE: Actual download of system packages is highly complex and not fully implemented.")
    logger.warning("    This step would involve finding appropriate download URLs for native libraries.")
    return True

def _compile_system_packages(system_packages, build_path, ndk_version, ndk_api, archs):
    """Cross-compile system packages (native libraries)."""
    logger.info("  - Cross-compiling system packages (placeholder)...")
    logger.warning("    NOTE: Actual cross-compilation of native libraries is highly complex and not fully implemented.")
    logger.warning("    This step would involve setting up build environments for each library and running their build systems with Android-specific flags.")
    logger.warning("    Manual intervention or a dedicated cross-compilation toolchain for each library might be required.")
    return True

def _bundle_system_packages(system_packages, build_path, archs):
    """Bundle compiled system packages (native libraries) into Android app jniLibs."""
    logger.info("  - Bundling system packages (placeholder)...")
    logger.warning("    NOTE: This step would involve copying compiled native libraries into the Android project's jniLibs.")
    return True


def build_android(config, verbose):
    """Build the Android application."""
    logger.info("Building Android application...")

    if verbose:
        logger.info(f"Configuration: {config}")

    # Project configs
    project = config.get("project", {})
    project_name = project.get("name", "Unnamed Project")
    main_file = project.get("main_file", "main.py")
    app_version = project.get("version", "1.0")
    target_platforms = project.get("target_platforms", [])
    package_domain = project.get("package_domain", "org.test")
    build_type = project.get("build_type", "debug")
    requirements = project.get("requirements", ["python3"])
    system_packages = project.get("system_packages", [])

    # Android configs
    android_cfg = config.get("android", {})
    archs = android_cfg.get("archs", ["arm64-v8a", "armeabi-v7a"])
    manifest_file = android_cfg.get("manifest_file", "")
    sdk_version = android_cfg.get("sdk_version")
    ndk_version = android_cfg.get("ndk_version")
    min_sdk_version = android_cfg.get("min_sdk_version")
    ndk_api = android_cfg.get("ndk_api")

    # Java configs
    java_cfg = config.get("java", {})
    jdk_version = java_cfg.get("jdk_version")
    gradle_version = java_cfg.get("gradle_version")

    # Python configs
    python_cfg = config.get("python", {})
    python_version = python_cfg.get("python_version")

    # Build path
    build_path = os.path.join(BUILD_DIR, project_name)
    dist_dir = os.path.join(os.getcwd(), "dist")

    # Ensure Android is a target
    if "android" not in target_platforms:
        logger.error(
            "Error: Android is not specified as a target platform in droidbuilder.toml."
        )
        return False

    # Log values safely
    logger.info(f"INSTALL_DIR: {INSTALL_DIR}")
    logger.info(f"SDK version: {sdk_version or 'not set'}")
    logger.info(f"NDK version: {ndk_version or 'not set'}")
    logger.info(f"minSdkVersion: {min_sdk_version or 'not set'}")
    logger.info(f"JDK version: {jdk_version or 'not set'}")
    logger.info(f"Gradle version: {gradle_version or 'not set'}")
    logger.info(f"Python version: {python_version or 'not set'}")

    # Construct NDK path if possible
    ndk_dir_path = (
        os.path.join(INSTALL_DIR, "android-sdk", "ndk", ndk_version)
        if ndk_version
        else None
    )
    logger.info(f"Constructed ndk_dir path: {ndk_dir_path or 'not available'}")

    # TODO: Add actual build steps here
    # Example placeholder
    if not ndk_dir_path or not os.path.exists(ndk_dir_path):
        logger.warning("NDK directory not found, build may fail.")

    # Set up environment for each architecture
    for arch in archs:
        if not _setup_python_build_environment(ndk_version, ndk_api, arch):
            logger.error(f"Failed to set up build environment for {arch}. Aborting.")
            return False
        
        if not _build_python_for_android(python_version, ndk_version, ndk_api, arch, build_path):
            logger.error(f"Failed to build Python for {arch}. Aborting.")
            return False

    # Create Android project structure
    if not _create_android_project(project_name, package_domain, build_path):
        logger.error("Failed to create Android project structure. Aborting.")
        return False

    # Configure the Android project
    if not _configure_android_project(build_path, project_name, package_domain, app_version, sdk_version, min_sdk_version, ndk_api, manifest_file):
        logger.error("Failed to configure Android project. Aborting.")
        return False

    # Copy Python assets
    if not _copy_python_assets(build_path, archs):
        logger.error("Failed to copy Python assets. Aborting.")
        return False

    # Copy user's Python code
    if not _copy_user_python_code(build_path, main_file):
        logger.error("Failed to copy user's Python code. Aborting.")
        return False

    # Download Python packages
    if requirements:
        if not _download_python_packages(requirements, build_path):
            logger.error("Failed to download Python packages. Aborting.")
            return False
        
        # Compile Python packages
        if not _compile_python_packages(requirements, build_path, ndk_version, ndk_api, archs):
            logger.error("Failed to compile Python packages. Aborting.")
            return False
        
        # Bundle Python packages
        if not _bundle_python_packages(requirements, build_path, archs):
            logger.error("Failed to bundle Python packages. Aborting.")
            return False

    # Download system packages
    if system_packages:
        if not _download_system_packages(system_packages, build_path):
            logger.error("Failed to download system packages. Aborting.")
            return False
        
        # Compile system packages
        if not _compile_system_packages(system_packages, build_path, ndk_version, ndk_api, archs):
            logger.error("Failed to compile system packages. Aborting.")
            return False
        
        # Bundle system packages
        if not _bundle_system_packages(system_packages, build_path, archs):
            logger.error("Failed to bundle system packages. Aborting.")
            return False

    logger.info(f"Starting build for {project_name} v{app_version} ({build_type})")

    # Build APK
    logger.info("  - Building Android APK...")
    gradlew_path = os.path.join(build_path, "gradlew")
    if not os.path.exists(gradlew_path):
        logger.error(f"Error: gradlew not found at {gradlew_path}. Android project setup failed.")
        return False
    
    try:
        os.chmod(gradlew_path, 0o755)
    except OSError as e:
        logger.error(f"Error making gradlew executable: {e}")
        logger.info("Please check file permissions for gradlew.")
        return False

    build_task = "assembleDebug"
    if build_type == "release":
        build_task = "assembleRelease"

    gradle_build_cmd = [gradlew_path, build_task]
    logger.info(f"  - Running Gradle build: {' '.join(gradle_build_cmd)}")

    try:
        subprocess.run(gradle_build_cmd, check=True, cwd=build_path, capture_output=True, text=True)
        logger.success("  - Android APK built successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Gradle build failed (Exit Code: {e.returncode}):")
        if e.stdout:
            logger.error(f"Stdout:\n{e.stdout}")
        if e.stderr:
            logger.error(f"Stderr:\n{e.stderr}")
        logger.info("Please review the Gradle output above for specific errors and ensure your Android SDK and NDK are correctly installed and configured.")
        return False
    except (OSError, FileNotFoundError) as e:
        logger.error(f"Error executing Gradle command: {e}")
        logger.info("This might indicate an issue with your Java or Gradle installation, or incorrect permissions.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during Gradle build: {e}")
        logger.info("Please report this issue to the DroidBuilder developers.")
        logger.exception(*sys.exc_info())
        return False

    # Find the generated APK and move it to the dist dir
    os.makedirs(dist_dir, exist_ok=True) # Ensure dist directory exists
    apk_name = f"{project_name}-{build_type}.apk" # Simplified name
    # The actual APK path is usually app/build/outputs/apk/{build_type}/app-{build_type}.apk
    generated_apk_path = os.path.join(build_path, "app", "build", "outputs", "apk", build_type, f"app-{build_type}.apk")
    
    if os.path.exists(generated_apk_path):
        try:
            shutil.move(generated_apk_path, os.path.join(dist_dir, apk_name))
            logger.success(f"Build successful! APK available at {os.path.join(dist_dir, apk_name)}")
            return True
        except (shutil.Error, OSError) as e:
            logger.error(f"Error moving generated APK to dist directory: {e}")
            logger.info("Please check permissions for the dist directory and ensure enough disk space.")
            return False
    else:
        # Try to find any apk
        found_apk = False
        for root, _, files in os.walk(os.path.join(build_path, "app", "build", "outputs", "apk")):
            for f in files:
                if f.endswith(".apk"):
                    try:
                        shutil.move(os.path.join(root, f), os.path.join(dist_dir, f)) # Use original filename if found
                        logger.success(f"Build successful! APK available at {os.path.join(dist_dir, f)}")
                        found_apk = True
                        break
                    except (shutil.Error, OSError) as e:
                        logger.error(f"Error moving found APK to dist directory: {e}")
                        logger.info("Please check permissions for the dist directory and ensure enough disk space.")
                        return False
            if found_apk:
                break
        if not found_apk:
            logger.error("Build failed: Could not find generated APK.")
            return False

    return True
