# DroidBuilder Usage Guide

DroidBuilder is a command-line tool designed to simplify the process of building Android (and other) applications. This guide will walk you through its usage, from initial setup to building your app, both locally and in CI/CD environments.

## 1. Local Development Workflow (Terminal Usage)

This process assumes you have Python 3 and Git installed on your system.

### Step 1: Initial Setup (One-time per project)

First, you need to set up your development environment and install DroidBuilder.

```bash
# 1. Clone your project repository (if you haven't already)
#    Replace <your_project_repo_url> with the actual URL
git clone <your_project_repo_url>
cd <your_project_directory> # Navigate into your project folder

# 2. Create a Python virtual environment to manage dependencies
python -m venv venv

# 3. Activate the virtual environment
#    On Linux/macOS/Termux:
source venv/bin/activate
#    On Windows (Command Prompt):
# venv\Scripts\activate.bat
#    On Windows (PowerShell):
# venv\Scripts\Activate.ps1

# 4. Install DroidBuilder in editable mode within the virtual environment
#    This makes the 'droidbuilder' command available in your terminal
pip install -e .
```

### Step 2: Initialize Your Project (`droidbuilder init`)

This command guides you through setting up your `droidbuilder.toml` configuration file.

```bash
# Ensure your virtual environment is active
source venv/bin/activate # Or your OS-specific activation command

# Run the initialization command
droidbuilder init
```
*   **Action:** The tool will prompt you for various details like Project Name, Version, Main Python File, Target Platforms (e.g., `android,ios,desktop`), Android SDK/NDK versions, Java JDK version, and whether to accept SDK licenses automatically.
*   **Output:** A `droidbuilder.toml` file will be created in your project's root directory, storing your chosen configurations.

### Step 3: Install Development Tools (`droidbuilder install-tools`)

This command downloads and sets up the necessary SDKs, NDKs, and JDKs based on your `droidbuilder.toml` file.

```bash
# Ensure your virtual environment is active
source venv/bin/activate # Or your OS-specific activation command

# Run the tool installation command
droidbuilder install-tools
```
*   **Action:** DroidBuilder will download the specified Android SDK command-line tools, NDK, and JDK. It will extract them into a hidden directory (e.g., `~/.droidbuilder`) and set up necessary environment variables. It will also install `py2jib`. This step requires an active internet connection.
*   **Output:** Progress messages indicating downloads, extractions, and installations.

### Step 4: Build Your Application (`droidbuilder build <platform>`)

Once tools are installed, you can build your application for the desired platform.

```bash
# Ensure your virtual environment is active
source venv/bin/activate # Or your OS-specific activation command

# Build for Android
droidbuilder build android

# Build for iOS (placeholder functionality)
# droidbuilder build ios

# Build for Desktop (placeholder functionality)
# droidbuilder build desktop
```
*   **Action (Android):** DroidBuilder will create a temporary Android project structure, download Gradle (if not cached), and execute Gradle commands to build your application.
*   **Output (Android):** Gradle build logs, indicating the progress and eventual success or failure. If successful, an APK file will be generated in a build output directory (e.g., `~/.droidbuilder_build/YourAppName_android/app/build/outputs/apk/debug/`).

#### Overriding Configuration with Command-Line Arguments

You can override values from `droidbuilder.toml` directly via command-line arguments for the `build` command. This is useful for quick tests or dynamic CI/CD scenarios.

```bash
# Example: Build for Android SDK 33 in release mode
droidbuilder build android --sdk-version 33 --build-type release

# Example: Override NDK and JDK versions
droidbuilder build android --ndk-version 25.2.9519653 --jdk-version 17
```

## 2. CI/CD Automation Workflow (e.g., GitHub Actions)

DroidBuilder is designed to be fully automatable, making it ideal for Continuous Integration (CI) systems. The key is using non-interactive flags and environment variables for sensitive information or dynamic configurations.

Here's an example of a `.github/workflows/android_build.yml` file for GitHub Actions:

```yaml
name: Android CI Build

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest # Or a specific Android/Linux runner if available

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.x' # Use a compatible Python version

    - name: Set up Java (for Android/Gradle)
      uses: actions/setup-java@v4
      with:
        distribution: 'temurin' # Or 'adopt'
        java-version: '11'      # Or the JDK version specified in droidbuilder.toml

    - name: Create and activate virtual environment, install DroidBuilder
      run: |
        python -m venv venv
        source venv/bin/activate
        pip install -e .

    # Option 1: Use a committed droidbuilder.toml (simplest)
    # Ensure droidbuilder.toml is committed to your repository.

    # Option 2: Generate droidbuilder.toml dynamically (for advanced CI)
    # This allows you to control configuration via environment variables or secrets.
    - name: Generate droidbuilder.toml dynamically
      run: |
        python - <<EOF
        import toml, os
        config = {
            "project": {
                "name": os.getenv("PROJECT_NAME", "CIApp"),
                "version": os.getenv("APP_VERSION", "1.0.0"),
                "main_file": "main.py"
            },
            "android": {
                "sdk_version": os.getenv("ANDROID_SDK_VERSION", "34"),
                "ndk_version": os.getenv("ANDROID_NDK_VERSION", "25.2.9519653"),
                "build_type": os.getenv("BUILD_TYPE", "debug"),
                "accept_sdk_license": "non-interactive"
            },
            "java": {
                "jdk_version": os.getenv("JAVA_JDK_VERSION", "11")
            }
        }
        with open("droidbuilder.toml", "w") as f:
            toml.dump(config, f)
        EOF
      env:
        PROJECT_NAME: ${{ github.event.repository.name }}
        APP_VERSION: 1.0.${{ github.run_number }}
        ANDROID_SDK_VERSION: 34 # Example: Can be overridden by workflow input
        ANDROID_NDK_VERSION: 25.2.9519653
        JAVA_JDK_VERSION: 11
        BUILD_TYPE: debug # Example: Can be 'release' based on branch

    - name: Install DroidBuilder tools
      run: |
        source venv/bin/activate
        droidbuilder install-tools

    - name: Build Android Application
      run: |
        source venv/bin/activate
        droidbuilder build android
        # Future: Add --release and signing options here
      # env: # Future: For release builds, use GitHub Secrets for signing credentials
      #   KEYSTORE_FILE: ${{ secrets.ANDROID_KEYSTORE_FILE }}
      #   KEYSTORE_PASS: ${{ secrets.ANDROID_KEYSTORE_PASS }}
      #   KEY_ALIAS: ${{ secrets.ANDROID_KEY_ALIAS }}
      #   KEY_PASS: ${{ secrets.ANDROID_KEY_PASS }}

    - name: Upload APK artifact
      uses: actions/upload-artifact@v4
      with:
        name: android-apk
        path: ~/.droidbuilder_build/${{ github.event.repository.name }}_android/app/build/outputs/apk/debug/*.apk # Adjust path dynamically
```

## 3. Advanced Topics (To be expanded)

*   **Integrating Python Code:** How to bundle your Python application with DroidBuilder.
*   **`py2jib` and `PyJNIus`:** Advanced Python-Java interoperability.
*   **Customizing Builds:** More detailed control over Gradle and platform-specific settings.
*   **Troubleshooting:** Common issues and solutions.
