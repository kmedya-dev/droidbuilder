import os
import sys
import shutil
from . import config
from . import toolchain
from .cli_logger import logger
from .utils import ARCH_MAP, resolve_config_type, patch_resolver, run_shell_command, get_explicit_dependencies, resolve_package
from .tools.installer import install

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")
BUILD_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder", "build")


# build_environment for python_source, runtime_packages, buildtime_packages
def _setup_build_environment(ndk_version, ndk_api, arch, ndk_dir_path, build_path):
    """Set up environment variables for cross-compiling."""
    logger.info(f"  - Setting up build environment for {arch} (NDK {ndk_version}, API {ndk_api})...")

    ndk_root = ndk_dir_path
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

    compiler_prefix = ARCH_MAP[arch][0]
    if not compiler_prefix:
        logger.error(f"Error: Unsupported architecture for Python build: {arch}")
        return False

    cc_path = f"{toolchain_bin}/{compiler_prefix}{ndk_api}-clang"
    cxx_path = f"{toolchain_bin}/{compiler_prefix}{ndk_api}-clang++"
    ar_path = f"{toolchain_bin}/llvm-ar"
    strip_path = f"{toolchain_bin}/llvm-strip"
    as_path = f"{toolchain_bin}/llvm-as"
    ld_path = f"{toolchain_bin}/ld"
    ranlib_path = f"{toolchain_bin}/llvm-ranlib"
    readelf_path = f"{toolchain_bin}/llvm-readelf"
    nm_path = f"{toolchain_bin}/llvm-nm"

    # Initialize cflags and ldflags with base values
    cflags = f"-fPIC -DANDROID -D__ANDROID_API__={ndk_api} -I{sysroot}/usr/include"
    ldflags = f"-L{sysroot}/usr/lib/{compiler_prefix}/{ndk_api} -lm -ldl --sysroot={sysroot}"

    # Prepare environment variables for subprocesses
    env = os.environ.copy()
    env["AR"] = ar_path
    env["AS"] = as_path
    env["CC"] = cc_path
    env["CXX"] = cxx_path
    env["LD"] = ld_path
    env["RANLIB"] = ranlib_path
    env["READELF"] = readelf_path
    env["NM"] = nm_path
    env["STRIP"] = strip_path
    env["sysROOT"] = sysroot
    env["PATH"] = f"{toolchain_bin}:{env['PATH']}"
    env["CFLAGS"] = cflags
    env["LDFLAGS"] = ldflags

    logger.info("  - Build environment set up.")
    return True, toolchain_bin, sysroot, cc_path, cxx_path, ar_path, strip_path, as_path, ld_path, ranlib_path, readelf_path, nm_path, cflags, ldflags, ndk_root, compiler_prefix, env

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


