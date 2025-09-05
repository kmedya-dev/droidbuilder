import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.installer import install_jdk

class TestInstallJdk(unittest.TestCase):

    @patch('droidbuilder.installer.logger')
    @patch('droidbuilder.installer._get_latest_temurin_jdk_url', return_value='http://test.com/jdk.tar.gz')
    @patch('droidbuilder.utils.download_and_extract')
    @patch('os.listdir', return_value=['jdk-11.0.15_10'])
    @patch('os.path.isdir', return_value=True)
    def test_install_jdk(self, mock_isdir, mock_listdir, mock_download_and_extract, mock_get_url, mock_logger):
        install_jdk('11')
        mock_get_url.assert_called_with('11')
        mock_download_and_extract.assert_called_with('http://test.com/jdk.tar.gz', unittest.mock.ANY)

if __name__ == '__main__':
    unittest.main()