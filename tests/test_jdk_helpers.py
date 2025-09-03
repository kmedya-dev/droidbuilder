import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.installer import _get_available_jdk_versions, _get_latest_temurin_jdk_url

class TestJdkHelpers(unittest.TestCase):

    @patch('requests.get')
    def test_get_available_jdk_versions(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'available_lts_releases': [11, 17]}
        mock_requests_get.return_value = mock_response

        versions = _get_available_jdk_versions()

        self.assertEqual(versions, [11, 17])

    @patch('requests.get')
    def test_get_latest_temurin_jdk_url(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'assets': [
                {
                    'name': 'OpenJDK11U-jdk_x64_linux_hotspot_11.0.15_10.tar.gz',
                    'browser_download_url': 'http://test.com/jdk.tar.gz'
                }
            ]
        }
        mock_requests_get.return_value = mock_response

        url = _get_latest_temurin_jdk_url(11)

        self.assertEqual(url, 'http://test.com/jdk.tar.gz')

if __name__ == '__main__':
    unittest.main()