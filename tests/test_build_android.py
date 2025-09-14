import os
import unittest
from unittest.mock import patch, MagicMock, call
from droidbuilder.builder import build_android
from unittest import mock

class TestBuildAndroid(unittest.TestCase):

    def setUp(self):
        self.conf = {
            "project": {
                "name": "MyTestApp",
                "version": "1.0.0",
                "package_domain": "com.example",
                "build_type": "debug",
                "target_platforms": ["android"],
                "main_file": "main.py",
            },
            "android": {
                "sdk_version": "36",
                "min_sdk_version": "24",
                "ndk_version": "25.2.9519653",
                "ndk_api": "24",
                "archs": ["arm64-v8a"],
            },
            "python": {
                "python_version": "3.9.13"
            }
        }
        self.mock_open_content = {
            "app/build.gradle": """applicationId "org.test.mydroidapp"
minSdkVersion 24
targetSdkVersion 36
versionName "1.0" """,
            "app/src/main/AndroidManifest.xml": 'package="org.test.mydroidapp" '
        }

    @patch('droidbuilder.builder.logger')
    @patch('shutil.copytree')
    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('os.chmod')
    @patch('subprocess.run')
    @patch('shutil.copy')
    @patch('droidbuilder.builder.downloader.download_python_source')
    @patch('droidbuilder.builder._download_system_packages')
    @patch('droidbuilder.builder._build_python_for_android')
    @patch('droidbuilder.builder._download_python_packages')
    @patch('droidbuilder.builder._create_android_project')
    @patch('droidbuilder.builder._configure_android_project')
    @patch('droidbuilder.builder._copy_assets_to_android_project')
    @patch('droidbuilder.builder._copy_user_python_code')
    def test_build_android_success(self, mock_copy_user_code, mock_copy_assets, mock_configure_project, mock_create_project, mock_download_python_packages, mock_build_python, mock_download_system_packages, mock_download_python_source, mock_shutil_copy, mock_subprocess_run, mock_chmod, mock_exists, mock_makedirs, mock_copytree, mock_logger):
        # Mock subprocess.run for gradlew
        mock_subprocess_run.return_value = MagicMock(stdout="Build successful", stderr="", returncode=0)

        build_android(self.conf, False)

        # No assertions for now, just checking that the function runs without crashing
        pass

    @patch('droidbuilder.builder.logger')
    @patch('droidbuilder.builder.downloader.download_system_package')
    @patch('droidbuilder.builder.downloader.download_python_source', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    @patch('subprocess.run')
    def test_build_android_with_system_packages(self, mock_subprocess_run, mock_makedirs, mock_exists, mock_download_python_source, mock_download_system_package, mock_logger):
        conf = self.conf.copy()
        conf['project']['requirements'] = {
            "system_packages": ["openssl==1.1.1k", "sdl2"]
        }

        # Mock the return value of download_system_package to avoid actual downloads
        mock_download_system_package.return_value = "/path/to/extracted_dir"
        
        # We need to patch _compile_system_package as well, since it's called from _download_system_packages
        with patch('droidbuilder.builder._compile_system_package', return_value=True):
            build_android(conf, False)

        # We expect download_system_package to be called for each system package
        expected_calls = [
            call('openssl', '1.1.1k', mock.ANY),
            call('sdl2', None, mock.ANY)
        ]
        mock_download_system_package.assert_has_calls(expected_calls, any_order=True)


if __name__ == '__main__':
    unittest.main()
