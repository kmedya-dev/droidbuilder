import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.installer import install_sdk_packages

class TestInstallSdkPackages(unittest.TestCase):

    @patch('droidbuilder.installer.logger')
    @patch('subprocess.run')
    @patch('os.path.exists', return_value=True)
    @patch('os.chmod')
    def test_install_sdk_packages(self, mock_chmod, mock_exists, mock_subprocess_run, mock_logger):
        install_sdk_packages('34', '/tmp/sdk')
        self.assertEqual(mock_subprocess_run.call_count, 2)

if __name__ == '__main__':
    unittest.main()