def _build_python_for_android(python_version, package_config, python_host, python_source_dir, ndk_version, ndk_api, arch, build_path, toolchain_bin, sysroot, cc_path, cxx_path, ar_path, strip_path, as_path, ld_path, ranlib_path, readelf_path, nm_path, compiler_prefix, env):
    """Build Python for a specific Android architecture."""
    logger.info(f"  - Building Python {python_version} for {arch}...")

    host = ARCH_MAP[arch][0]
    if not host:
        logger.error(f"Error: Unsupported architecture for Python build: {arch}")
        return False

    install_dir = os.path.join(build_path, "python-install", arch)
    os.makedirs(install_dir, exist_ok=True)

    extra_configure_args = [
        "--disable-ipv6",
        "--without-ensurepip",
        f"--with-build-python={python_host}"
    ]

    commands = resolve_config_type(
        package_name=f"python-{python_version}",
        package_config=package_config,
        package_source_path=python_source_dir,
        arch=arch,
        ndk_api=ndk_api,
        install_dir=install_dir,
        cflags=env["CFLAGS"],
        ldflags=env["LDFLAGS"],
        ar=ar_path,
        as_=as_path,
        cc=cc_path,
        cxx=cxx_path,
        ld=ld_path,
        ranlib=ranlib_path,
        readelf=readelf_path,
        nm=nm_path,
        strip=strip_path,
        ndk_root=ndk_root,
        sysroot=sysroot,
        extra_configure_args=extra_configure_args,
    )

    clean_cmd = commands["clean_command"]
    configure_cmd = commands["configure_command"]
    build_cmd = commands["build_command"]
    install_cmd = commands["install_command"]

    if clean_cmd:
        stdout, stderr, returncode = run_shell_command(clean_cmd, description=f"  - Cleaning Python build for {arch}", env=env, cwd=python_source_dir)
        if returncode != 0:
            logger.warning(f"Clean command failed for Python (Exit Code: {returncode}). Continuing anyway.")

    if configure_cmd:
        stdout, stderr, returncode = run_shell_command(configure_cmd, description=f"  - Running Python configure for {arch}", env=env, cwd=python_source_dir)
        if returncode != 0:
            logger.error(f"Configure failed for Python (Exit Code: {returncode}):")
            if stdout:
                logger.error(f"Stdout:\n{stdout}")
            if stderr:
                logger.error(f"Stderr:\n{stderr}")
            return False

    stdout, stderr, returncode = run_shell_command(build_cmd, description=f"  - Running Python build for {arch}", env=env, cwd=python_source_dir)
    if returncode != 0:
        logger.error(f"Build failed for Python (Exit Code: {returncode}):")
        if stdout:
            logger.error(f"Stdout:\n{stdout}")
        if stderr:
            logger.error(f"Stderr:\n{stderr}")
        return False

    stdout, stderr, returncode = run_shell_command(install_cmd, description=f"  - Running Python install for {arch}", env=env, cwd=python_source_dir)
    if returncode != 0:
        logger.error(f"Install failed for Python (Exit Code: {returncode}):")
        if stdout:
            logger.error(f"Stdout:\n{stdout}")
        if stderr:
            logger.error(f"Stderr:\n{stderr}")
        return False

    logger.success(f"  - Python {python_version} built and installed for {arch}.")
    return True

def _compile_runtime_package(package_name, package_config, runtime_package_source_path, python_install_dir, arch, ndk_version, ndk_api, build_path, ndk_dir_path, config):
    """Compiles and installs a runtime package for a specific Android architecture."""
    logger.info(f"  - Compiling runtime package {package_name} for {arch}...")

    # Apply patches if specified in config
    if not patch_resolver.apply_patches(package_name, runtime_package_source_path, config):
        return False

    # Set up environment for cross-compilation
    success, toolchain_bin, sysroot, cc_path, cxx_path, ar_path, strip_path, as_path, ld_path, ranlib_path, readelf_path, nm_path, cflags, ldflags, ndk_root, compiler_prefix, env = _setup_build_environment(ndk_version, ndk_api, arch, ndk_dir_path, build_path)
    if not success:
        logger.error(f"Failed to set up build environment for {arch} for runtime package {package_name}. Aborting.")
        return False

    # Attempt to install using pip (preferred for runtime packages)
    # Ensure pip is available in the cross-compiled Python environment
    python_bin = os.path.join(python_install_dir, "bin", "python3")
    if not os.path.exists(python_bin):
        logger.error(f"Error: Cross-compiled Python interpreter not found at {python_bin}. Cannot install runtime package {package_name}.")
        return False

    # Create a new environment for pip install to include CFLAGS and LDFLAGS
    pip_env = env.copy() # Use the env returned by _setup_build_environment
    pip_env["CFLAGS"] = cflags
    pip_env["LDFLAGS"] = ldflags

    # Get pip install command from configure_resolver
    # We need to pass a dummy package_config with config_type="pip"
    # The actual package_config for runtime packages is not directly available here,
    # but resolve_config_type only cares about config_type for "pip"
    pip_commands = resolve_config_type(
        package_name=package_name,
        package_config={"config_type": "pip"},
        package_source_path=runtime_package_source_path,
        arch=arch,
        ndk_api=ndk_api,
        install_dir=python_install_dir, # This is the target install dir
        cflags=cflags,
        ldflags=ldflags,
        ar=ar_path,
        cc=cc_path,
        cxx=cxx_path,
        strip=strip_path,
        ndk_root=ndk_root,
        sysroot=sysroot,
    )
    pip_install_cmd = pip_commands["install_command"]

    stdout, stderr, returncode = run_shell_command(pip_install_cmd, description=f"    - Running pip install for {package_name}", env=pip_env, cwd=runtime_package_source_path)
    if returncode != 0:
        logger.error(f"Pip install failed for runtime package {package_name} (Exit Code: {returncode}):")
        if stdout:
            logger.error(f"Stdout:\n{stdout}")
        if stderr:
            logger.error(f"Stderr:\n{stderr}")
        logger.info("Please check the runtime packages and cross-compilation environment.")
        return False

    logger.success(f"    - Successfully compiled and installed {package_name} for {arch}.")
    return True

