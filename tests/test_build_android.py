import os
import unittest
from unittest.mock import patch, MagicMock, call
from droidbuilder.builder import build_android

class TestBuildAndroid(unittest.TestCase):

    def setUp(self):
        self.conf = {
            "project": {
                "name": "MyTestApp",
                "version": "1.0.0",
                "package_domain": "com.example",
                "build_type": "debug"
            },
            "android": {
                "sdk_version": "36",
                "min_sdk_version": "24" 
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
    def test_build_android_success(self, mock_shutil_copy, mock_subprocess_run, mock_chmod, mock_exists, mock_makedirs, mock_copytree, mock_logger):
        # Mock subprocess.run for gradlew
        mock_subprocess_run.return_value = MagicMock(stdout="Build successful", stderr="", returncode=0)

        build_android(self.conf, False)

        # No assertions for now, just checking that the function runs without crashing
        pass

if __name__ == '__main__':
    unittest.main()
