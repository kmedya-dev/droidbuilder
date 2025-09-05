import os
import unittest
from click.testing import CliRunner
from droidbuilder.main import cli
from unittest.mock import patch, MagicMock

class TestInitCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch('click.prompt')
    @patch('click.confirm')
    def test_init_command(self, mock_confirm, mock_prompt):
        # Define the answers for each prompt
        mock_prompt.side_effect = [
            "MyTestApp",  # Project Name
            "1.0",        # Project Version
            "main.py",    # Main Python File
            "android",    # Target Platforms
            "org.test",   # Package Domain
            "debug",      # Build Type
            "arm64-v8a",  # Target Architectures
            "",           # Path to custom AndroidManifest.xml
            "",           # Path to custom intent_filters.xml
            "9123335",    # Android Command Line Tools Tag
            "py2jib",     # Python Requirements
            "34",         # Android SDK Version
            "21",         # Android Minimum SDK Version
            "24",         # Android NDK API
            "25.2.9519653", # Android NDK Version
            "11",         # Java JDK Version
            "8.7",        # Java Gradle Version
            "3.9.13",     # Python Version for cross-compilation
            "interactive",# Accept SDK licenses automatically?
            "openssl,sdl2"# System Packages
        ]
        mock_confirm.return_value = True # For any click.confirm calls

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['init'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(os.path.exists('droidbuilder.toml'))

            # Verify system_packages are in droidbuilder.toml
            with open('droidbuilder.toml', 'r') as f:
                content = f.read()
                self.assertIn('system_packages = [ "openssl", "sdl2",]', content)

if __name__ == '__main__':
    unittest.main()