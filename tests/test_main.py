import os
import toml
import unittest
from unittest.mock import patch
from click.testing import CliRunner
from droidbuilder import config
from droidbuilder.main import cli

class TestMain(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.test_dir = "test_project"
        os.makedirs(self.test_dir, exist_ok=True)
        self.config_path = os.path.join(self.test_dir, config.CONFIG_FILE)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.test_dir)

    def test_config_view_not_found(self):
        """Test that viewing a non-existent config returns an error."""
        with patch.object(config, 'CONFIG_FILE', self.config_path):
            result = self.runner.invoke(cli, ["config", "view"])
            self.assertIn("Error: No droidbuilder.toml found.", result.output)

    def test_config_view(self):
        """Test that viewing a config prints its content."""
        sample_config = {
            "project": {
                "name": "TestApp",
                "version": "0.1.0"
            }
        }
        config.save_config(sample_config, path=self.test_dir)

        result = self.runner.invoke(cli, ["--path", self.test_dir, "config", "view"])
        print(result.output)
        with open(self.config_path, "r") as f:
            self.assertEqual(result.output.strip(), f.read().strip())

    @patch("click.edit")
    def test_config_edit(self, mock_edit):
        """Test that editing a config calls click.edit."""
        sample_config = {
            "project": {
                "name": "TestApp",
                "version": "0.1.0"
            }
        }
        config.save_config(sample_config, path=self.test_dir)

        self.runner.invoke(cli, ["--path", self.test_dir, "config", "edit"])
        mock_edit.assert_called_once_with(filename=self.config_path)

if __name__ == "__main__":
    unittest.main()
