import unittest
from click.testing import CliRunner
from droidbuilder.main import cli
import os
import shutil
from unittest.mock import patch, MagicMock

class TestCheckDepsCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.test_dir = "test_project"
        os.makedirs(self.test_dir, exist_ok=True)
        with open(os.path.join(self.test_dir, "droidbuilder.toml"), "w") as f:
            f.write('''
[project]
name = "Test Project"
requirements = ["requests"]
''')
        with open(os.path.join(self.test_dir, "main.py"), "w") as f:
            f.write("import requests\nimport numpy\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('droidbuilder.commands.check_deps.logger')
    def test_check_deps_missing(self, mock_logger):
        result = self.runner.invoke(cli, ["--path", self.test_dir, "check-deps"])
        self.assertEqual(result.exit_code, 0)
        mock_logger.warning.assert_any_call("Found imported packages not listed in droidbuilder.toml:")
        mock_logger.warning.assert_any_call("  - numpy")

    @patch('droidbuilder.commands.check_deps.logger')
    def test_check_deps_ok(self, mock_logger):
        with open(os.path.join(self.test_dir, "droidbuilder.toml"), "w") as f:
            f.write('''
[project]
name = "Test Project"
requirements = ["requests", "numpy"]
''')
        result = self.runner.invoke(cli, ["--path", self.test_dir, "check-deps"])
        self.assertEqual(result.exit_code, 0)
        mock_logger.success.assert_called_with("All imported packages are listed in droidbuilder.toml.")

if __name__ == '__main__':
    unittest.main()