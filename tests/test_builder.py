import unittest
from unittest.mock import patch, MagicMock, call
from droidbuilder.builder import build_android
from unittest import mock

class TestBuilder(unittest.TestCase):

    def setUp(self):
        self.conf = {
            "project": {
                "name": "MyTestApp",
                "version": "1.0.0",
                "package_domain": "com.example",
                "build_type": "debug",
                "target_platforms": ["android"],
                "main_file": "main.py",
                "requirements": {
                    "python_packages": ["some_package", "another_package==1.2.3"],
                    "system_packages": ["openssl==1.1.1k", "sdl2"]
                },
                "dependency_mapping": {
                    "openssl": "http://example.com/openssl-1.1.1k.tar.gz", # Added openssl mapping
                    "sdl2": "https://libsdl.org/release/SDL2-2.30.2.tar.gz"
                },
                "python_dependency_mapping": {
                    "some_package": "https://example.com/custom_some_package-2.0.0.zip"
                }
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
        mock_subprocess_run.return_value = MagicMock(stdout="Build successful", stderr="", returncode=0)
        build_android(self.conf, False)
        # Basic check that it runs without immediate crash
        self.assertTrue(True)

    @patch('droidbuilder.builder.logger')
    @patch('droidbuilder.downloader.download_system_package') # This now expects a URL
    @patch('droidbuilder.downloader.download_from_url')
    @patch('droidbuilder.utils.system_package.resolve_dependencies_recursively')
    @patch('droidbuilder.builder.downloader.download_python_source', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    @patch('droidbuilder.builder.subprocess.run')
    @patch('requests.get')
    @patch('droidbuilder.utils.system_package.subprocess.run')
    def test_build_android_system_packages_flow(self, mock_logger, mock_download_system_package, mock_download_from_url, mock_resolve_dependencies_recursively, mock_download_python_source, mock_exists, mock_makedirs, mock_builder_subprocess_run, mock_requests_get, mock_system_package_subprocess_run):
        mock_system_package_subprocess_run.return_value = MagicMock(returncode=0, stdout="Homepage: http://example.com/openssl", stderr="")
        mock_builder_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mock_resolve_dependencies_recursively.return_value = {"openssl": "http://example.com/openssl-1.1.1k.tar.gz", "sdl2": "https://libsdl.org/release/SDL2-2.30.2.tar.gz"}
        mock_download_system_package.return_value = "/path/to/extracted_dir_openssl"
        mock_download_from_url.return_value = "/path/to/extracted_dir_sdl2"
        
        with patch('droidbuilder.builder._compile_system_package', return_value=True):
            build_android(self.conf, False)

        mock_resolve_dependencies_recursively.assert_called_once_with(
            self.conf['project']['requirements']['system_packages'],
            self.conf['project']['dependency_mapping']
        )
        # download_system_package is now called with a URL directly
        mock_download_system_package.assert_called_once_with(
            self.conf['project']['dependency_mapping']['openssl'], mock.ANY
        )
        mock_download_from_url.assert_called_once_with(
            self.conf['project']['dependency_mapping']['sdl2'], mock.ANY
        )

    @patch('droidbuilder.builder.logger')
    @patch('droidbuilder.downloader.download_pypi_package')
    @patch('droidbuilder.downloader.download_from_url')
    @patch('droidbuilder.builder.downloader.download_python_source', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    @patch('droidbuilder.builder.subprocess.run')
    @patch('requests.get')
    @patch('droidbuilder.utils.dependencies.get_explicit_dependencies')
    @patch('droidbuilder.utils.system_package.subprocess.run')
    def test_build_android_python_packages_flow(self, mock_logger, mock_download_pypi_package, mock_download_from_url, mock_download_python_source, mock_exists, mock_makedirs, mock_builder_subprocess_run, mock_requests_get, mock_get_explicit_dependencies, mock_system_package_subprocess_run):
        mock_system_package_subprocess_run.return_value = MagicMock(returncode=0, stdout="Homepage: http://example.com/openssl", stderr="")
        mock_builder_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mock_requests_get.side_effect = [
            MagicMock(json=MagicMock(return_value={"info": {"version": "1.0.0"}, "releases": {"1.0.0": [{"packagetype": "sdist", "url": "http://example.com/some_package-1.0.0.tar.gz"}]}}), raise_for_status=lambda: None),
            MagicMock(iter_content=lambda chunk_size: [b'test'], headers={'content-length': '4'}, raise_for_status=lambda: None)
        ]
        mock_download_pypi_package.return_value = "/path/to/extracted_dir_another_package"
        mock_download_from_url.return_value = "/path/to/extracted_dir_some_package"
        mock_get_explicit_dependencies.return_value = (['some_package'], [], {'some_package': 'https://example.com/custom_some_package-2.0.0.zip'})
        
        with patch('droidbuilder.builder._compile_python_package', return_value=True):
            build_android(self.conf, False)

        mock_download_from_url.assert_called_once_with(
            self.conf['project']['python_dependency_mapping']['some_package'], mock.ANY
        )
        mock_download_pypi_package.assert_called_once_with(
            'another_package==1.2.3', mock.ANY
        )
