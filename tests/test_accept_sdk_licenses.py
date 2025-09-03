import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.installer import _accept_sdk_licenses

class TestAcceptSdkLicenses(unittest.TestCase):

    @patch('droidbuilder.installer.logger')
    @patch('subprocess.Popen')
    @patch('os.path.exists', return_value=True)
    @patch('os.chmod')
    def test_accept_sdk_licenses(self, mock_chmod, mock_exists, mock_popen, mock_logger):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'')
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        _accept_sdk_licenses('/tmp')

        mock_popen.assert_called_once()

if __name__ == '__main__':
    unittest.main()