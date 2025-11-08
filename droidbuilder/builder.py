import os
import sys
import shutil
from . import config
from . import toolchain
from .cli_logger import logger
from .utils import ARCH_MAP, BuildEnvironment, resolve_config_type, patch_resolver, run_shell_command, get_explicit_dependencies, resolve_package
from .tools.installer import install

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")
BUILD_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder", "build")


def _disable_unnecessary_python_modules(python_source_dir):
    """Disables unnecessary Python modules to reduce final binary size."""
    logger.info("  - Disabling unnecessary Python modules...")
    setup_local_path = os.path.join(python_source_dir, "Modules", "Setup.local")
    
    # Modules to keep enabled: _ssl, _sqlite3, _ctypes, zlib
    disabled_modules = [
        # Already disabled
        "grp",
        "_lzma",
        "readline",
        
        # GUI
        "_tkinter",
        
        # Database
        "_gdbm",
        "_dbm",
        
        # Other
        "_posixshmem",
        "_posixsubprocess",
        "nis",
        "ossaudiodev",
        "spwd",
        "syslog",
        "winreg",
        "winsound",
        "_uuid",
    ]
    
    try:
        os.makedirs(os.path.dirname(setup_local_path), exist_ok=True)
        with open(setup_local_path, "w") as f:
            f.write("*disabled*\n")
            for module in disabled_modules:
                f.write(f"{module}\n")
        logger.success("  - Unnecessary Python modules disabled.")
        return True
    except IOError as e:
        logger.error(f"Error writing to {setup_local_path}: {e}")
        return False


def _build_python_for_android(python_version, package_config, python_host, python_source_dir, env_obj):
    """Build Python for a specific Android architecture."""
    logger.info(f"  - Building Python {python_version} for {env_obj.arch}...")

    install_dir = os.path.join(env_obj.build_path, "python-install", env_obj.arch)
    os.makedirs(install_dir, exist_ok=True)

    libdir_relative = os.path.join(install_dir, "lib")

    # Create config.site file for cross-compilation
    config_site_path = os.path.join(python_source_dir, "config.site")
    with open(config_site_path, "w") as f:
        f.write("ac_cv_file__dev_ptmx=yes\n")
        f.write("ac_cv_file__dev_ptc=no\n")

    # Set CONFIG_SITE environment variable to point to our config.site file
    env_obj.env["CONFIG_SITE"] = config_site_path

    extra_configure_args = [
        "--disable-ipv6",
        "--without-ensurepip",
        "--with-lto",
        f"--with-openssl={env_obj.sysroot}/usr"
        f"--with-build-python={python_host}"
    ]

    commands = resolve_config_type(
        package_name=f"python-{python_version}",
        package_config=package_config,
        package_source_path=python_source_dir,
        arch=env_obj.arch,
        ndk_api=env_obj.ndk_api,
        install_dir=install_dir,
        libdir_relative=libdir_relative,
        cflags=env_obj.cflags,
        ldflags=env_obj.ldflags,
        ar=env_obj.ar_path,
        as_=env_obj.as_path,
        cc=env_obj.cc_path,
        cxx=env_obj.cxx_path,
        ld=env_obj.ld_path,
        ranlib=env_obj.ranlib_path,
        readelf=env_obj.readelf_path,
        nm=env_obj.nm_path,
        strip=env_obj.strip_path,
        ndk_root=env_obj.ndk_root,
        sysroot=env_obj.sysroot,
        pkg_config=env_obj.pkg_config_path,
        extra_configure_args=extra_configure_args,
    )

    clean_cmd = commands["clean_command"]
    configure_cmd = commands["configure_command"]
    build_cmd = commands["build_command"]
    install_cmd = commands["install_command"]

    if clean_cmd:
        result = run_shell_command(clean_cmd, description=f"  - Cleaning Python build for {env_obj.arch}", env=env_obj.env, cwd=python_source_dir)
        if result["returncode"] != 0:
            logger.warning(f"Clean command failed for Python (Exit Code: {result['returncode']}). Continuing anyway.")

    if configure_cmd:
        result = run_shell_command(configure_cmd, description=f"  - Running Python configure for {env_obj.arch}", env=env_obj.env, cwd=python_source_dir)
        if result["returncode"] != 0:
            logger.error(f"Configure failed for Python (Exit Code: {result['returncode']}):")
            if result["stdout"]:
                logger.error(f"Stdout:\n{result['stdout']}")
            if result["stderr"]:
                logger.error(f"Stderr:\n{result['stderr']}")
            return False

    result = run_shell_command(build_cmd, description=f"  - Running Python build for {env_obj.arch}", env=env_obj.env, cwd=python_source_dir)
    if result["returncode"] != 0:
        logger.error(f"Build failed for Python (Exit Code: {result['returncode']}):")
        if result["stdout"]:
            logger.error(f"Stdout:\n{result['stdout']}")
        if result["stderr"]:
            logger.error(f"Stderr:\n{result['stderr']}")
        return False

    result = run_shell_command(install_cmd, description=f"  - Running Python install for {env_obj.arch}", env=env_obj.env, cwd=python_source_dir)
    if result["returncode"] != 0:
        logger.error(f"Install failed for Python (Exit Code: {result['returncode']}):")
        if result["stdout"]:
            logger.error(f"Stdout:\n{result['stdout']}")
        if result["stderr"]:
            logger.error(f"Stderr:\n{result['stderr']}")
        return False

    logger.success(f"  - Python {python_version} built and installed for {env_obj.arch}.")
    return True

