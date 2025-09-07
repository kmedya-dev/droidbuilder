import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.commands.uninstall import uninstall
from droidbuilder.main import cli # Import cli to invoke the command
from click.testing import CliRunner

class TestUninstallCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    @patch('droidbuilder.commands.uninstall.logger')
    @patch('droidbuilder.installer.list_installed_tools')
    @patch('droidbuilder.installer.uninstall_tool')
    def test_uninstall_all_success(self, mock_uninstall_tool, mock_list_installed_tools, mock_logger):
        # Mock installed tools
        mock_list_installed_tools.return_value = {
            "android_sdk": ["34"],
            "android_ndk": ["25.2.9519653"],
            "java_jdk": ["11"],
            "gradle": ["8.7"],
            "android_cmdline_tools": True,
        }
        mock_uninstall_tool.return_value = True # Simulate successful uninstallation for each tool

        result = self.runner.invoke(cli, ['uninstall', 'all'])

        self.assertEqual(result.exit_code, 0)
        mock_logger.info.assert_any_call("Attempting to uninstall all DroidBuilder tools...")
        mock_uninstall_tool.assert_any_call("android-sdk")
        mock_uninstall_tool.assert_any_call("jdk-11")
        mock_uninstall_tool.assert_any_call("gradle-8.7")
        mock_uninstall_tool.assert_any_call("ndk-25.2.9519653")
        mock_logger.success("All DroidBuilder tools uninstalled successfully.")

    @patch('droidbuilder.commands.uninstall.logger')
    @patch('droidbuilder.installer.list_installed_tools')
    @patch('droidbuilder.installer.uninstall_tool')
    @patch('os.path.exists') # Re-add this mock
    def test_uninstall_all_partial_failure(self, mock_exists, mock_uninstall_tool, mock_list_installed_tools, mock_logger):
        # Mock installed tools to have only one tool that will fail
        mock_list_installed_tools.return_value = {
            "java_jdk": ["11"],
        }
        # Simulate failure for this tool
        mock_uninstall_tool.return_value = False 
        mock_exists.return_value = False # Ensure os.path.exists returns False for python-source check

        result = self.runner.invoke(cli, ['uninstall', 'all'])

        # The command itself should not crash, so exit_code should be 0
        self.assertEqual(result.exit_code, 0) 
        mock_logger.info.assert_any_call("Attempting to uninstall all DroidBuilder tools...")
        mock_uninstall_tool.assert_called_once_with("jdk-11")
        mock_logger.error("Failed to uninstall jdk-11.")
        mock_logger.error("Some DroidBuilder tools failed to uninstall. Please check the logs for details.")

    @patch('droidbuilder.commands.uninstall.logger')
    @patch('droidbuilder.installer.uninstall_tool')
    def test_uninstall_single_tool_success(self, mock_uninstall_tool, mock_logger):
        mock_uninstall_tool.return_value = True

        result = self.runner.invoke(cli, ['uninstall', 'jdk-11'])

        self.assertEqual(result.exit_code, 0)
        mock_uninstall_tool.assert_called_once_with('jdk-11')
        mock_logger.success("Successfully uninstalled 'jdk-11'.")

    @patch('droidbuilder.commands.uninstall.logger')
    @patch('droidbuilder.installer.uninstall_tool')
    def test_uninstall_single_tool_failure(self, mock_uninstall_tool, mock_logger):
        mock_uninstall_tool.return_value = False

        result = self.runner.invoke(cli, ['uninstall', 'gradle-8.7'])

        self.assertEqual(result.exit_code, 0) # Command itself should not crash
        mock_uninstall_tool.assert_called_once_with('gradle-8.7')
        mock_logger.error("Failed to uninstall 'gradle-8.7'. Please check the logs for details.")

if __name__ == '__main__':
    unittest.main()