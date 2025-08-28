import os
import unittest
from unittest.mock import patch, MagicMock
from droidbuilder import installer
import requests

class TestInstaller(unittest.TestCase):

    @patch("os.path.exists")
    def test_get_sdk_manager_exists(self, mock_exists):
        mock_exists.return_value = True
        sdk_install_dir = "/fake/sdk"
        expected_path = os.path.join(sdk_install_dir, "cmdline-tools", "latest", "bin", "sdkmanager")
        with patch("os.chmod") as mock_chmod:
            path = installer._get_sdk_manager(sdk_install_dir)
            self.assertEqual(path, expected_path)
            mock_chmod.assert_called_once_with(expected_path, 0o755)

    @patch("os.path.exists")
    def test_get_sdk_manager_not_exists(self, mock_exists):
        mock_exists.return_value = False
        sdk_install_dir = "/fake/sdk"
        path = installer._get_sdk_manager(sdk_install_dir)
        self.assertIsNone(path)

    @patch("requests.get")
    def test_get_available_jdk_versions_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"available_lts_releases": ["11", "17", "21"]}
        mock_get.return_value = mock_response

        versions = installer._get_available_jdk_versions()
        self.assertEqual(versions, ["11", "17", "21"])

    @patch("requests.get")
    def test_get_available_jdk_versions_api_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("API is down")

        versions = installer._get_available_jdk_versions()
        self.assertEqual(versions, [])

if __name__ == "__main__":
    unittest.main()
