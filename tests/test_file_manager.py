import os
import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.utils.file_manager import download_and_extract, extract

class TestFileManager(unittest.TestCase):

    @patch('droidbuilder.cli_logger.logger')
    @patch('zipfile.ZipFile')
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    @patch('os.remove')
    def test_extract_zip(self, mock_remove, mock_makedirs, mock_exists, mock_zipfile, mock_logger):
        mock_zip_ref = MagicMock()
        mock_zip_ref.infolist.return_value = [MagicMock(filename='file.txt', is_dir=lambda: False, external_attr=0)]
        mock_zipfile.return_value.__enter__.return_value = mock_zip_ref

        with unittest.mock.patch('builtins.open', unittest.mock.mock_open()):
            extract('/tmp/test.zip', '/tmp/extracted')
            mock_zipfile.assert_called_with('/tmp/test.zip', 'r')
            mock_remove.assert_called_with('/tmp/test.zip')

    @patch('droidbuilder.cli_logger.logger')
    @patch('tarfile.open')
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    @patch('os.remove')
    def test_extract_tar(self, mock_remove, mock_makedirs, mock_exists, mock_tarfile, mock_logger):
        mock_tar_ref = MagicMock()
        mock_tar_ref.getmembers.return_value = [MagicMock(name='file.txt', isdir=lambda: False, mode=0)]
        mock_tar_ref.extractfile.return_value.__enter__.return_value = MagicMock()
        mock_tarfile.return_value.__enter__.return_value = mock_tar_ref

        with unittest.mock.patch('builtins.open', unittest.mock.mock_open()):
            extract('/tmp/test.tar.gz', '/tmp/extracted')
            mock_tarfile.assert_called_with('/tmp/test.tar.gz', 'r:*')
            mock_remove.assert_called_with('/tmp/test.tar.gz')

    @patch('droidbuilder.cli_logger.logger')
    @patch('requests.get')
    @patch('droidbuilder.utils.file_manager.extract') # Patch the extract function
    @patch('os.replace')
    def test_download_and_extract_zip(self, mock_replace, mock_extract, mock_requests_get, mock_logger):
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b'test']
        mock_response.headers.get.return_value = '4'
        mock_requests_get.return_value.__enter__.return_value = mock_response

        with unittest.mock.patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            download_and_extract('http://test.com/test.zip', '/tmp')
            mock_open.assert_called_with('/tmp/test.zip.tmp', 'wb')
            mock_replace.assert_called_with('/tmp/test.zip.tmp', '/tmp/test.zip')
            mock_extract.assert_called_with('/tmp/test.zip', '/tmp') # Assert extract is called

    @patch('droidbuilder.cli_logger.logger')
    @patch('requests.get')
    @patch('droidbuilder.utils.file_manager.extract') # Patch the extract function
    @patch('os.replace')
    def test_download_and_extract_tar(self, mock_replace, mock_extract, mock_requests_get, mock_logger):
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b'test']
        mock_response.headers.get.return_value = '4'
        mock_requests_get.return_value.__enter__.return_value = mock_response

        with unittest.mock.patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            download_and_extract('http://test.com/test.tar.gz', '/tmp')
            mock_open.assert_called_with('/tmp/test.tar.gz.tmp', 'wb')
            mock_replace.assert_called_with('/tmp/test.tar.gz.tmp', '/tmp/test.tar.gz')
            mock_extract.assert_called_with('/tmp/test.tar.gz', '/tmp') # Assert extract is called
