import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.utils.python_package import resolve_python_package

class TestPythonPackage(unittest.TestCase):

    @patch('droidbuilder.cli_logger.logger')
    @patch('requests.get')
    def test_resolve_python_package_success(self, mock_requests_get, mock_logger):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "info": {"version": "1.0.0"},
            "releases": {
                "1.0.0": [
                    {"packagetype": "sdist", "url": "http://example.com/test_package-1.0.0.tar.gz"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        url, version = resolve_python_package("test_package")
        self.assertEqual(url, "http://example.com/test_package-1.0.0.tar.gz")
        self.assertEqual(version, "1.0.0")
        mock_requests_get.assert_called_once_with("https://pypi.org/pypi/test_package/json")

    @patch('droidbuilder.cli_logger.logger')
    @patch('requests.get')
    def test_resolve_python_package_not_found(self, mock_requests_get, mock_logger):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        url, version = resolve_python_package("non_existent_package")
        self.assertIsNone(url)
        self.assertIsNone(version)

    @patch('droidbuilder.cli_logger.logger')
    @patch('requests.get')
    def test_resolve_python_package_version_not_found(self, mock_requests_get, mock_logger):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "info": {"version": "1.0.0"},
            "releases": {
                "1.0.0": [
                    {"packagetype": "sdist", "url": "http://example.com/test_package-1.0.0.tar.gz"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        url, version = resolve_python_package("test_package", "2.0.0")
        self.assertEqual(url, "http://example.com/test_package-1.0.0.tar.gz") # Falls back to latest
        self.assertEqual(version, "1.0.0")

    @patch('droidbuilder.cli_logger.logger')
    @patch('requests.get')
    def test_resolve_python_package_no_sdist(self, mock_requests_get, mock_logger):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "info": {"version": "1.0.0"},
            "releases": {
                "1.0.0": [
                    {"packagetype": "bdist_wheel", "url": "http://example.com/test_package-1.0.0-py3-none-any.whl"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        url, version = resolve_python_package("test_package")
        self.assertIsNone(url)
        self.assertIsNone(version)