def _compile_runtime_package(package_name, package_config, runtime_package_source_path, python_install_dir, env_obj, config):
    """Compiles and installs a runtime package for a specific Android architecture."""
    logger.info(f"  - Compiling runtime package {package_name} for {env_obj.arch}...")

    # Apply patches if specified in config
    if not patch_resolver.apply_patches(package_name, runtime_package_source_path, config):
        return False

    # Set up environment for cross-compilation
    # Attempt to install using pip (preferred for runtime packages)
    # Ensure pip is available in the cross-compiled Python environment
    python_bin = os.path.join(python_install_dir, "bin", "python3")
    if not os.path.exists(python_bin):
        logger.error(f"Error: Cross-compiled Python interpreter not found at {python_bin}. Cannot install runtime package {package_name}.")
        return False

    # Create a new environment for pip install to include CFLAGS and LDFLAGS
    pip_env = env_obj.env.copy() # Use the env returned by _setup_build_environment
    pip_env["CFLAGS"] = env_obj.cflags
    pip_env["LDFLAGS"] = env_obj.ldflags

    # Get pip install command from configure_resolver
    # We need to pass a dummy package_config with config_type="pip"
    # The actual package_config for runtime packages is not directly available here,
    # but resolve_config_type only cares about config_type for "pip"
    pip_commands = resolve_config_type(
        package_name=package_name,
        package_config={"config_type": "pip"},
        package_source_path=runtime_package_source_path,
        arch=env_obj.arch,
        ndk_api=env_obj.ndk_api,
        install_dir=python_install_dir, # This is the target install dir
        libdir_relative=None,
        cflags=env_obj.cflags,
        ldflags=env_obj.ldflags,
        ar=env_obj.ar_path,
        cc=env_obj.cc_path,
        cxx=env_obj.cxx_path,
        strip=env_obj.strip_path,
        ndk_root=env_obj.ndk_root,
        sysroot=env_obj.sysroot,
        pkg_config=env_obj.pkg_config_path,
    )
    pip_install_cmd = pip_commands["install_command"]

    result = run_shell_command(pip_install_cmd, description=f"    - Running pip install for {package_name}", env=pip_env, cwd=runtime_package_source_path)
    if result["returncode"] != 0:
        logger.error(f"Pip install failed for runtime package {package_name} (Exit Code: {result['returncode']}):")
        if result["stdout"]:
            logger.error(f"Stdout:\n{result['stdout']}")
        if result["stderr"]:
            logger.error(f"Stderr:\n{result['stderr']}")
        logger.info("Please check the runtime packages and cross-compilation environment.")
        return False

    logger.success(f"    - Successfully compiled and installed {package_name} for {env_obj.arch}.")
    return True

