import click
import os
import subprocess
import shutil
import sys
from .cli_logger import logger

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
    toolchain_bin = os.path.join(ndk_root, "toolchains", "llvm", "prebuilt", "linux-x86_64", "bin")
    sysroot = os.path.join(toolchain_bin, f"../sysroot") # sysroot is usually relative to toolchain bin

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
    python_install_dir = os.path.join(build_path, "python-install", arch)
    os.makedirs(python_install_dir, exist_ok=True)

    # Get build triplet
    build_triplet = subprocess.check_output(["uname", "-m", "-s"]).decode().strip().replace(" ", "-").lower()

    # Get host triplet
    host_triplet = ARCH_COMPILER_PREFIXES.get(arch)

    if not host_triplet:
        logger.error(f"Error: Could not determine host triplet for architecture: {arch}")
        return False

    # Configure command
    configure_cmd = [
        os.path.join(python_source_dir, "configure"),
        f"--host={host_triplet}",
        f"--build={build_triplet}",
        "--enable-shared",
        "--disable-ipv6",
        "--with-system-ffi=no",
        "--without-ensurepip",
        f"--prefix={python_install_dir}",
        f"CC={os.environ['CC']}",
        f"CXX={os.environ['CXX']}",
        f"AR={os.environ['AR']}",
        f"LD={os.environ['LD']}",
        f"RANLIB={os.environ['RANLIB']}",
        f"STRIP={os.environ['STRIP']}",
        f"SYSROOT={os.environ['SYSROOT']}",
        f"CFLAGS=-fPIC -DANDROID -D__ANDROID_API__={ndk_api}",
        f"LDFLAGS=-L{os.environ['SYSROOT']}/usr/lib/{host_triplet}/{ndk_api}",
    ]

    logger.info(f"  - Running configure: {' '.join(configure_cmd)}")
    try:
        subprocess.run(configure_cmd, check=True, cwd=python_source_dir)
    except subprocess.CalledProcessError as e:
        logger.error(f"Python configure failed: {e}")
        return False

    # Make command
    make_cmd = ["make", "-j", str(os.cpu_count())]
    logger.info(f"  - Running make: {' '.join(make_cmd)}")
    try:
        subprocess.run(make_cmd, check=True, cwd=python_source_dir)
    except subprocess.CalledProcessError as e:
        logger.error(f"Python make failed: {e}")
        return False

    # Make install command
    make_install_cmd = ["make", "install"]
    logger.info(f"  - Running make install: {' '.join(make_install_cmd)}")
    try:
        subprocess.run(make_install_cmd, check=True, cwd=python_source_dir)
    except subprocess.CalledProcessError as e:
        logger.error(f"Python make install failed: {e}")
        return False

    logger.success(f"  - Python {python_version} built and installed for {arch}.")
    return True

def _create_android_project(project_name, package_domain, build_path):
    """Create a basic Android project structure by copying from template."""
    logger.info(f"  - Creating Android project structure for {project_name} from template...")

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "android", "template")
    
    if not os.path.exists(template_path):
        logger.error(f"Error: Android project template not found at {template_path}")
        return False

    try:
        shutil.copytree(template_path, build_path, dirs_exist_ok=True)
    except Exception as e:
        logger.error(f"Error copying Android project template: {e}")
        return False

    logger.success(f"  - Android project structure created at {build_path}.")
    return True

def _configure_android_project(build_path, project_name, package_domain, app_version, sdk_version, min_sdk_version, ndk_api):
    """Configure the copied Android project with actual values."""
    logger.info(f"  - Configuring Android project at {build_path}...")

    # settings.gradle.kts
    settings_gradle_path = os.path.join(build_path, "settings.gradle.kts")
    if os.path.exists(settings_gradle_path):
        with open(settings_gradle_path, "r") as f:
            content = f.read()
        content = content.replace("rootProject.name = \"MyDroidApp\"", f"rootProject.name = \"{project_name}\"")
        with open(settings_gradle_path, "w") as f:
            f.write(content)
        logger.info("    - Configured settings.gradle.kts")

    # app/build.gradle.kts
    app_build_gradle_path = os.path.join(build_path, "app", "build.gradle.kts")
    if os.path.exists(app_build_gradle_path):
        with open(app_build_gradle_path, "r") as f:
            content = f.read()
        
        app_id = f"{package_domain}.{project_name.lower()}"
        content = content.replace("namespace = \"com.example.myapp\"", f"namespace = \"{app_id}\"")
        content = content.replace("applicationId = \"com.example.myapp\"", f"applicationId = \"{app_id}\"")
        content = content.replace("compileSdk = 34", f"compileSdk = {sdk_version}")
        content = content.replace("minSdk = 21", f"minSdk = {min_sdk_version}")
        content = content.replace("targetSdk = 34", f"targetSdk = {sdk_version}") # targetSdk should be same as compileSdk
        content = content.replace("versionName = \"1.0\"", f"versionName = \"{app_version}\"")

        with open(app_build_gradle_path, "w") as f:
            f.write(content)
        logger.info("    - Configured app/build.gradle.kts")

    # app/src/main/AndroidManifest.xml
    manifest_path = os.path.join(build_path, "app", "src", "main", "AndroidManifest.xml")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            content = f.read()
        
        # Replace package name in manifest tag
        content = content.replace("package=\"com.example.myapp\"", f"package=\"{package_domain}.{project_name.lower()}\"")

        with open(manifest_path, "w") as f:
            f.write(content)
        logger.info("    - Configured AndroidManifest.xml")

    # app/src/main/res/values/strings.xml
    strings_xml_path = os.path.join(build_path, "app", "src", "main", "res", "values", "strings.xml")
    if os.path.exists(strings_xml_path):
        with open(strings_xml_path, "r") as f:
            content = f.read()
        content = content.replace("<string name=\"app_name\">MyDroidApp</string>", f"<string name=\"app_name\">{project_name}</string>")
        with open(strings_xml_path, "w") as f:
            f.write(content)
        logger.info("    - Configured strings.xml")

    logger.success("  - Android project configured.")
    return True

