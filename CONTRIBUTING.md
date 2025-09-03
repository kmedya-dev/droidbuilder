# Contributing to DroidBuilder

We welcome contributions to DroidBuilder! To ensure a smooth and collaborative process, please follow these guidelines.

## How to Contribute

1.  **Fork the repository:** Start by forking the DroidBuilder repository to your GitHub account.
2.  **Clone your fork:** Clone your forked repository to your local machine:
    ```bash
    git clone https://github.com/YOUR_USERNAME/droidbuilder.git
    cd droidbuilder
    ```
3.  **Create a new branch:** Create a new branch for your feature or bug fix:
    ```bash
    git checkout -b feature/your-feature-name
    ```
    or
    ```bash
    git checkout -b bugfix/your-bug-fix-name
    ```
4.  **Make your changes:** Implement your feature or bug fix. Ensure your code adheres to the existing coding style and conventions.
5.  **Write tests:** If you're adding new functionality, please write unit tests to cover your changes. If you're fixing a bug, add a test that reproduces the bug and verifies the fix.
6.  **Run tests:** Before committing, run the test suite to ensure everything is working as expected:
    ```bash
    pytest tests/
    ```
7.  **Commit your changes:** Write clear and concise commit messages. Follow the conventional commits specification if possible.
    ```bash
    git commit -m "feat: Add new feature"
    ```
    or
    ```bash
    git commit -m "fix: Fix a bug"
    ```
8.  **Push to your fork:** Push your changes to your forked repository:
    ```bash
    git push origin feature/your-feature-name
    ```
9.  **Create a Pull Request (PR):** Open a pull request from your branch to the `main` branch of the original DroidBuilder repository. Provide a detailed description of your changes and reference any related issues.

## Code Style

*   Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code.
*   Use [Ruff](https://beta.ruff.rs/docs/) for linting and formatting.

## Reporting Bugs

If you find a bug, please open an issue on the [GitHub Issues](https://github.com/YOUR_USERNAME/droidbuilder/issues) page. Provide a clear and concise description of the bug, steps to reproduce it, and your environment details.

## Feature Requests

If you have an idea for a new feature, please open an issue on the [GitHub Issues](https://github.com/YOUR_USERNAME/droidbuilder/issues) page. Describe your idea, its potential benefits, and any relevant use cases.

Thank you for contributing to DroidBuilder!