def _compile_buildtime_package(package_name, package_config, buildtime_package_source_path, env_obj, config, extra_configure_args=[]):
    """Compiles and installs a buildtime package for a specific Android architecture."""
    logger.info(f"  - Compiling buildtime package {package_name} for {env_obj.arch}...")

    # Apply patches if specified in config
    if not patch_resolver.apply_patches(package_name, buildtime_package_source_path, config):
        return False

    # as runtime_packages & python_source's c_types modules, (not needed to bundled as jnilibs)
    install_dir = os.path.join(env_obj.sysroot, "usr")
    libdir_relative =  os.path.join(install_dir, "lib", ARCH_MAP[env_obj.arch][4], env_obj.ndk_api)

    commands = resolve_config_type(
        package_name=package_name,
        package_config=package_config,
        package_source_path=buildtime_package_source_path,
        arch=env_obj.arch,
        ndk_api=env_obj.ndk_api,
        install_dir=install_dir,
        libdir_relative=libdir_relative,
        cflags=env_obj.cflags,
        ldflags=env_obj.ldflags,
        ar=env_obj.ar_path,
        as_=env_obj.as_path,
        cc=env_obj.cc_path,
        cxx=env_obj.cxx_path,
        ld=env_obj.ld_path,
        ranlib=env_obj.ranlib_path,
        readelf=env_obj.readelf_path,
        nm=env_obj.nm_path,
        strip=env_obj.strip_path,
        ndk_root=env_obj.ndk_root,
        sysroot=env_obj.sysroot,
        pkg_config=env_obj.pkg_config_path,
        extra_configure_args=extra_configure_args,
    )

    clean_cmd = commands["clean_command"]
    configure_cmd = commands["configure_command"]
    build_cmd = commands["build_command"]
    install_cmd = commands["install_command"]

    if clean_cmd:
        result = run_shell_command(clean_cmd, description=f"  - Cleaning buildtime package {package_name} for {env_obj.arch}", env=env_obj.env, cwd=buildtime_package_source_path)
        if result["returncode"] != 0:
            logger.warning(f"Clean command failed for {package_name} (Exit Code: {result['returncode']}). Continuing anyway.")
            if result["stdout"]:
                logger.warning(f"Stdout:\n{result['stdout']}")
            if result["stderr"]:
                logger.warning(f"Stderr:\n{result['stderr']}")

    if configure_cmd:
        result = run_shell_command(configure_cmd, description=f"  - Running configure for {package_name} on {env_obj.arch}", env=env_obj.env, cwd=buildtime_package_source_path)
        if result["returncode"] != 0:
            logger.error(f"Configure failed for {package_name} (Exit Code: {result['returncode']}):")
            if result["stdout"]:
                logger.error(f"Stdout:\n{result['stdout']}")
            if result["stderr"]:
                logger.error(f"Stderr:\n{result['stderr']}")
            return False

    result = run_shell_command(build_cmd, description=f"  - Running build for {package_name} on {env_obj.arch}", env=env_obj.env, cwd=buildtime_package_source_path)
    if result["returncode"] != 0:
        logger.error(f"Build failed for {package_name} (Exit Code: {result['returncode']}):")
        if result["stdout"]:
            logger.error(f"Stdout:\n{result['stdout']}")
        if result["stderr"]:
            logger.error(f"Stderr:\n{result['stderr']}")
        return False

    result = run_shell_command(install_cmd, description=f"  - Running install for {package_name} on {env_obj.arch}", env=env_obj.env, cwd=buildtime_package_source_path)
    if result["returncode"] != 0:
        logger.error(f"Install failed for {package_name} (Exit Code: {result['returncode']}):")
        if result["stdout"]:
            logger.error(f"Stdout:\n{result['stdout']}")
        if result["stderr"]:
            logger.error(f"Stderr:\n{result['stderr']}")
        return False

    logger.success(f"  - Successfully compiled and installed {package_name} for {env_obj.arch}.")
    return True

