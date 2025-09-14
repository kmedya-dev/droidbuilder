import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.installer import setup_tools

class TestSetupTools(unittest.TestCase):

    @patch('droidbuilder.installer.install_cmdline_tools')
    @patch('droidbuilder.installer._accept_sdk_licenses')
    @patch('droidbuilder.installer.install_sdk_packages')
    @patch('droidbuilder.installer.install_ndk')
    @patch('droidbuilder.installer.install_jdk')
    def test_setup_tools(self, mock_install_jdk, mock_install_ndk, mock_install_sdk_packages, mock_accept_licenses, mock_install_cmdline_tools):
        conf = {
            'android': {
                'sdk_version': '34',
                'ndk_version': '25.2.9519653',
                'cmdline_tools_version': '9123335',
                'accept_sdk_license': 'non-interactive'
            },
            'java': {
                'jdk_version': '11'
            }
        }
        setup_tools(conf)
        mock_install_cmdline_tools.assert_called_with('9123335')
        mock_accept_licenses.assert_called_once()
        mock_install_sdk_packages.assert_called_with('34', unittest.mock.ANY)
        mock_install_ndk.assert_called_with('25.2.9519653', unittest.mock.ANY)
        mock_install_jdk.assert_called_with('11')

if __name__ == '__main__':
    unittest.main()