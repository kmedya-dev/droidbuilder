import unittest
from unittest.mock import patch, MagicMock
from droidbuilder import downloader

class TestDownloader(unittest.TestCase):

    @patch('droidbuilder.cli_logger.logger')
    @patch('droidbuilder.utils.file_manager.download_and_extract')
    def test_download_system_package(self, mock_download_and_extract, mock_logger):
        mock_download_and_extract.return_value = "/path/to/extracted_dir"

        # Now download_system_package expects a URL directly
        result = downloader.download_system_package("http://example.com/test.tar.gz", "/tmp")
        self.assertEqual(result, "/path/to/extracted_dir")
        mock_download_and_extract.assert_called_once_with("http://example.com/test.tar.gz", "/tmp/sources/test", "test.tar.gz")

    @patch('droidbuilder.cli_logger.logger')
    @patch('requests.get')
    @patch('droidbuilder.utils.python_package.resolve_python_package')
    def test_download_pypi_package(self, mock_resolve_python_package, mock_requests_get, mock_logger):
        mock_resolve_python_package.return_value = ("http://example.com/test_package-1.0.0.tar.gz", "1.0.0")
        mock_requests_get.return_value.__enter__.return_value = MagicMock(status_code=200, iter_content=lambda chunk_size: [b'test'], headers={'content-length': '4'})

        with patch('builtins.open', MagicMock()):
            result = downloader.download_pypi_package("test_package", "/tmp")
            self.assertEqual(result, "/tmp/test_package-1.0.0.tar.gz")
            mock_resolve_python_package.assert_called_once_with("test_package", None)
            mock_requests_get.assert_called_once_with("http://example.com/test_package-1.0.0.tar.gz", stream=True)

    @patch('droidbuilder.cli_logger.logger')
    @patch('requests.get')
    @patch('droidbuilder.utils.file_manager.download_and_extract')
    def test_download_from_url(self, mock_download_and_extract, mock_requests_get, mock_logger):
        mock_download_and_extract.return_value = "/path/to/extracted_dir"

        result = downloader.download_from_url("http://example.com/test.zip", "/tmp")
        self.assertEqual(result, "/path/to/extracted_dir")
        mock_download_and_extract.assert_called_once_with("http://example.com/test.zip", "/tmp/sources/test", "test.zip")