def _create_android_app(app_name, package_domain, build_path):
    """Create a basic Android app structure by copying from template."""
    logger.info(f"  - Creating Android app structure for {app_name} from template...")

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target", "android")
    
    if not os.path.exists(template_path):
        logger.error(f"Error: Android app template not found at {template_path}")
        return False

    try:
        shutil.copytree(template_path, build_path, dirs_exist_ok=True)
    except (shutil.Error, OSError) as e:
        logger.error(f"Error copying Android app template: {e}")
        logger.info("Please check file permissions and ensure the template directory is accessible.")
        return False

    logger.success(f"  - Android app structure created at {build_path}.")
    return True

def _configure_android_app(build_path, app_name, package_domain, app_version, sdk_version, min_sdk_version, ndk_api, manifest_file, python_version):
    """Configure the copied Android app with actual values."""
    logger.info(f"  - Configuring Android app at {build_path}...")

    files_to_configure = {
        "settings.gradle.kts": {
            "path": os.path.join(build_path, "settings.gradle.kts"),
            "replacements": [
                ("rootProject.name = \"MyDroidApp\"", f"rootProject.name = \"{app_name}\""),
            ]
        },
        "app/build.gradle.kts": {
            "path": os.path.join(build_path, "app", "build.gradle.kts"),
            "replacements": [
                ("namespace = \"com.example.myapp\"", f"namespace = \"{package_domain}.{app_name.lower()}\""),
                ("applicationId = \"com.example.myapp\"", f"applicationId = \"{package_domain}.{app_name.lower()}\""),
                ("compileSdk = 34", f"compileSdk = {sdk_version}"),
                ("minSdk = 21", f"minSdk = {min_sdk_version}"),
                ("targetSdk = 34", f"targetSdk = {sdk_version}"),
                ("versionName = \"1.0\"", f"versionName = \"{app_version}\""),
                ("cppFlags += \"\"", f'arguments.add("-DPYTHON_VERSION={python_version}")'),
            ]
        },
        "app/src/main/AndroidManifest.xml": {
            "path": os.path.join(build_path, "app", "src", "main", "AndroidManifest.xml"),
            "replacements": [
                ("package=\"com.example.myapp\"", f"package=\"{package_domain}.{app_name.lower()}\""),
            ]
        },
        "app/src/main/res/values/strings.xml": {
            "path": os.path.join(build_path, "app", "src", "main", "res", "values", "strings.xml"),
            "replacements": [
                ("<string name=\"app_name\">MyDroidApp</string>", f"<string name=\"app_name\">{app_name}</string>"),
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

    logger.success("  - Android app configured.")
    return True


def _copy_assets_to_android_app(build_path, archs):
    """Copy compiled Python interpreter, modules, and buildtime libraries to Android app assets/jniLibs."""
    logger.info("  - Copying Python and buildtime assets to Android app...")

    assets_dir = os.path.join(build_path, "app", "src", "main", "assets")
    jni_libs_dir = os.path.join(build_path, "app", "src", "main", "jniLibs")
    try:
        os.makedirs(assets_dir, exist_ok=True)
        os.makedirs(jni_libs_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating assets/jniLibs directory: {e}")
        return False

    for arch in archs:
        # Copy Python assets
        python_install_dir = os.path.join(build_path, "python-install", arch)
        dest_python_dir = os.path.join(assets_dir, "python", arch)
        
        if not os.path.exists(python_install_dir):
            logger.error(f"Error: Compiled Python for {arch} not found at {python_install_dir}. Please ensure Python was built successfully for this architecture.")
            return False

        try:
            shutil.copytree(python_install_dir, dest_python_dir, dirs_exist_ok=True)
            logger.info(f"    - Copied Python assets for {arch} to {dest_python_dir}")
        except (shutil.Error, OSError) as e:
            logger.error(f"Error copying Python assets for {arch} from {python_install_dir} to {dest_python_dir}: {e}")
            logger.info("Please check directory permissions and ensure enough disk space is available.")
            return False

def _copy_user_python_code(build_path, main_file):
    """Copy user's Python application code to Android app assets."""
    logger.info("  - Copying user's Python code to Android app...")

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

def build_android(config, verbose):
    """Build the Android application."""
    logger.info("Building Android application...")

    app_name = config.get("app", {}).get("name", "MyAwesomeApp")
    package_domain = config.get("app", {}).get("package_domain", "org.test")
    app_version = config.get("app", {}).get("version", "0.1")
    main_file = config.get("app", {}).get("main_file", "main.py")
    target_platforms = config.get("app", {}).get("target_platforms", [])
    
    sdk_version = config.get("android", {}).get("sdk_version", "36")
    ndk_version = config.get("android", {}).get("ndk_version", "28.2.13676358")
    min_sdk_version = config.get("android", {}).get("min_sdk_version", "24")
    ndk_api = config.get("android", {}).get("ndk_api", "24")
    archs = config.get("android", {}).get("archs", ["arm64-v8a", "armeabi-v7a"])
    manifest_file = config.get("android", {}).get("manifest_file", "")
    
    python_version = config.get("python", {}).get("python_version", "3.12.1")
    python_host = sys.executable

    build_type = config.get("build", {}).get("type", "debug")

    used_apt_fallback = False
    if verbose:
        logger.info(f"Configuration: {config}")

    runtime_packages, buildtime_packages, dependency_mapping = get_explicit_dependencies(config)

    # Build path
    build_path = os.path.join(BUILD_DIR, app_name)
    dist_dir = os.path.join(os.getcwd(), "dist")

    temp_bin_dir = os.path.join(INSTALL_DIR, "bin")

    try:
        # Ensure Android is a target
        if "android" not in target_platforms:
            logger.error(
                "Error: Android is not specified as a target platform in droidbuilder.toml."
            )
            return False

        # Construct NDK path if possible
        ndk_dir_path = (
            os.path.join(INSTALL_DIR, "android-sdk", "ndk", ndk_version)
            if ndk_version
            else None
        )
        logger.info(f"Constructed ndk_dir path: {ndk_dir_path or 'not available'}")

        if not ndk_dir_path or not os.path.exists(ndk_dir_path):
            logger.warning("NDK directory not found, build may fail.")

        env_map = {}
        for arch in archs:
            try:
                env_map[arch] = BuildEnvironment(ndk_version, ndk_api, arch, ndk_dir_path, build_path)
            except (FileNotFoundError, ValueError) as e:
                logger.error(f"Failed to set up build environment for {arch}: {e}")
                return False

        for package_name, package_version in buildtime_packages:
            name, url, resolved_version = resolve_package(package_name, package_version, dependency_mapping)
            if not url:
                logger.error(f"Could not resolve buildtime package {name}. Aborting.")
                return False

            buildtime_package_source_dir = os.path.join(INSTALL_DIR, "buildtime_packages_src", f"{name}-{resolved_version or ''}")
            buildtime_package_source_path = install(url, buildtime_package_source_dir, f"{name}-{resolved_version or ''}", verbose=verbose)
            if not buildtime_package_source_path:
                logger.error(f"Failed to download buildtime package {name}. Aborting.")
                return False
                
            for arch in archs:
                if not _compile_buildtime_package(name, {}, buildtime_package_source_path, env_map[arch], config):
                    logger.error(f"Failed to compile buildtime package {name} for {arch}. Aborting.")
                    return False

        python_url = f"https://www.python.org/ftp/python/{python_version}/Python-{python_version}.tgz"
        source_dir = os.path.join(INSTALL_DIR, "python-source", f"Python-{python_version}")
        if python_version:
            python_source_dir = install(python_url, source_dir, f"Python-{python_version}", verbose=verbose)
            if not python_source_dir:
                logger.error("Failed to download Python source. Aborting.")
                return False
        else:
            logger.error("Python version not specified in droidbuilder.toml. Aborting.")
            return False

        # Disable unnecessary Python modules
        if not _disable_unnecessary_python_modules(python_source_dir):
            logger.warning("Could not disable unnecessary Python modules. Continuing with the build...")

        # Set up environment for each architecture and build Python
        for arch in archs:
            if not _build_python_for_android(python_version, {}, python_host, python_source_dir, env_map[arch]):
                logger.error(f"Failed to build Python for {arch}. Aborting.")
                return False

        for package_name, package_version in runtime_packages:
            name, url, resolved_version = resolve_package(package_name, package_version, dependency_mapping)
            if not url:
                logger.error(f"Could not resolve runtime package {name}. Aborting.")
                return False

            runtime_package_source_dir = os.path.join(INSTALL_DIR, "runtime_packages_src", f"{name}-{resolved_version or ''}")
            runtime_package_source_path = install(url, runtime_package_source_dir, f"{name}-{resolved_version or ''}", verbose=verbose)
            if not runtime_package_source_path:
                logger.error(f"Failed to download runtime package {name}. Aborting.")
                return False
        
            for arch in archs:
                python_install_dir = os.path.join(build_path, "python-install", arch)
                if not _compile_runtime_package(name, {}, runtime_package_source_path, python_install_dir, env_map[arch], config):
                    logger.error(f"Failed to compile runtime package {name} for {arch}. Aborting.")
                    return False

        # Create Android app structure
        if not _create_android_app(app_name, package_domain, build_path):
            logger.error("Failed to create Android app structure. Aborting.")
            return False

        # Configure the Android app
        if not _configure_android_app(build_path, app_name, package_domain, app_version, sdk_version, min_sdk_version, ndk_api, manifest_file, python_version):
            logger.error("Failed to configure Android app. Aborting.")
            return False

        # Copy Python assets
        if not _copy_assets_to_android_app(build_path, archs):
            logger.error("Failed to copy assets to Android app. Aborting.")
            return False

        # Copy user's Python code
        if not _copy_user_python_code(build_path, main_file):
            logger.error("Failed to copy user's Python code. Aborting.")
            return False

        logger.info(f"Starting build for {app_name} v{app_version} ({build_type})")

        # Build APK
        logger.info("  - Building Android APK...")
        gradlew_path = os.path.join(build_path, "gradlew")
        if not os.path.exists(gradlew_path):
            logger.error(f"Error: gradlew not found at {gradlew_path}. Android app setup failed.")
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
        result = run_shell_command(gradle_build_cmd, description=f"  - Running Gradle build: {' '.join(gradle_build_cmd)}", cwd=build_path)
        if result["returncode"] != 0:
            logger.error(f"Gradle build failed (Exit Code: {result['returncode']}):")
            if result["stdout"]:
                logger.error(f"Stdout:\n{result['stdout']}")
            if result["stderr"]:
                logger.error(f"Stderr:\n{result['stderr']}")
            logger.info("Please review the Gradle output above for specific errors and ensure your Android SDK and NDK are correctly installed and configured.")
            return False

        # Find the generated APK and move it to the dist dir
        os.makedirs(dist_dir, exist_ok=True) # Ensure dist directory exists
        apk_name = f"{app_name}-{build_type}.apk" # Simplified name
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
                            if used_apt_fallback:
                                logger.warning("⚠️ Some dependencies were installed from host packages instead of cross-compiled sources. APK may crash at runtime due to ABI mismatch")
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
    finally:
        if os.path.exists(temp_bin_dir):
            try:
                shutil.rmtree(temp_bin_dir)
                logger.info(f"Cleaned up temporary directory: {temp_bin_dir}")
            except OSError as e:
                logger.warning(f"Could not clean up temporary directory {temp_bin_dir}: {e}")