def _copy_python_assets(build_path, archs):
    """Copy compiled Python interpreter and modules to Android project assets."""
    logger.info("  - Copying Python assets to Android project...")

    assets_dir = os.path.join(build_path, "app", "src", "main", "assets")
    os.makedirs(assets_dir, exist_ok=True)

    for arch in archs:
        python_install_dir = os.path.join(build_path, "python-install", arch)
        dest_dir = os.path.join(assets_dir, "python", arch)
        
        if not os.path.exists(python_install_dir):
            logger.error(f"Error: Compiled Python for {arch} not found at {python_install_dir}")
            return False

        try:
            shutil.copytree(python_install_dir, dest_dir, dirs_exist_ok=True)
            logger.info(f"    - Copied Python assets for {arch} to {dest_dir}")
        except Exception as e:
            logger.error(f"Error copying Python assets for {arch}: {e}")
            return False

    logger.success("  - Python assets copied.")
    return True

def _copy_user_python_code(build_path, main_file):
    """Copy user's Python application code to Android project assets."""
    logger.info("  - Copying user's Python code to Android project...")

    user_python_assets_dir = os.path.join(build_path, "app", "src", "main", "assets", "user_python")
    os.makedirs(user_python_assets_dir, exist_ok=True)

    source_main_file_path = os.path.join(os.getcwd(), main_file)
    dest_main_file_path = os.path.join(user_python_assets_dir, os.path.basename(main_file))

    if not os.path.exists(source_main_file_path):
        logger.error(f"Error: Main Python file not found at {source_main_file_path}")
        return False

    try:
        shutil.copyfile(source_main_file_path, dest_main_file_path)
        logger.success(f"  - Copied user's main Python file to {dest_main_file_path}")
    except Exception as e:
        logger.error(f"Error copying user's main Python file: {e}")
        return False

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
    if not _configure_android_project(build_path, project_name, package_domain, app_version, sdk_version, min_sdk_version, ndk_api):
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

    logger.info(f"Starting build for {project_name} v{app_version} ({build_type})")

    build_path = os.path.join(BUILD_DIR, project_name)
    dist_dir = os.path.join(os.getcwd(), "dist")

    # Build APK
    logger.info("  - Building Android APK...")
    gradlew_path = os.path.join(build_path, "gradlew")
    if not os.path.exists(gradlew_path):
        logger.error(f"Error: gradlew not found at {gradlew_path}. Android project setup failed.")
        return False
    
    # Make gradlew executable
    os.chmod(gradlew_path, 0o755)

    build_task = "assembleDebug"
    if build_type == "release":
        build_task = "assembleRelease"

    gradle_build_cmd = [gradlew_path, build_task]
    logger.info(f"  - Running Gradle build: {' '.join(gradle_build_cmd)}")

    try:
        subprocess.run(gradle_build_cmd, check=True, cwd=build_path)
        logger.success("  - Android APK built successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Gradle build failed: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during Gradle build: {e}")
        return False

    # Find the generated APK and move it to the dist dir
    apk_name = f"{project_name}-{build_type}.apk" # Simplified name
    # The actual APK path is usually app/build/outputs/apk/{build_type}/app-{build_type}.apk
    generated_apk_path = os.path.join(build_path, "app", "build", "outputs", "apk", build_type, f"app-{build_type}.apk")
    
    if os.path.exists(generated_apk_path):
        shutil.move(generated_apk_path, dist_dir)
        logger.success(f"Build successful! APK available at {os.path.join(dist_dir, apk_name)}")
    else:
        # Try to find any apk
        found_apk = False
        for root, _, files in os.walk(os.path.join(build_path, "app", "build", "outputs", "apk")):
            for f in files:
                if f.endswith(".apk"):
                    shutil.move(os.path.join(root, f), dist_dir)
                    logger.success(f"Build successful! APK available at {os.path.join(root, f)}")
                    found_apk = True
                    break
            if found_apk:
                break
        if not found_apk:
            logger.error("Build failed: Could not find generated APK.")
            return False

    return True