def _compile_buildtime_package(package_name, package_config, buildtime_package_source_path, arch, ndk_version, ndk_api, build_path, cflags, ldflags, cc_path, cxx_path, ar_path, strip_path, as_path, ld_path, ranlib_path, readelf_path, nm_path, ndk_root, sysroot, env, toolchain_bin, config, extra_configure_args=[]):
    """Compiles and installs a buildtime package for a specific Android architecture."""
    logger.info(f"  - Compiling buildtime package {package_name} for {arch}...")

    # Apply patches if specified in config
    if not patch_resolver.apply_patches(package_name, buildtime_package_source_path, config):
        return False

    commands = resolve_config_type(
        package_name=package_name,
        package_config=package_config,
        package_source_path=buildtime_package_source_path,
        arch=arch,
        ndk_api=ndk_api,
        install_dir=os.path.join(toolchain_bin, f"../sysroot"),
        cflags=cflags,
        ldflags=ldflags,
        ar=ar_path,
        as_=as_path,
        cc=cc_path,
        cxx=cxx_path,
        ld=ld_path,
        ranlib=ranlib_path,
        readelf=readelf_path,
        nm=nm_path,
        strip=strip_path,
        ndk_root=ndk_root,
        sysroot=sysroot,
        extra_configure_args=extra_configure_args,
    )

    clean_cmd = commands["clean_command"]
    configure_cmd = commands["configure_command"]
    build_cmd = commands["build_command"]
    install_cmd = commands["install_command"]

    if clean_cmd:
        stdout, stderr, returncode = run_shell_command(clean_cmd, description=f"  - Cleaning buildtime package {package_name} for {arch}", env=env, cwd=buildtime_package_source_path)
        if returncode != 0:
            logger.warning(f"Clean command failed for {package_name} (Exit Code: {returncode}). Continuing anyway.")
            if stdout:
                logger.warning(f"Stdout:\n{stdout}")
            if stderr:
                logger.warning(f"Stderr:\n{stderr}")

    if configure_cmd:
        stdout, stderr, returncode = run_shell_command(configure_cmd, description=f"  - Running configure for {package_name} on {arch}", env=env, cwd=buildtime_package_source_path)
        if returncode != 0:
            logger.error(f"Configure failed for {package_name} (Exit Code: {returncode}):")
            if stdout:
                logger.info(f"Stdout:\n{stdout}")
            if stderr:
                logger.info(f"Stderr:\n{stderr}")
            return False

    stdout, stderr, returncode = run_shell_command(build_cmd, description=f"  - Running build for {package_name} on {arch}", env=env, cwd=buildtime_package_source_path)
    if returncode != 0:
        logger.error(f"Build failed for {package_name} (Exit Code: {returncode}):")
        if stdout:
            logger.error(f"Stdout:\n{stdout}")
        if stderr:
            logger.error(f"Stderr:\n{stderr}")
        return False

    stdout, stderr, returncode = run_shell_command(install_cmd, description=f"  - Running install for {package_name} on {arch}", env=env, cwd=buildtime_package_source_path)
    if returncode != 0:
        logger.error(f"Install failed for {package_name} (Exit Code: {returncode}):")
        if stdout:
            logger.error(f"Stdout:\n{stdout}")
        if stderr:
            logger.error(f"Stderr:\n{stderr}")
        return False

    logger.success(f"  - Successfully compiled and installed {package_name} for {arch}.")
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

        compiler_prefix_map = {}
        toolchain_bin_map = {}
        sysroot_map = {}
        cc_path_map = {}
        cxx_path_map = {}
        ar_path_map = {}
        strip_path_map = {}
        as_path_map = {}
        ld_path_map = {}
        ranlib_path_map = {}
        readelf_path_map = {}
        nm_path_map = {}
        cflags_map = {}
        ldflags_map = {}
        ndk_root_map = {}
        env_map = {}

        for arch in archs:
            success, toolchain_bin, sysroot, cc_path, cxx_path, ar_path, strip_path, as_path, ld_path, ranlib_path, readelf_path, nm_path, cflags, ldflags, ndk_root, compiler_prefix, env = _setup_build_environment(ndk_version, ndk_api, arch, ndk_dir_path, build_path)
            if not success:
                logger.error(f"Failed to set up build environment for {arch}. Aborting.")
                return False

            toolchain_bin_map[arch] = toolchain_bin
            sysroot_map[arch] = sysroot
            cc_path_map[arch] = cc_path
            cxx_path_map[arch] = cxx_path
            ar_path_map[arch] = ar_path
            strip_path_map[arch] = strip_path
            as_path_map[arch] = as_path
            ld_path_map[arch] = ld_path
            ranlib_path_map[arch] = ranlib_path
            readelf_path_map[arch] = readelf_path
            nm_path_map[arch] = nm_path
            cflags_map[arch] = cflags
            ldflags_map[arch] = ldflags
            ndk_root_map[arch] = ndk_root
            compiler_prefix_map[arch] = compiler_prefix
            env_map[arch] = env

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
                if not _compile_buildtime_package(name, {}, buildtime_package_source_path, arch, ndk_version, ndk_api, build_path, cflags_map[arch], ldflags_map[arch], cc_path_map[arch], cxx_path_map[arch], ar_path_map[arch], strip_path_map[arch], as_path_map[arch], ld_path_map[arch], ranlib_path_map[arch], readelf_path_map[arch], nm_path_map[arch], ndk_root_map[arch], sysroot_map[arch], env_map[arch], toolchain_bin_map[arch], config):
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
            if not _build_python_for_android(python_version, {}, python_host, python_source_dir, ndk_version, ndk_api, arch, build_path, toolchain_bin_map[arch], sysroot_map[arch], cc_path_map[arch], cxx_path_map[arch], ar_path_map[arch], strip_path_map[arch], as_path_map[arch], ld_path_map[arch], ranlib_path_map[arch], readelf_path_map[arch], nm_path_map[arch], compiler_prefix_map[arch], env_map[arch]):
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
                if not _compile_runtime_package(name, {}, runtime_package_source_path, python_install_dir, arch, ndk_version, ndk_api, build_path, ndk_dir_path, config):
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

        # Copy Python and buildtime assets
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
        stdout, stderr, returncode = run_shell_command(gradle_build_cmd, description=f"  - Running Gradle build: {' '.join(gradle_build_cmd)}", cwd=build_path)
        if returncode != 0:
            logger.error(f"Gradle build failed (Exit Code: {returncode}):")
            if stdout:
                logger.error(f"Stdout:\n{stdout}")
            if stderr:
                logger.error(f"Stderr:\n{stderr}")
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
