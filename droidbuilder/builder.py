import click
import os
import subprocess
import shutil
import sys
from .cli_logger import logger

INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder")
BUILD_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder_build")


def build_android(config, verbose):
    """Build the Android application."""
    logger.info("Building Android application...")

    if verbose:
        logger.info(f"Configuration: {conf}")

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

    logger.info(f"Starting build for {project_name} v{app_version} ({build_type})")

    return True
