import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.installer import install_ndk

class TestInstallNdk(unittest.TestCase):

    @patch('droidbuilder.installer.logger')
    @patch('subprocess.run')
    @patch('os.path.exists', return_value=True)
    @patch('os.chmod')
    def test_install_ndk(self, mock_chmod, mock_exists, mock_subprocess_run, mock_logger):
        install_ndk('25.2.9519653', '/tmp')
        mock_subprocess_run.assert_called_once()

if __name__ == '__main__':
    unittest.main()