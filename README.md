# DroidBuilder

A user-friendly, cross-platform command-line tool designed to simplify the process of building Android apps while also supporting app development for other platforms (e.g., iOS, Linux, Windows).

## Features

*   **Interactive Setup**: Guides users through initial project configuration.
*   **Automated Tool Installation**: Installs Android SDK, NDK, JDK, and integrates `py2jib`.
*   **Cross-Platform Builds**: Supports building for Android, iOS, and Desktop (with planned expansion).
*   **CI/CD Friendly**: Designed for automation in Continuous Integration environments.
*   **User Control**: Dynamic configuration via `droidbuilder.toml` for full control over versions and settings.

## Getting Started

### Installation

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <repository_url>
    cd droidbuilder
    ```
2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  **Install DroidBuilder in editable mode:**
    ```bash
    pip install -e .
    ```

### Basic Usage

1.  **Initialize your project:**
    Navigate to your project directory and run:
    ```bash
    droidbuilder init
    ```
    This command will guide you through an interactive setup to create a `droidbuilder.toml` configuration file.

2.  **Install development tools:**
    After initialization, install the necessary SDKs, NDKs, and JDKs:
    ```bash
    droidbuilder install-tools
    ```
    For CI/CD environments, use the `--ci` flag to accept licenses automatically:
    ```bash
    droidbuilder install-tools --ci
    ```

3.  **Build your application:**
    Build your application for a target platform (e.g., `android`):
    ```bash
    droidbuilder build android
    ```
    Supported platforms include `android`, `ios`, and `desktop`.

## Commands Reference

*   `droidbuilder init`
    *   Initializes a new DroidBuilder project and creates `droidbuilder.toml`.
    *   Prompts for project name, version, main file, target platforms, SDK/NDK/JDK versions.

*   `droidbuilder install-tools [--ci]`
    *   Installs Android SDK, NDK, JDK, and `py2jib` based on `droidbuilder.toml`.
    *   `--ci`: Runs in CI mode, automatically accepting licenses.

*   `droidbuilder build <platform>`
    *   Builds the application for the specified platform.
    *   `<platform>`: `android`, `ios`, or `desktop`.

*   `droidbuilder list-installed`
    *   Lists all installed droids (SDK, NDK, JDK versions).

*   `droidbuilder uninstall <tool_name>`
    *   Uninstalls a specified tool (e.g., `jdk-11`).

*   `droidbuilder update <tool_name>`
    *   Updates a specified tool to the latest version (e.g., `jdk`).

*   `droidbuilder search <tool_name>`
    *   Searches for available versions of a specified tool (e.g., `jdk`).

*   `droidbuilder doctor`
    *   Checks if all required tools are installed and the environment is set up correctly.

*   `droidbuilder config`
    *   View or edit the `droidbuilder.toml` configuration file.
    *   `view`: View the contents of the `droidbuilder.toml` file.
    *   `edit`: Edit the `droidbuilder.toml` file in your default editor.

*   `droidbuilder version`
    *   Prints the version of the DroidBuilder tool.

*   `droidbuilder log`
    *   Displays the latest log file.

## Configuration (`droidbuilder.toml`)

The `droidbuilder.toml` file stores your project's configuration. An example structure:

```toml
[project]
name = "MyAwesomeApp"
version = "1.0.0"
main_file = "app.py"
target_platforms = ["android", "ios"]

[android]
sdk_version = "34"
ndk_version = "25.2.9519653"

[java]
jdk_version = "11"
```

## Contributing

Contributions are welcome! Please refer to the contribution guidelines (to be added).
