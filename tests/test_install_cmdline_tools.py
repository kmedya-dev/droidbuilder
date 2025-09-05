import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.installer import install_cmdline_tools

class TestInstallCmdlineTools(unittest.TestCase):

    @patch('droidbuilder.installer.logger')
    @patch('droidbuilder.utils.download_and_extract')
    @patch('os.path.exists', return_value=True)
    @patch('os.chmod')
    def test_install_cmdline_tools(self, mock_chmod, mock_exists, mock_download_and_extract, mock_logger):
        install_cmdline_tools('9123335')
        mock_download_and_extract.assert_called_once()

if __name__ == '__main__':
    unittest.main()