
import os
import toml
import unittest
from click.testing import CliRunner
from droidbuilder import config
from droidbuilder.commands.config import config as config_command
import json

class TestConfig(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_project"
        os.makedirs(self.test_dir, exist_ok=True)
        self.config_path = os.path.join(self.test_dir, config.CONFIG_FILE)
        self.sample_config = {
            "project": {
                "name": "TestApp",
                "version": "0.1.0"
            },
            "author": "Test Author"
        }
        config.save_config(self.sample_config, path=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.test_dir)

    def test_load_config_not_found(self):
        """Test that loading a non-existent config returns an empty dict."""
        os.remove(self.config_path)
        cfg = config.load_config(path=self.test_dir)
        self.assertEqual(cfg, {})

    def test_save_and_load_config(self):
        """Test saving a config and then loading it back."""
        self.assertTrue(os.path.exists(self.config_path))
        loaded_config = config.load_config(path=self.test_dir)
        self.assertEqual(loaded_config, self.sample_config)
        with open(self.config_path, "r") as f:
            toml_content = toml.load(f)
        self.assertEqual(toml_content, self.sample_config)

    def test_get_value(self):
        """Test getting a value from the config via the CLI."""
        runner = CliRunner()
        result = runner.invoke(config_command, ['get', 'author'], obj={"path": self.test_dir})
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(), 'Test Author')

    def test_get_nested_value(self):
        """Test getting a nested value from the config via the CLI."""
        runner = CliRunner()
        result = runner.invoke(config_command, ['get', 'project.name'], obj={"path": self.test_dir})
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(), 'TestApp')

    def test_get_non_existent_value(self):
        """Test getting a non-existent value from the config via the CLI."""
        runner = CliRunner()
        result = runner.invoke(config_command, ['get', 'project.nonexistent'], obj={"path": self.test_dir})
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error: Key 'project.nonexistent' not found", result.output)

    def test_set_value(self):
        """Test setting a value in the config via the CLI."""
        runner = CliRunner()
        result = runner.invoke(config_command, ['set', 'author', 'New Author'], obj={"path": self.test_dir})
        self.assertEqual(result.exit_code, 0)
        loaded_config = config.load_config(path=self.test_dir)
        self.assertEqual(loaded_config['author'], 'New Author')

    def test_set_nested_value(self):
        """Test setting a nested value in the config via the CLI."""
        runner = CliRunner()
        result = runner.invoke(config_command, ['set', 'project.name', 'NewName'], obj={"path": self.test_dir})
        self.assertEqual(result.exit_code, 0)
        loaded_config = config.load_config(path=self.test_dir)
        self.assertEqual(loaded_config['project']['name'], 'NewName')

    def test_unset_value(self):
        """Test unsetting a value in the config via the CLI."""
        runner = CliRunner()
        result = runner.invoke(config_command, ['unset', 'author'], obj={"path": self.test_dir})
        self.assertEqual(result.exit_code, 0)
        loaded_config = config.load_config(path=self.test_dir)
        self.assertNotIn('author', loaded_config)

    def test_unset_nested_value(self):
        """Test unsetting a nested value in the config via the CLI."""
        runner = CliRunner()
        result = runner.invoke(config_command, ['unset', 'project.name'], obj={"path": self.test_dir})
        self.assertEqual(result.exit_code, 0)
        loaded_config = config.load_config(path=self.test_dir)
        self.assertNotIn('name', loaded_config['project'])

    def test_list_config(self):
        """Test listing all config values via the CLI."""
        runner = CliRunner()
        result = runner.invoke(config_command, ['list'], obj={"path": self.test_dir})
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.output.strip()), self.sample_config)

if __name__ == "__main__":
    unittest.main()
