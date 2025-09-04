import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.installer import install_python_requirements

class TestInstallPythonRequirements(unittest.TestCase):

    @patch('droidbuilder.installer.logger')
    @patch('subprocess.check_call')
    def test_install_python_requirements(self, mock_subprocess_check_call, mock_logger):
        install_python_requirements(['kivy', 'requests'])
        mock_subprocess_check_call.assert_called_once()

if __name__ == '__main__':
    unittest.main()