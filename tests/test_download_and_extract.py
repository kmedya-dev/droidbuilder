import os
import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.utils import download_and_extract

class TestDownloadAndExtract(unittest.TestCase):

    @patch('droidbuilder.utils.logger')
    @patch('requests.get')
    @patch('zipfile.ZipFile')
    @patch('os.replace')
    def test_download_and_extract_zip(self, mock_replace, mock_zipfile, mock_requests_get, mock_logger):
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b'test']
        mock_response.headers.get.return_value = '4'
        mock_requests_get.return_value.__enter__.return_value = mock_response

        with unittest.mock.patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            download_and_extract('http://test.com/test.zip', '/tmp')
            mock_open.assert_called_with('/tmp/test.zip.tmp', 'wb')
            mock_replace.assert_called_with('/tmp/test.zip.tmp', '/tmp/test.zip')
            mock_zipfile.assert_called_with('/tmp/test.zip', 'r')

    @patch('droidbuilder.utils.logger')
    @patch('requests.get')
    @patch('tarfile.open')
    @patch('os.replace')
    def test_download_and_extract_tar(self, mock_replace, mock_tarfile, mock_requests_get, mock_logger):
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b'test']
        mock_response.headers.get.return_value = '4'
        mock_requests_get.return_value.__enter__.return_value = mock_response

        with unittest.mock.patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            download_and_extract('http://test.com/test.tar.gz', '/tmp')
            mock_open.assert_called_with('/tmp/test.tar.gz.tmp', 'wb')
            mock_replace.assert_called_with('/tmp/test.tar.gz.tmp', '/tmp/test.tar.gz')
            mock_tarfile.assert_called_with('/tmp/test.tar.gz', 'r:*')

if __name__ == '__main__':
    unittest.main()