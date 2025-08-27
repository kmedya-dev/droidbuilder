
import os
import toml
import unittest
from droidbuilder import config

class TestConfig(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_project"
        os.makedirs(self.test_dir, exist_ok=True)
        self.config_path = os.path.join(self.test_dir, config.CONFIG_FILE)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.test_dir)

    def test_load_config_not_found(self):
        """Test that loading a non-existent config returns an empty dict."""
        cfg = config.load_config(path=self.test_dir)
        self.assertEqual(cfg, {})

    def test_save_and_load_config(self):
        """Test saving a config and then loading it back."""
        # 1. Create a sample config and save it
        sample_config = {
            "project": {
                "name": "TestApp",
                "version": "0.1.0"
            }
        }
        config.save_config(sample_config, path=self.test_dir)

        # 2. Verify the file was created
        self.assertTrue(os.path.exists(self.config_path))

        # 3. Load the config back and verify its contents
        loaded_config = config.load_config(path=self.test_dir)
        self.assertEqual(loaded_config, sample_config)

        # 4. Verify the TOML content is as expected
        with open(self.config_path, "r") as f:
            toml_content = toml.load(f)
        self.assertEqual(toml_content, sample_config)

if __name__ == "__main__":
    unittest.main()
