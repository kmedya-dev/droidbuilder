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
    @patch('shutil.rmtree')
    @patch('os.chmod')
    @patch('subprocess.run')
    @patch('shutil.copy')
    def test_build_android_success(self, mock_shutil_copy, mock_subprocess_run, mock_chmod, mock_rmtree, mock_exists, mock_makedirs, mock_copytree, mock_logger):
        # Mock file operations
        def mock_open_func(file_path, mode='r'):
            mock_file = MagicMock()
            if mode == 'r':
                # Extract relative path from absolute path for lookup in mock_open_content
                relative_path = os.path.relpath(file_path, os.path.join(os.path.sep, 'workspaces', 'droidbuilder', 'build', 'MyTestApp'))
                if relative_path in self.mock_open_content:
                    mock_file.read.return_value = self.mock_open_content[relative_path]
                else:
                    # Handle cases where file is opened for reading but not in mock_open_content
                    mock_file.read.return_value = ""
            return mock_file

        with patch('builtins.open', side_effect=mock_open_func) as mock_open:
            # Mock subprocess.run for gradlew
            mock_subprocess_run.return_value = MagicMock(stdout="Build successful", stderr="", returncode=0)

            build_android(self.conf, False)

            # Assertions
            mock_rmtree.assert_called_once()
            mock_makedirs.assert_has_calls([
                call(os.path.join(os.getcwd(), "build", "MyTestApp")),
                call(os.path.join(os.getcwd(), "dist"), exist_ok=True)
            ])
            mock_copytree.assert_called_once()

            # Check calls to open for writing
            expected_write_paths = [
                os.path.join("app", "build.gradle"),
                os.path.join("app", "src", "main", "AndroidManifest.xml")
            ]
            actual_write_calls = []
            for call_args in mock_open.call_args_list:
                path, mode = call_args.args
                if mode == 'w':
                    actual_write_calls.append(path)

            self.assertEqual(len(actual_write_calls), len(expected_write_paths))
            for expected_path in expected_write_paths:
                self.assertTrue(any(actual_path.endswith(expected_path) for actual_path in actual_write_calls))

            mock_chmod.assert_called_once()
            mock_subprocess_run.assert_called_once_with([
                os.path.join(os.getcwd(), "build", "MyTestApp", "gradlew"),
                ':app:assembleDebug'
            ], cwd=os.path.join(os.getcwd(), "build", "MyTestApp"), check=True, capture_output=True, text=True)
            mock_shutil_copy.assert_called_once()

if __name__ == '__main__':
    unittest.main()
